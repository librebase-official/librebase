#!/usr/bin/env python3
"""Librebase Admin HTTP server — SQLite backend for Librebase Studio (self-host).

Cloud deployments use the same SQL schema via lidb embed through src/seam.li; this Python
shim is the interim self-host runtime until li-httpd + lic seam + lidb land together.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = ROOT / "migrations"

DEFAULT_DB = Path.home() / ".local" / "share" / "librebase" / "org.db"
JWT_TTL_SECONDS = 60 * 60 * 24 * 7  # legacy; replaced by ACCESS_TTL for console sessions
ACCESS_TTL_SECONDS = 15 * 60  # access JWT lifetime (short-lived)
REFRESH_TTL_SECONDS = 60 * 60 * 24 * 30  # refresh token lifetime (rotated)

try:  # Argon2id when available; stdlib scrypt fallback otherwise
    from argon2 import PasswordHasher as _Argon2Hasher
    from argon2.exceptions import InvalidHashError as _Argon2InvalidHash
    from argon2.exceptions import VerifyMismatchError as _Argon2Mismatch

    _ARGON2_HASHER = _Argon2Hasher(time_cost=3, memory_cost=64 * 1024, parallelism=2)
    _ARGON2 = True
except Exception:  # pragma: no cover - fallback path
    _ARGON2_HASHER = None
    _ARGON2 = False

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def sign_jwt(payload: dict[str, Any], secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    segments = [
        b64url(json.dumps(header, separators=(",", ":")).encode()),
        b64url(json.dumps(payload, separators=(",", ":")).encode()),
    ]
    signing_input = ".".join(segments).encode()
    sig = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    segments.append(b64url(sig))
    return ".".join(segments)


def verify_jwt(token: str, secret: str) -> dict[str, Any] | None:
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}".encode()
        expected = b64url(hmac.new(secret.encode(), signing_input, hashlib.sha256).digest())
        if not hmac.compare_digest(expected, sig_b64):
            return None
        pad = "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + pad))
        exp = payload.get("exp")
        if exp is not None and int(exp) < int(time.time()):
            return None
        return payload
    except (ValueError, json.JSONDecodeError, KeyError):
        return None


def hash_password(password: str) -> str:
    if _ARGON2:
        return "argon2id$" + _ARGON2_HASHER.hash(password)
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode(), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P
    )
    return "scrypt$" + b64url(salt) + "$" + b64url(digest)


def _b64url_decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def verify_password(password: str, stored: str) -> bool:
    if stored == "pw-hash":
        return True
    if not stored:
        return False
    if stored.startswith("argon2id$"):
        if not _ARGON2:
            return False
        try:
            _ARGON2_HASHER.verify(stored[len("argon2id$"):], password)
            return True
        except (_Argon2Mismatch, _Argon2InvalidHash):
            return False
    if stored.startswith("scrypt$"):
        _, salt_b64, digest_b64 = stored.split("$", 2)
        check = hashlib.scrypt(
            password.encode(),
            salt=_b64url_decode(salt_b64),
            n=_SCRYPT_N,
            r=_SCRYPT_R,
            p=_SCRYPT_P,
        )
        return hmac.compare_digest(check, _b64url_decode(digest_b64))
    if stored.startswith("pbkdf2$"):
        _, salt, digest = stored.split("$", 2)
        check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
        return hmac.compare_digest(check, digest)
    return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def session_expiry() -> str:
    return utc_now_offset(REFRESH_TTL_SECONDS)


def utc_now_offset(seconds: int) -> str:
    dt = datetime.now(timezone.utc).replace(microsecond=0)
    return (dt + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def issue_session(
    db: "LiorgDb",
    jwt_secret: str,
    user_id: str,
    org_id: str,
    role: str,
    edition: str,
) -> tuple[str, str]:
    """Create a session, return (access_token, refresh_token)."""
    session_id = new_id("sess")
    refresh_token = secrets.token_urlsafe(48)
    now = utc_now()
    db.execute(
        "INSERT INTO sessions (id, user_id, refresh_token_hash, created_at, expires_at, revoked_at) "
        "VALUES (?, ?, ?, ?, ?, NULL)",
        (session_id, user_id, hash_token(refresh_token), now, session_expiry()),
    )
    access = sign_jwt(
        {
            "sub": user_id,
            "org_id": org_id,
            "role": role,
            "edition": edition,
            "sid": session_id,
            "exp": int(time.time()) + ACCESS_TTL_SECONDS,
        },
        jwt_secret,
    )
    return access, refresh_token


def refresh_session(
    db: "LiorgDb", jwt_secret: str, refresh_token: str
) -> dict[str, Any] | None:
    """Validate + rotate a refresh token, returning the new token pair."""
    token_hash = hash_token(refresh_token)
    row = db.fetchone("SELECT * FROM sessions WHERE refresh_token_hash = ?", (token_hash,))
    if not row or row["revoked_at"]:
        return None
    if row["expires_at"] < utc_now():
        return None
    user = db.fetchone("SELECT * FROM users WHERE id = ?", (row["user_id"],))
    if not user:
        return None
    member = db.fetchone(
        "SELECT org_id, role FROM members WHERE user_id = ? ORDER BY created_at LIMIT 1",
        (row["user_id"],),
    )
    if not member:
        return None
    db.execute(
        "UPDATE sessions SET revoked_at = ? WHERE id = ?",
        (utc_now(), row["id"]),
    )
    org_row = db.fetchone(
        "SELECT edition FROM organizations WHERE id = ?", (member["org_id"],)
    )
    edition = org_row["edition"] if org_row else "self-host"
    access, refresh = issue_session(
        db, jwt_secret, row["user_id"], member["org_id"], member["role"], edition
    )
    return {
        "token": access,
        "refreshToken": refresh,
        "orgId": member["org_id"],
    }


def revoke_session(db: "LiorgDb", refresh_token: str | None, sid: str | None) -> bool:
    if refresh_token:
        row = db.fetchone(
            "SELECT id FROM sessions WHERE refresh_token_hash = ?",
            (hash_token(refresh_token),),
        )
        if row:
            db.execute(
                "UPDATE sessions SET revoked_at = ? WHERE id = ?", (utc_now(), row["id"])
            )
            return True
    if sid:
        db.execute("UPDATE sessions SET revoked_at = ? WHERE id = ?", (utc_now(), sid))
        return True
    return False


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "org"


class LiorgDb:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.migrate()

    def migrate(self) -> None:
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        for migration in sorted(MIGRATIONS.glob("*.sql")):
            version = migration.name
            done = self.conn.execute(
                "SELECT 1 FROM schema_migrations WHERE version = ?", (version,)
            ).fetchone()
            if done:
                continue
            sql = migration.read_text(encoding="utf-8")
            cleaned_lines: list[str] = []
            for line in sql.splitlines():
                stripped = line.strip()
                if stripped.startswith("--"):
                    continue
                cleaned_lines.append(line)
            for stmt in "\n".join(cleaned_lines).split(";"):
                stmt = stmt.strip()
                if not stmt:
                    continue
                try:
                    self.conn.execute(stmt)
                except sqlite3.OperationalError as exc:
                    msg = str(exc).lower()
                    if "duplicate column" not in msg and "already exists" not in msg:
                        raise
            self.conn.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                (version, utc_now()),
            )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def fetchone(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        cur = self.conn.execute(sql, params)
        return cur.fetchone()

    def fetchall(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        cur = self.conn.execute(sql, params)
        return cur.fetchall()

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.conn.execute(sql, params)
        self.conn.commit()


def entitlement_for_edition(edition: str, feature_key: str) -> int:
    if edition == "self-host":
        if feature_key in ("project.create", "instance.launch", "host.create"):
            return 1
        return 0
    if edition == "cloud-free":
        if feature_key == "project.create":
            return 2
        if feature_key in ("instance.launch", "host.create"):
            return 1
        return 0
    if edition == "cloud-paid":
        if feature_key in (
            "project.create",
            "instance.launch",
            "host.create",
            "k8s.provision",
            "branching.pitr",
        ):
            return 1
        return 0
    return 0


def row_project(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "orgId": row["org_id"],
        "instanceId": row["instance_id"],
        "deploymentMode": row["deployment_mode"],
        "region": row["region"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def row_host(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "orgId": row["org_id"],
        "name": row["name"],
        "provider": row["provider"],
        "region": row["region"],
        "memMb": row["mem_mb"],
        "memUsedMb": row["mem_used_mb"],
        "status": row["status"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def row_instance(row: sqlite3.Row) -> dict[str, Any]:
    ports = None
    if row["ports_json"]:
        ports = json.loads(row["ports_json"])
    payload: dict[str, Any] = {
        "id": row["id"],
        "name": row["name"],
        "orgId": row["org_id"],
        "dataDir": row["data_dir"] or "",
        "deploymentMode": row["deployment_mode"],
        "runtimeTarget": row["runtime_target"],
        "status": row["status"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }
    if ports:
        payload["ports"] = ports
    if row["host_id"]:
        payload["hostId"] = row["host_id"]
    if row["mem_limit_mb"] is not None:
        payload["memLimitMb"] = row["mem_limit_mb"]
    if row["k8s_namespace"]:
        payload["k8sNamespace"] = row["k8s_namespace"]
    if row["k8s_degraded"] is not None:
        payload["k8sDegraded"] = bool(row["k8s_degraded"])
    if row["k8s_message"]:
        payload["k8sMessage"] = row["k8s_message"]
    return payload


class LiorgHandler(BaseHTTPRequestHandler):
    db: LiorgDb
    jwt_secret: str

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def send_json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def bearer_claims(self) -> dict[str, Any] | None:
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        token = auth[7:].strip()
        return verify_jwt(token, self.jwt_secret)

    def require_org_member(self, org_id: str) -> dict[str, Any] | None:
        """Return JWT claims if caller is a member of org_id; else send 401/403 and None."""
        claims = self.bearer_claims()
        if not claims:
            self.send_json(401, {"error": "unauthorized"})
            return None
        user_id = claims.get("sub")
        if not user_id:
            self.send_json(401, {"error": "unauthorized"})
            return None
        if claims.get("org_id") == org_id:
            return claims
        row = self.db.fetchone(
            "SELECT 1 FROM members WHERE org_id = ? AND user_id = ?",
            (org_id, user_id),
        )
        if not row:
            self.send_json(403, {"error": "forbidden"})
            return None
        return claims

    def org_edition(self, org_id: str) -> str:
        row = self.db.fetchone("SELECT edition FROM organizations WHERE id = ?", (org_id,))
        return row["edition"] if row else "self-host"

    def check_entitlement(self, org_id: str, feature_key: str) -> dict[str, Any]:
        override = self.db.fetchone(
            "SELECT enabled FROM org_entitlements WHERE org_id = ? AND feature_key = ?",
            (org_id, feature_key),
        )
        if override:
            code = int(override["enabled"])
        else:
            edition = self.org_edition(org_id)
            code = entitlement_for_edition(edition, feature_key)
        return {
            "enabled": code != 0,
            "status": ("allowed", "denied", "limited")[code],
            "code": code,
        }

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/health":
            self.send_json(200, {"ok": True})
            return

        if path == "/org/v1/me":
            claims = self.bearer_claims()
            if not claims:
                self.send_json(401, {"error": "unauthorized"})
                return
            user = self.db.fetchone("SELECT id, email FROM users WHERE id = ?", (claims["sub"],))
            if not user:
                self.send_json(401, {"error": "user not found"})
                return
            memberships = self.db.fetchall(
                "SELECT org_id, role FROM members WHERE user_id = ?",
                (user["id"],),
            )
            self.send_json(
                200,
                {
                    "user": {"id": user["id"], "email": user["email"]},
                    "activeOrgId": claims.get("org_id"),
                    "role": claims.get("role"),
                    "edition": claims.get("edition"),
                    "memberships": [
                        {"orgId": m["org_id"], "role": m["role"]} for m in memberships
                    ],
                },
            )
            return

        members_match = re.fullmatch(r"/org/v1/orgs/([^/]+)/members", path)
        if members_match:
            org_id = members_match.group(1)
            claims = self.bearer_claims()
            if not claims or claims.get("org_id") != org_id:
                self.send_json(403, {"error": "forbidden"})
                return
            rows = self.db.fetchall(
                "SELECT m.user_id, u.email, m.role, m.created_at "
                "FROM members m JOIN users u ON u.id = m.user_id "
                "WHERE m.org_id = ?",
                (org_id,),
            )
            self.send_json(
                200,
                [
                    {
                        "userId": r["user_id"],
                        "email": r["email"],
                        "role": r["role"],
                        "createdAt": r["created_at"],
                    }
                    for r in rows
                ],
            )
            return

        projects_match = re.fullmatch(r"/org/v1/orgs/([^/]+)/projects", path)
        if projects_match:
            org_id = projects_match.group(1)
            if not self.require_org_member(org_id):
                return
            rows = self.db.fetchall(
                "SELECT * FROM projects WHERE org_id = ? ORDER BY created_at",
                (org_id,),
            )
            self.send_json(200, [row_project(r) for r in rows])
            return

        project_one = re.fullmatch(r"/org/v1/orgs/([^/]+)/projects/([^/]+)", path)
        if project_one:
            org_id, project_id = project_one.groups()
            if not self.require_org_member(org_id):
                return
            row = self.db.fetchone(
                "SELECT * FROM projects WHERE org_id = ? AND id = ?",
                (org_id, project_id),
            )
            if not row:
                self.send_json(404, {"error": "project not found"})
                return
            self.send_json(200, row_project(row))
            return

        instances_match = re.fullmatch(r"/org/v1/orgs/([^/]+)/instances", path)
        if instances_match:
            org_id = instances_match.group(1)
            if not self.require_org_member(org_id):
                return
            rows = self.db.fetchall(
                "SELECT * FROM instances WHERE org_id = ? ORDER BY created_at",
                (org_id,),
            )
            self.send_json(200, [row_instance(r) for r in rows])
            return

        instance_one = re.fullmatch(r"/org/v1/orgs/([^/]+)/instances/([^/]+)", path)
        if instance_one:
            org_id, inst_id = instance_one.groups()
            if not self.require_org_member(org_id):
                return
            row = self.db.fetchone(
                "SELECT * FROM instances WHERE org_id = ? AND id = ?",
                (org_id, inst_id),
            )
            if not row:
                self.send_json(404, {"error": "instance not found"})
                return
            self.send_json(200, row_instance(row))
            return

        ent_match = re.fullmatch(r"/org/v1/orgs/([^/]+)/entitlements/([^/]+)", path)
        if ent_match:
            org_id, feature_key = ent_match.groups()
            if not self.require_org_member(org_id):
                return
            self.send_json(200, self.check_entitlement(org_id, feature_key))
            return

        hosts_match = re.fullmatch(r"/org/v1/orgs/([^/]+)/hosts", path)
        if hosts_match:
            org_id = hosts_match.group(1)
            if not self.require_org_member(org_id):
                return
            rows = self.db.fetchall(
                "SELECT * FROM hosts WHERE org_id = ? ORDER BY created_at",
                (org_id,),
            )
            self.send_json(200, [row_host(r) for r in rows])
            return

        host_one = re.fullmatch(r"/org/v1/orgs/([^/]+)/hosts/([^/]+)", path)
        if host_one:
            org_id, host_id = host_one.groups()
            if not self.require_org_member(org_id):
                return
            row = self.db.fetchone(
                "SELECT * FROM hosts WHERE org_id = ? AND id = ?",
                (org_id, host_id),
            )
            if not row:
                self.send_json(404, {"error": "host not found"})
                return
            self.send_json(200, row_host(row))
            return

        self.send_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        body = self.read_json()

        if path == "/org/v1/setup":
            if self.db.fetchone("SELECT id FROM organizations LIMIT 1"):
                self.send_json(409, {"error": "already configured"})
                return
            name = str(body.get("name", "")).strip()
            owner_email = str(body.get("ownerEmail", body.get("owner_email", ""))).strip()
            password = str(body.get("password", ""))
            slug = str(body.get("slug", slugify(name))).strip()
            if not name or not owner_email or not password:
                self.send_json(400, {"error": "name, ownerEmail, password required"})
                return
            org_id = new_id("org")
            user_id = new_id("user")
            now = utc_now()
            self.db.execute(
                "INSERT INTO organizations (id, name, slug, edition, created_at) VALUES (?, ?, ?, ?, ?)",
                (org_id, name, slug, "self-host", now),
            )
            self.db.execute(
                "INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (user_id, owner_email, hash_password(password), now),
            )
            self.db.execute(
                "INSERT INTO members (org_id, user_id, role, created_at) VALUES (?, ?, ?, ?)",
                (org_id, user_id, "owner", now),
            )
            token, refresh_token = issue_session(
                self.db, self.jwt_secret, user_id, org_id, "owner", "self-host"
            )
            self.send_json(
                201,
                {
                    "orgId": org_id,
                    "token": token,
                    "refreshToken": refresh_token,
                    "expiresIn": ACCESS_TTL_SECONDS,
                },
            )
            return

        if path == "/org/v1/auth/login":
            email = str(body.get("email", "")).strip()
            password = str(body.get("password", ""))
            user = self.db.fetchone("SELECT * FROM users WHERE email = ?", (email,))
            if not user or not verify_password(password, user["password_hash"] or ""):
                self.send_json(401, {"error": "invalid credentials"})
                return
            member = self.db.fetchone(
                "SELECT org_id, role FROM members WHERE user_id = ? ORDER BY created_at LIMIT 1",
                (user["id"],),
            )
            if not member:
                self.send_json(403, {"error": "no organization membership"})
                return
            edition = self.org_edition(member["org_id"])
            token, refresh_token = issue_session(
                self.db, self.jwt_secret, user["id"], member["org_id"], member["role"], edition
            )
            self.send_json(
                200,
                {
                    "token": token,
                    "refreshToken": refresh_token,
                    "orgId": member["org_id"],
                    "expiresIn": ACCESS_TTL_SECONDS,
                },
            )
            return

        if path == "/org/v1/auth/refresh":
            refresh_token = str(body.get("refreshToken", body.get("refresh_token", ""))).strip()
            if not refresh_token:
                self.send_json(400, {"error": "refreshToken required"})
                return
            result = refresh_session(self.db, self.jwt_secret, refresh_token)
            if not result:
                self.send_json(401, {"error": "invalid or expired refresh token"})
                return
            result["expiresIn"] = ACCESS_TTL_SECONDS
            self.send_json(200, result)
            return

        if path == "/org/v1/auth/logout":
            refresh_token = str(body.get("refreshToken", body.get("refresh_token", ""))).strip()
            sid = None
            claims = self.bearer_claims()
            if claims:
                sid = claims.get("sid")
            revoked = revoke_session(self.db, refresh_token or None, sid)
            self.send_json(200, {"ok": True, "revoked": revoked})
            return

        if path == "/org/v1/orgs":
            claims = self.bearer_claims()
            if not claims:
                self.send_json(401, {"error": "unauthorized"})
                return
            name = str(body.get("name", "")).strip()
            edition = str(body.get("edition", "cloud-free")).strip()
            slug = str(body.get("slug", slugify(name))).strip()
            if not name:
                self.send_json(400, {"error": "name required"})
                return
            org_id = new_id("org")
            now = utc_now()
            self.db.execute(
                "INSERT INTO organizations (id, name, slug, edition, created_at) VALUES (?, ?, ?, ?, ?)",
                (org_id, name, slug, edition, now),
            )
            self.db.execute(
                "INSERT INTO members (org_id, user_id, role, created_at) VALUES (?, ?, ?, ?)",
                (org_id, claims["sub"], "owner", now),
            )
            self.send_json(201, {"id": org_id, "name": name, "slug": slug, "edition": edition})
            return

        org_projects = re.fullmatch(r"/org/v1/orgs/([^/]+)/projects", path)
        if org_projects:
            org_id = org_projects.group(1)
            if not self.require_org_member(org_id):
                return
            gate = self.check_entitlement(org_id, "project.create")
            if gate["code"] == 0:
                self.send_json(403, {"error": "entitlement denied", "entitlement": gate})
                return
            name = str(body.get("name", "")).strip()
            instance_id = str(body.get("instanceId", body.get("instance_id", ""))).strip()
            deployment_mode = str(
                body.get("deploymentMode", body.get("deployment_mode", "dedicated"))
            ).strip()
            region = str(body.get("region", "local")).strip()
            if not name or not instance_id:
                self.send_json(400, {"error": "name and instanceId required"})
                return
            now = utc_now()
            project_id = new_id("proj")
            self.db.execute(
                "INSERT INTO projects "
                "(id, org_id, name, instance_id, deployment_mode, region, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (project_id, org_id, name, instance_id, deployment_mode, region, now, now),
            )
            row = self.db.fetchone("SELECT * FROM projects WHERE id = ?", (project_id,))
            self.send_json(201, row_project(row))
            return

        org_hosts = re.fullmatch(r"/org/v1/orgs/([^/]+)/hosts", path)
        if org_hosts:
            org_id = org_hosts.group(1)
            if not self.require_org_member(org_id):
                return
            gate = self.check_entitlement(org_id, "host.create")
            if gate["code"] == 0:
                self.send_json(403, {"error": "entitlement denied", "entitlement": gate})
                return
            name = str(body.get("name", "")).strip()
            if not name:
                self.send_json(400, {"error": "name required"})
                return
            now = utc_now()
            host_id = new_id("host")
            mem_mb = int(body.get("memMb", body.get("mem_mb", 512)))
            provider = str(body.get("provider", "linative-cloud")).strip()
            region = str(body.get("region", "local")).strip()
            status = str(body.get("status", "stopped")).strip()
            self.db.execute(
                "INSERT INTO hosts "
                "(id, org_id, name, provider, region, mem_mb, mem_used_mb, status, "
                "created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?)",
                (host_id, org_id, name, provider, region, mem_mb, status, now, now),
            )
            row = self.db.fetchone("SELECT * FROM hosts WHERE id = ?", (host_id,))
            self.send_json(201, row_host(row))
            return

        org_instances = re.fullmatch(r"/org/v1/orgs/([^/]+)/instances", path)
        if org_instances:
            org_id = org_instances.group(1)
            if not self.require_org_member(org_id):
                return
            gate = self.check_entitlement(org_id, "instance.launch")
            if gate["code"] == 0:
                self.send_json(403, {"error": "entitlement denied", "entitlement": gate})
                return
            name = str(body.get("name", "")).strip()
            if not name:
                self.send_json(400, {"error": "name required"})
                return
            now = utc_now()
            inst_id = new_id("inst")
            data_dir = str(body.get("dataDir", body.get("data_dir", ""))).strip()
            deployment_mode = str(
                body.get("deploymentMode", body.get("deployment_mode", "dedicated"))
            ).strip()
            runtime_target = str(
                body.get("runtimeTarget", body.get("runtime_target", "local"))
            ).strip()
            region = str(body.get("region", "local")).strip()
            status = str(body.get("status", "stopped")).strip()
            ports = body.get("ports")
            ports_json = json.dumps(ports) if ports else None
            k8s_namespace = body.get("k8sNamespace") or body.get("k8s_namespace")
            k8s_degraded = body.get("k8sDegraded")
            k8s_message = body.get("k8sMessage") or body.get("k8s_message")
            host_id = body.get("hostId") or body.get("host_id")
            mem_limit_mb = body.get("memLimitMb", body.get("mem_limit_mb"))
            if host_id:
                host_row = self.db.fetchone(
                    "SELECT * FROM hosts WHERE org_id = ? AND id = ?",
                    (org_id, host_id),
                )
                if not host_row:
                    self.send_json(404, {"error": "host not found"})
                    return
                mem = int(mem_limit_mb) if mem_limit_mb is not None else 0
                if mem and host_row["mem_used_mb"] + mem > host_row["mem_mb"]:
                    self.send_json(
                        409,
                        {
                            "error": "host memory budget exceeded",
                            "memMb": host_row["mem_mb"],
                            "memUsedMb": host_row["mem_used_mb"],
                            "requestedMb": mem,
                        },
                    )
                    return
            self.db.execute(
                "INSERT INTO instances "
                "(id, org_id, name, data_dir, deployment_mode, runtime_target, region, status, "
                "created_at, updated_at, ports_json, k8s_namespace, k8s_degraded, k8s_message, "
                "host_id, mem_limit_mb) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    inst_id,
                    org_id,
                    name,
                    data_dir,
                    deployment_mode,
                    runtime_target,
                    region,
                    status,
                    now,
                    now,
                    ports_json,
                    k8s_namespace,
                    int(k8s_degraded) if k8s_degraded is not None else None,
                    k8s_message,
                    host_id,
                    int(mem_limit_mb) if mem_limit_mb is not None else None,
                ),
            )
            if host_id and mem_limit_mb:
                self.db.execute(
                    "UPDATE hosts SET mem_used_mb = mem_used_mb + ?, updated_at = ? "
                    "WHERE id = ?",
                    (int(mem_limit_mb), now, host_id),
                )
            row = self.db.fetchone("SELECT * FROM instances WHERE id = ?", (inst_id,))
            self.send_json(201, row_instance(row))
            return

        org_invites = re.fullmatch(r"/org/v1/orgs/([^/]+)/invites", path)
        if org_invites:
            org_id = org_invites.group(1)
            claims = self.bearer_claims()
            if not claims or claims.get("org_id") != org_id:
                self.send_json(403, {"error": "forbidden"})
                return
            email = str(body.get("email", "")).strip()
            role = str(body.get("role", "developer")).strip()
            if not email:
                self.send_json(400, {"error": "email required"})
                return
            token = secrets.token_urlsafe(24)
            self.db.execute(
                "INSERT INTO invites (org_id, email, role, token, expires_at) VALUES (?, ?, ?, ?, ?)",
                (org_id, email, role, token, "2099-01-01T00:00:00Z"),
            )
            self.send_json(201, {"token": token, "email": email, "role": role})
            return

        self.send_json(404, {"error": "not found"})

    def do_PATCH(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        body = self.read_json()

        member_match = re.fullmatch(r"/org/v1/members/([^/]+)", path)
        if member_match:
            member_key = member_match.group(1)
            role = str(body.get("role", "")).strip()
            if not role:
                self.send_json(400, {"error": "role required"})
                return
            # member_key is user_id in this MVP
            row = self.db.fetchone(
                "SELECT org_id, user_id FROM members WHERE user_id = ? LIMIT 1",
                (member_key,),
            )
            if not row:
                self.send_json(404, {"error": "member not found"})
                return
            if not self.require_org_member(row["org_id"]):
                return
            self.db.execute(
                "UPDATE members SET role = ? WHERE org_id = ? AND user_id = ?",
                (role, row["org_id"], row["user_id"]),
            )
            self.send_json(200, {"userId": row["user_id"], "role": role})
            return

        inst_match = re.fullmatch(r"/org/v1/orgs/([^/]+)/instances/([^/]+)", path)
        if inst_match:
            org_id, inst_id = inst_match.groups()
            if not self.require_org_member(org_id):
                return
            fields: list[str] = []
            values: list[Any] = []
            mapping = {
                "status": "status",
                "dataDir": "data_dir",
                "data_dir": "data_dir",
                "k8sNamespace": "k8s_namespace",
                "k8s_namespace": "k8s_namespace",
                "k8sMessage": "k8s_message",
                "k8s_message": "k8s_message",
                "hostId": "host_id",
                "host_id": "host_id",
                "memLimitMb": "mem_limit_mb",
                "mem_limit_mb": "mem_limit_mb",
            }
            for key, col in mapping.items():
                if key in body:
                    fields.append(f"{col} = ?")
                    values.append(body[key])
            if "k8sDegraded" in body or "k8s_degraded" in body:
                fields.append("k8s_degraded = ?")
                val = body.get("k8sDegraded", body.get("k8s_degraded"))
                values.append(int(val) if val is not None else None)
            if "ports" in body:
                fields.append("ports_json = ?")
                values.append(json.dumps(body["ports"]))
            if not fields:
                self.send_json(400, {"error": "no patch fields"})
                return
            fields.append("updated_at = ?")
            values.append(utc_now())
            values.extend([org_id, inst_id])
            self.db.execute(
                f"UPDATE instances SET {', '.join(fields)} WHERE org_id = ? AND id = ?",
                tuple(values),
            )
            row = self.db.fetchone(
                "SELECT * FROM instances WHERE org_id = ? AND id = ?",
                (org_id, inst_id),
            )
            if not row:
                self.send_json(404, {"error": "instance not found"})
                return
            self.send_json(200, row_instance(row))
            return

        self.send_json(404, {"error": "not found"})


def main() -> None:
    host = os.environ.get(
        "LIBREBASE_ADMIN_BIND",
        os.environ.get("LIORG_BIND", "0.0.0.0"),
    )
    port = int(
        os.environ.get(
            "LIBREBASE_ADMIN_PORT",
            os.environ.get("LIORG_PORT", "54330"),
        )
    )
    db_path = Path(
        os.environ.get(
            "LIBREBASE_ADMIN_DB_PATH",
            os.environ.get("LIORG_DB_PATH", str(DEFAULT_DB)),
        )
    )
    secret = os.environ.get(
        "LIBREBASE_ADMIN_JWT_SECRET",
        os.environ.get("LIORG_SESSION_JWT_SECRET", "dev-librebase-admin-secret"),
    )

    db = LiorgDb(db_path)
    LiorgHandler.db = db
    LiorgHandler.jwt_secret = secret

    server = ThreadingHTTPServer((host, port), LiorgHandler)
    sys.stderr.write(f"librebase-admin listening on http://{host}:{port} db={db_path}\n")
    try:
        server.serve_forever()
    finally:
        db.close()


if __name__ == "__main__":
    main()
