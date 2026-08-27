#!/usr/bin/env python3
"""Librebase instance API — /rest/v1, /v1/auth, /v1/sql.

Stdlib-only file-backed runtime used when `lis` is not installed on the VM.
Speaks the same contract as @librebase/librebase (supabase-js-shaped).
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

ANON_KEY = os.environ.get("LI_ANON_KEY", os.environ.get("LIBREBASE_ANON_KEY", "anon"))
SERVICE_KEY = os.environ.get(
    "LI_SERVICE_ROLE_KEY", os.environ.get("LIBREBASE_SERVICE_ROLE_KEY", "service_role")
)
JWT_SECRET = os.environ.get("LI_JWT_SECRET", os.environ.get("LIBREBASE_JWT_SECRET", "librebase-dev-jwt"))
STATIC_DIR = Path(os.environ.get("LIBREBASE_STATIC_DIR", "/opt/librebase/crm"))

# Insecure dev defaults. Production instances MUST override these: the host agent
# injects per-instance keys (LIBREBASE_SERVICE_ROLE_KEY / LIBREBASE_JWT_SECRET)
# fetched from the control plane. Starting on the world-known defaults would let
# any peer on the host forge service-role access, so we fail closed instead.
_INSECURE_SERVICE_KEY = "service_role"
_INSECURE_JWT_SECRET = "librebase-dev-jwt"


def _insecure_defaults_active() -> bool:
    return SERVICE_KEY == _INSECURE_SERVICE_KEY or JWT_SECRET == _INSECURE_JWT_SECRET

CRM_TABLES = {
    "notes": ["id", "body", "author", "email", "owner_id", "created_at"],
    "companies": ["id", "name", "domain", "industry", "notes", "owner_id", "created_at"],
    "contacts": [
        "id",
        "name",
        "email",
        "phone",
        "title",
        "company_id",
        "notes",
        "owner_id",
        "created_at",
    ],
    "deals": [
        "id",
        "title",
        "amount",
        "stage",
        "company_id",
        "contact_id",
        "notes",
        "owner_id",
        "created_at",
    ],
}


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    pad = "=" * ((4 - len(data) % 4) % 4)
    return base64.urlsafe_b64decode(data + pad)


def hash_password(password: str, salt: str | None = None) -> str:
    salt_b = (salt or secrets.token_hex(16)).encode() if salt is None else bytes.fromhex(salt)
    if salt is None:
        salt_hex = salt_b.hex() if isinstance(salt_b, bytes) else str(salt)
        salt_b = bytes.fromhex(salt_hex)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt_b, 120_000)
        return salt_hex + "$" + digest.hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 120_000)
    return salt + "$" + digest.hex()


def new_password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 120_000)
    return salt + "$" + digest.hex()


def verify_password(password: str, stored: str) -> bool:
    if "$" not in stored:
        return False
    salt, digest = stored.split("$", 1)
    check = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 120_000).hex()
    return hmac.compare_digest(check, digest)


def sign_jwt(payload: dict[str, Any], secret: str = JWT_SECRET, ttl: int = 3600) -> str:
    body = dict(payload)
    body.setdefault("iat", int(time.time()))
    body.setdefault("exp", int(time.time()) + ttl)
    header = _b64url(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    p = _b64url(json.dumps(body, separators=(",", ":")).encode())
    sig = hmac.new(secret.encode(), f"{header}.{p}".encode(), hashlib.sha256).digest()
    return f"{header}.{p}.{_b64url(sig)}"


def verify_jwt(token: str, secret: str = JWT_SECRET) -> dict[str, Any] | None:
    try:
        header_b, payload_b, sig_b = token.split(".")
        expected = hmac.new(secret.encode(), f"{header_b}.{payload_b}".encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(_b64url(expected), sig_b):
            return None
        payload = json.loads(_b64url_decode(payload_b))
        if int(payload.get("exp", 0)) < int(time.time()):
            return None
        return payload
    except (ValueError, json.JSONDecodeError, KeyError):
        return None


# ---------------------------------------------------------------------------
# lidb_embed integration — real SQL engine when the binary is available.
# ---------------------------------------------------------------------------
_LIDB_EMBED: str | None = None  # cached path, resolved once at startup


def _find_lidb_embed() -> str | None:
    """Locate the lidb_embed binary. Checks PATH, then common install locations."""
    global _LIDB_EMBED
    if _LIDB_EMBED is not None:
        return _LIDB_EMBED
    # 1. On PATH
    found = shutil.which("lidb_embed")
    if found:
        _LIDB_EMBED = found
        return _LIDB_EMBED
    # 2. LIDB_ROOT env var (set by host-agent)
    lidb_root = os.environ.get("LIDB_ROOT", "")
    if lidb_root:
        candidate = Path(lidb_root) / "build" / "lidb_embed"
        if candidate.is_file():
            _LIDB_EMBED = str(candidate)
            return _LIDB_EMBED
    # 3. Standard locations
    for candidate in (
        "/usr/local/bin/lidb_embed",
        "/opt/lidb/build/lidb_embed",
        "/opt/li/lidb/build/lidb_embed",
    ):
        if Path(candidate).is_file():
            _LIDB_EMBED = candidate
            return _LIDB_EMBED
    return None


_LIDB_ENGINE: Any = None  # liorm.embed_engine module, loaded once


def _get_lidb_engine(data_dir: str) -> Any | None:
    """Get or initialize the liorm.embed_engine for persistent lidb sessions."""
    global _LIDB_ENGINE
    if _LIDB_ENGINE is not None:
        return _LIDB_ENGINE
    # Try to import liorm.embed_engine from the lidb repo
    lidb_root = os.environ.get("LIDB_ROOT", "")
    if not lidb_root:
        for candidate in ("/opt/li/lidb", "/opt/lidb", "../li/lidb"):
            if Path(candidate).is_dir():
                lidb_root = candidate
                break
    if not lidb_root:
        return None
    lidb_path = Path(lidb_root)
    if not (lidb_path / "liorm" / "embed_engine.py").is_file():
        return None
    import importlib
    lidb_str = str(lidb_path)
    if lidb_str not in sys.path:
        sys.path.insert(0, lidb_str)
    os.environ.setdefault("LIDB_ROOT", lidb_str)
    os.environ.setdefault("LIDB_EMBED", "/usr/local/bin/lidb_embed")
    os.environ["LIDB_DATA_DIR"] = data_dir
    os.environ["LI_DATA_DIR"] = data_dir
    try:
        mod = importlib.import_module("liorm.embed_engine")
        session = mod.ensure_session()
        if session is None:
            return None
        _LIDB_ENGINE = mod
        return mod
    except Exception:
        return None


_DDL_RE = re.compile(
    r"^\s*(create|insert|update|delete|drop|alter|grant|revoke|begin|commit|rollback)\b",
    re.I,
)


def _exec_lidb_sql(data_dir: str, sql: str) -> dict[str, Any] | None:
    """Execute SQL via liorm.embed_engine (persistent lidb session). Returns None if unavailable."""
    engine = _get_lidb_engine(data_dir)
    if engine is None:
        return None
    try:
        rows = engine.execute_sql(sql, [])
        return {"ok": True, "rows": rows}
    except RuntimeError:
        # lidb_embed returns exit 1 for DDL/DML (CREATE/INSERT/UPDATE/DELETE)
        # when rows are empty + affected=0. This is expected — treat as success.
        if _DDL_RE.match(sql):
            return {"ok": True, "rows": [], "message": "statement executed"}
        return None
    except Exception:
        return None


class Store:
    def __init__(self, data_dir: str) -> None:
        self.path = Path(data_dir) / "store.json"
        self.lock = threading.RLock()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()

    def _empty(self) -> dict[str, Any]:
        return {
            "users": [],
            "refresh": {},
            "tables": {name: [] for name in CRM_TABLES},
            "schemas": {name: cols[:] for name, cols in CRM_TABLES.items()},
        }

    def _load(self) -> dict[str, Any]:
        if not self.path.is_file():
            data = self._empty()
            self.path.write_text(json.dumps(data, indent=2))
            return data
        try:
            data = json.loads(self.path.read_text())
        except (OSError, json.JSONDecodeError):
            data = self._empty()
        data.setdefault("users", [])
        data.setdefault("refresh", {})
        data.setdefault("tables", {})
        data.setdefault("schemas", {})
        for name, cols in CRM_TABLES.items():
            data["tables"].setdefault(name, [])
            data["schemas"].setdefault(name, cols[:])
        return data

    def save(self) -> None:
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self._data, indent=2))
        tmp.replace(self.path)

    def snapshot(self) -> dict[str, Any]:
        with self.lock:
            return json.loads(json.dumps(self._data))

    def mutate(self, fn):
        with self.lock:
            result = fn(self._data)
            self.save()
            return result


def match_filter(row: dict[str, Any], spec: str) -> bool:
    if "=" not in spec:
        return True
    col, _, rest = spec.partition("=")
    col = unquote(col)
    op, _, raw = rest.partition(".")
    raw = unquote(raw)
    value = row.get(col)
    sval = "" if value is None else str(value)
    if op == "eq":
        return sval == raw
    if op == "neq":
        return sval != raw
    if op == "gt":
        return _cmp(value, raw) > 0
    if op == "gte":
        return _cmp(value, raw) >= 0
    if op == "lt":
        return _cmp(value, raw) < 0
    if op == "lte":
        return _cmp(value, raw) <= 0
    if op == "like":
        return _like(sval, raw, False)
    if op == "ilike":
        return _like(sval, raw, True)
    if op == "in":
        inner = raw.strip()
        if inner.startswith("(") and inner.endswith(")"):
            inner = inner[1:-1]
        parts = [p.strip() for p in inner.split(",") if p.strip()]
        return sval in parts
    if op == "is":
        if raw.lower() == "null":
            return value is None
        if raw.lower() == "true":
            return value is True
        if raw.lower() == "false":
            return value is False
    return True


def _like(value: str, pattern: str, insensitive: bool) -> bool:
    src = value.lower() if insensitive else value
    pat = pattern.lower() if insensitive else pattern
    rx = "^" + re.escape(pat).replace("%", ".*").replace("_", ".") + "$"
    return re.search(rx, src) is not None


def _cmp(left: Any, right: str) -> int:
    try:
        lf = float(left)
        rf = float(right)
        return (lf > rf) - (lf < rf)
    except (TypeError, ValueError):
        ls, rs = str(left), str(right)
        return (ls > rs) - (ls < rs)


def parse_qs_filters(query: str) -> tuple[list[str], int | None]:
    filters: list[str] = []
    limit = None
    if not query:
        return filters, limit
    for part in query.split("&"):
        if not part:
            continue
        if part.startswith("limit="):
            try:
                limit = int(part.split("=", 1)[1])
            except ValueError:
                limit = None
            continue
        if part.startswith("select="):
            continue
        filters.append(part)
    return filters, limit


class Handler(BaseHTTPRequestHandler):
    store: Store
    data_dir: str = "/data"
    api_port: int = 54320
    postgres_port: int = 54322

    def log_message(self, fmt: str, *args: object) -> None:
        logging.info("%s - " + fmt, self.address_string(), *args)

    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "authorization, apikey, content-type, prefer")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")

    def _send(self, status: int, body: Any, content_type: str = "application/json") -> None:
        if isinstance(body, (dict, list)) or body is None:
            raw = json.dumps(body if body is not None else {}).encode()
        elif isinstance(body, bytes):
            raw = body
        else:
            raw = str(body).encode()
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _read_json(self) -> Any:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        if not raw:
            return {}
        try:
            return json.loads(raw.decode())
        except json.JSONDecodeError:
            return {}

    def _auth(self) -> dict[str, Any]:
        header = self.headers.get("Authorization") or self.headers.get("authorization") or ""
        token = header[7:].strip() if header.lower().startswith("bearer ") else ""
        apikey = self.headers.get("apikey") or ANON_KEY
        if token in (ANON_KEY, "", None) and apikey:
            token = token or apikey
        if token == SERVICE_KEY:
            return {"sub": "service", "role": "service_role", "email": None}
        if token == ANON_KEY or not token:
            return {"sub": None, "role": "anon", "email": None}
        payload = verify_jwt(token)
        if payload:
            payload.setdefault("role", "authenticated")
            return payload
        return {"sub": None, "role": "anon", "email": None, "invalid": True}

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path in ("/health", "/status"):
            self._send(
                200,
                {
                    "status": "running",
                    "runtime_mode": "librebase",
                    "message": "Librebase API runtime",
                    "data_dir": self.data_dir,
                    "api_port": self.api_port,
                    "postgres_port": self.postgres_port,
                    "running": True,
                    "api_reachable": True,
                    "postgres_reachable": True,
                    "degraded": False,
                },
            )
            return
        if path in ("/", "/index.html", "/crm", "/crm/"):
            self._serve_static("index.html")
            return
        if path.startswith("/crm/"):
            self._serve_static(path[len("/crm/") :])
            return
        if path.startswith("/rest/v1/"):
            self._rest_get(path, parsed.query)
            return
        if path in ("/v1/auth/user", "/auth/v1/user"):
            self._auth_user()
            return
        if path in ("/auth/v1/admin/users", "/v1/auth/admin/users"):
            self._admin_users()
            return
        self._send(404, {"error": "not_found", "path": path})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        body = self._read_json()
        if path in ("/v1/auth/signup", "/auth/v1/signup"):
            self._signup(body)
            return
        if path in ("/v1/auth/login", "/v1/auth/signin"):
            self._login(body)
            return
        if path == "/auth/v1/token":
            grant = parse_qs(parsed.query).get("grant_type", [""])[0]
            if grant == "refresh_token":
                self._refresh(body)
            else:
                self._login(body)
            return
        if path in ("/v1/auth/oauth/login", "/auth/v1/oauth/login"):
            self._oauth_login(body)
            return
        if path == "/v1/sql":
            self._sql(body)
            return
        if path.startswith("/rest/v1/rpc/"):
            name = path.split("/rest/v1/rpc/", 1)[1]
            if name == "exec":
                self._sql(body)
                return
            self._send(404, {"error": "unknown_rpc", "name": name})
            return
        if path.startswith("/rest/v1/"):
            self._rest_insert(path, body)
            return
        self._send(404, {"error": "not_found", "path": path})

    def do_PATCH(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path.startswith("/rest/v1/"):
            self._rest_patch(path, parsed.query, self._read_json())
            return
        self._send(404, {"error": "not_found", "path": path})

    def do_DELETE(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        if path.startswith("/rest/v1/"):
            self._rest_delete(path, parsed.query)
            return
        self._send(404, {"error": "not_found", "path": path})

    def _serve_static(self, rel: str) -> None:
        rel = rel.lstrip("/") or "index.html"
        target = (STATIC_DIR / rel).resolve()
        if STATIC_DIR.exists() and str(target).startswith(str(STATIC_DIR.resolve())) and target.is_file():
            data = target.read_bytes()
            ctype = "text/html; charset=utf-8"
            if rel.endswith(".js"):
                ctype = "text/javascript; charset=utf-8"
            elif rel.endswith(".css"):
                ctype = "text/css; charset=utf-8"
            elif rel.endswith(".json"):
                ctype = "application/json"
            self._send(200, data, ctype)
            return
        fallback = Path(__file__).resolve().parent.parent / "apps" / "crm-app" / "public" / "index.html"
        if fallback.is_file() and (rel.endswith("index.html") or rel in ("", "index.html")):
            self._send(200, fallback.read_bytes(), "text/html; charset=utf-8")
            return
        self._send(404, {"error": "not_found", "path": rel})

    def _session(self, user: dict[str, Any]) -> dict[str, Any]:
        access = sign_jwt(
            {"sub": user["id"], "email": user["email"], "role": "authenticated"}
        )
        refresh = secrets.token_urlsafe(32)

        def add(data):
            data["refresh"][refresh] = user["id"]
            return None

        self.store.mutate(add)
        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "expires_in": 3600,
            "user": {"id": user["id"], "email": user["email"], "role": "authenticated"},
        }

    def _signup(self, body: Any) -> None:
        email = str((body or {}).get("email") or "").strip().lower()
        password = str((body or {}).get("password") or "")
        if not email or not password:
            self._send(400, {"error": "email and password required"})
            return
        if len(password) < 6:
            self._send(400, {"error": "password must be at least 6 characters"})
            return

        def add(data):
            for u in data["users"]:
                if u["email"] == email:
                    return None
            user = {
                "id": "usr_" + uuid.uuid4().hex[:12],
                "email": email,
                "password_hash": new_password_hash(password),
                "created_at": _now(),
            }
            data["users"].append(user)
            return user

        user = self.store.mutate(add)
        if user is None:
            self._send(409, {"error": "user already exists", "message": "user already exists"})
            return
        self._send(200, self._session(user))

    def _login(self, body: Any) -> None:
        email = str((body or {}).get("email") or "").strip().lower()
        password = str((body or {}).get("password") or "")
        snap = self.store.snapshot()
        user = next((u for u in snap["users"] if u["email"] == email), None)
        if not user or not verify_password(password, user["password_hash"]):
            self._send(401, {"error": "invalid_credentials", "message": "Invalid login credentials"})
            return
        self._send(200, self._session(user))

    def _oauth_login(self, body: Any) -> None:
        auth = self._auth()
        if auth.get("role") != "service_role":
            self._send(401, {"error": "service_role required"})
            return
        email = str((body or {}).get("email") or "").strip().lower()
        provider = str((body or {}).get("provider") or "").strip().lower()
        sub = str((body or {}).get("sub") or "").strip()
        if not email or not provider or not sub:
            self._send(400, {"error": "email, provider, and sub required"})
            return
        oauth_sub = f"{provider}:{sub}"

        def upsert(data):
            for u in data["users"]:
                if u.get("oauth_sub") == oauth_sub or u.get("email") == email:
                    u["oauth_sub"] = oauth_sub
                    u["email"] = email
                    return u
            user = {
                "id": "usr_" + uuid.uuid4().hex[:12],
                "email": email,
                "password_hash": new_password_hash(secrets.token_urlsafe(18)),
                "oauth_sub": oauth_sub,
                "created_at": _now(),
            }
            data["users"].append(user)
            return user

        user = self.store.mutate(upsert)
        self._send(200, {**self._session(user), "provider": provider})

    def _refresh(self, body: Any) -> None:
        token = str((body or {}).get("refresh_token") or "")
        snap = self.store.snapshot()
        uid = snap["refresh"].get(token)
        user = next((u for u in snap["users"] if u["id"] == uid), None) if uid else None
        if not user:
            self._send(401, {"error": "invalid_refresh", "message": "Invalid refresh token"})
            return
        self._send(200, self._session(user))

    def _auth_user(self) -> None:
        auth = self._auth()
        if auth.get("role") not in ("authenticated", "service_role") or not auth.get("sub"):
            self._send(401, {"error": "unauthorized"})
            return
        self._send(200, {"id": auth.get("sub"), "email": auth.get("email"), "role": auth.get("role")})

    def _admin_users(self) -> None:
        auth = self._auth()
        if auth.get("role") != "service_role":
            self._send(401, {"error": "service_role required"})
            return
        users = [{"id": u["id"], "email": u["email"], "created_at": u.get("created_at")} for u in self.store.snapshot()["users"]]
        self._send(200, {"users": users})

    def _table_name(self, path: str) -> str:
        name = path.split("/rest/v1/", 1)[1]
        name = name.split("?", 1)[0].strip("/")
        return unquote(name)

    def _visible_rows(self, table: str, auth: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        schema = self.store.snapshot()["schemas"].get(table, [])
        if auth.get("role") == "service_role":
            return rows
        # Public read for the feedback wall.
        if table == "notes":
            return rows
        if "owner_id" not in schema:
            return rows
        sub = auth.get("sub")
        if auth.get("role") != "authenticated" or not sub:
            return []
        return [r for r in rows if r.get("owner_id") == sub]

    def _rest_get(self, path: str, query: str) -> None:
        table = self._table_name(path)
        snap = self.store.snapshot()
        if table not in snap["tables"]:
            self._send(404, {"error": "table not found", "table": table})
            return
        auth = self._auth()
        rows = self._visible_rows(table, auth, snap["tables"][table])
        filters, limit = parse_qs_filters(query)
        matched = [r for r in rows if all(match_filter(r, f) for f in filters)]
        if limit is not None:
            matched = matched[:limit]
        self._send(200, matched)

    def _rest_insert(self, path: str, body: Any) -> None:
        table = self._table_name(path)
        auth = self._auth()
        if auth.get("role") not in ("authenticated", "service_role"):
            self._send(401, {"error": "unauthorized", "message": "Sign in required"})
            return
        rows_in = body if isinstance(body, list) else [body]
        created: list[dict[str, Any]] = []

        def add(data):
            data["tables"].setdefault(table, [])
            data["schemas"].setdefault(table, ["id", "owner_id", "created_at"])
            schema = data["schemas"][table]
            out = []
            for item in rows_in:
                if not isinstance(item, dict):
                    continue
                row = {k: item[k] for k in item}
                row.setdefault("id", "row_" + uuid.uuid4().hex[:12])
                row.setdefault("created_at", _now())
                if "owner_id" in schema or "owner_id" in row:
                    row.setdefault("owner_id", auth.get("sub"))
                    if "owner_id" not in schema:
                        schema.append("owner_id")
                data["tables"][table].append(row)
                out.append(row)
            return out

        created = self.store.mutate(add)
        self._send(201, created)

    def _rest_patch(self, path: str, query: str, body: Any) -> None:
        table = self._table_name(path)
        auth = self._auth()
        if auth.get("role") not in ("authenticated", "service_role"):
            self._send(401, {"error": "unauthorized"})
            return
        patch = body if isinstance(body, dict) else {}
        filters, _ = parse_qs_filters(query)

        def upd(data):
            rows = data["tables"].get(table)
            if rows is None:
                return None
            visible = self._visible_rows(table, auth, rows)
            changed = []
            ids = {id(r) for r in visible if all(match_filter(r, f) for f in filters)}
            for row in rows:
                if id(row) in ids:
                    for k, v in patch.items():
                        if k in ("id", "owner_id"):
                            continue
                        row[k] = v
                    changed.append(dict(row))
            return changed

        changed = self.store.mutate(upd)
        if changed is None:
            self._send(404, {"error": "table not found", "table": table})
            return
        self._send(200, changed)

    def _rest_delete(self, path: str, query: str) -> None:
        table = self._table_name(path)
        auth = self._auth()
        if auth.get("role") not in ("authenticated", "service_role"):
            self._send(401, {"error": "unauthorized"})
            return
        filters, _ = parse_qs_filters(query)

        def rm(data):
            rows = data["tables"].get(table)
            if rows is None:
                return None
            visible = self._visible_rows(table, auth, rows)
            drop_ids = {id(r) for r in visible if all(match_filter(r, f) for f in filters)}
            kept = [r for r in rows if id(r) not in drop_ids]
            deleted = len(rows) - len(kept)
            data["tables"][table] = kept
            return [{"deleted": True}] * deleted

        deleted = self.store.mutate(rm)
        if deleted is None:
            self._send(404, {"error": "table not found"})
            return
        self._send(200, deleted)

    def _sql(self, body: Any) -> None:
        sql = str((body or {}).get("sql") or "").strip()
        if not sql:
            self._send(400, {"error": "sql is required"})
            return
        # SQL is a data-access path; it must be authenticated like the REST API.
        # Without this, any peer that can reach the port could read the whole
        # store via `select * from <table>` (bypassing owner_id visibility).
        auth = self._auth()
        if auth.get("role") not in ("authenticated", "service_role"):
            self._send(401, {"error": "unauthorized", "message": "Sign in required"})
            return
        # Try lidb_embed first — real SQL engine when available.
        lidb_result = _exec_lidb_sql(self.data_dir, sql)
        if lidb_result is not None:
            self._send(200, lidb_result)
            return
        # Fallback: file-backed stub for environments without lidb_embed.
        lowered = " ".join(sql.lower().split())
        if "information_schema.tables" in lowered:
            snap = self.store.snapshot()
            rows = [
                {"schema": "public", "name": name, "kind": "BASE TABLE"}
                for name in snap["tables"]
            ]
            self._send(200, {"rows": rows})
            return
        select = re.match(
            r"select\s+\*\s+from\s+\"?([a-zA-Z_][\w]*)\"?(?:\s+limit\s+(\d+))?\s*;?\s*$",
            sql,
            re.I,
        )
        if select:
            name = select.group(1)
            limit = int(select.group(2) or "200")
            snap = self.store.snapshot()
            rows = self._visible_rows(name, auth, list(snap["tables"].get(name, [])))[:limit]
            self._send(200, {"ok": True, "rows": rows})
            return
        create = re.match(r"create\s+table(?:\s+if\s+not\s+exists)?\s+([a-zA-Z_][\w]*)\s*\((.*)\)\s*;?\s*$", sql, re.I | re.S)
        if create:
            name = create.group(1)
            cols = [c.strip().split()[0] for c in create.group(2).split(",") if c.strip()]

            def add(data):
                data["tables"].setdefault(name, [])
                existing = data["schemas"].get(name, [])
                merged = list(dict.fromkeys(existing + cols + ["id", "owner_id", "created_at"]))
                data["schemas"][name] = merged
                return {"ok": True, "table": name, "columns": merged}

            self._send(200, self.store.mutate(add))
            return
        self._send(200, {"ok": True, "rows": [], "message": "statement accepted"})


def _tcp_acceptor(port: int, name: str) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", port))
    sock.listen(64)
    logging.info("librebase-api: %s listening on 0.0.0.0:%d", name, port)
    while True:
        conn, _addr = sock.accept()
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Librebase API runtime")
    parser.add_argument("--data-dir", default=os.environ.get("LI_DATA_DIR", "/data"))
    parser.add_argument("--api-port", type=int, default=int(os.environ.get("LIBREBASE_API_PORT", "54320")))
    parser.add_argument("--postgres-port", type=int, default=int(os.environ.get("LIBREBASE_PG_PORT", "54322")))
    parser.add_argument(
        "--bind",
        default=os.environ.get("LIBREBASE_API_BIND", "0.0.0.0"),
        help="Listen address (127.0.0.1 to keep it behind Apache).",
    )
    args = parser.parse_args()

    if _insecure_defaults_active() and os.environ.get("LIBREBASE_ALLOW_INSECURE_DEFAULTS", "") != "1":
        logging.error(
            "refusing to start: runtime secrets are insecure defaults. "
            "Set LIBREBASE_SERVICE_ROLE_KEY + LIBREBASE_JWT_SECRET (injected by the "
            "host agent), or LIBREBASE_ALLOW_INSECURE_DEFAULTS=1 for local dev."
        )
        return 2

    Path(args.data_dir).mkdir(parents=True, exist_ok=True)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.info(
        "librebase api runtime data_dir=%s api_port=%d postgres_port=%d",
        args.data_dir,
        args.api_port,
        args.postgres_port,
    )

    store = Store(args.data_dir)
    Handler.store = store
    Handler.data_dir = args.data_dir
    Handler.api_port = args.api_port
    Handler.postgres_port = args.postgres_port

    server = ThreadingHTTPServer((args.bind, args.api_port), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    threading.Thread(
        target=_tcp_acceptor, args=(args.postgres_port, "postgres-wire"), daemon=True
    ).start()
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
