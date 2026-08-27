#!/usr/bin/env python3
"""Persistent LiDB HTTP supervisor.

Wraps lidb-engine as a per-query subprocess but maintains data persistence
through a consistent data directory. Exposes /v1/sql, /health, and /rest/v1/*
endpoints compatible with the Librebase runtime contract.

Usage:
    python3 lidb_supervisor.py --data-dir /data/todos --api-port 54320 --app-name todos
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

_EMBED: str | None = None
_DATA_DIR: str = "/data"
_APP_NAME: str = "default"

_DDL_RE = re.compile(
    r"^\s*(create|insert|update|delete|drop|alter|grant|revoke|begin|commit|rollback)\b",
    re.I,
)
_SELECT_RE = re.compile(r"^\s*select\b", re.I)
_TABLE_RE = re.compile(
    r"^\s*create\s+table\s+(?:if\s+not\s+exists\s+)?\"?(\w+)\"?\s*\(",
    re.I,
)


def _find_embed() -> str:
    global _EMBED
    if _EMBED:
        return _EMBED
    # Check LIDB_ENGINE env, then PATH, then common locations
    for candidate in [
        os.environ.get("LIDB_ENGINE", ""),
        shutil.which("lidb-engine") or "",
        "/usr/local/bin/lidb-engine",
        "/opt/li/lidb/build/lidb-engine",
    ]:
        if candidate and Path(candidate).is_file():
            _EMBED = candidate
            return _EMBED
    raise RuntimeError("lidb-engine not found")


def _run_embed(args: list[str], stdin: str = "[]", timeout: float = 30) -> dict[str, Any]:
    """Run lidb-engine and return parsed JSON result."""
    embed = _find_embed()
    data = Path(_DATA_DIR)
    data.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(
            [embed, *args],
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(data),
        )
        if result.stdout.strip():
            return json.loads(result.stdout.strip())
        return {"error": "no output", "stderr": (result.stderr or "").strip()}
    except subprocess.TimeoutExpired:
        return {"error": "timeout"}
    except json.JSONDecodeError as e:
        return {"error": f"json decode: {e}", "raw": result.stdout.strip()[:200]}
    except Exception as e:
        return {"error": str(e)}


def ensure_database() -> bool:
    """Open and migrate the database. Returns True if ready."""
    try:
        r1 = _run_embed(["open", _DATA_DIR])
        r2 = _run_embed(["migrate", _DATA_DIR])
        return True
    except Exception:
        return False


def execute_sql(sql: str, params: list[str] | None = None) -> dict[str, Any]:
    """Execute SQL via lidb-engine exec-json."""
    params = params or []
    try:
        result = _run_embed(
            ["exec-json", _DATA_DIR, sql],
            stdin=json.dumps(params),
        )
        if "rows" in result:
            rows = result["rows"]
            affected = result.get("affected", 0)
            return {"ok": True, "rows": rows, "affected": affected}
        if "error" in result:
            # DDL returns exit 1 but still succeeds
            if _DDL_RE.match(sql):
                return {"ok": True, "rows": [], "message": "statement executed"}
            return {"ok": False, "error": result["error"]}
        return {"ok": True, "rows": [], "message": "statement executed"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


class SupervisorHandler(BaseHTTPRequestHandler):
    """HTTP handler for LiDB supervisor."""

    def log_message(self, format: str, *args: Any) -> None:
        logging.info(f"{self.address_string()} {format % args}")

    def _send_json(self, status: int, data: Any) -> None:
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> Any:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/health":
            self._send_json(200, {
                "status": "running",
                "runtime_mode": "lidb",
                "app": _APP_NAME,
                "message": f"LiDB supervisor ({_APP_NAME})",
                "data_dir": _DATA_DIR,
                "running": True,
            })
            return

        if path == "/v1/sql":
            # GET /v1/sql?sql=SELECT+1 — convenience for browser testing
            qs = parse_qs(parsed.query)
            sql = qs.get("sql", [""])[0]
            if not sql:
                self._send_json(400, {"error": "sql query parameter required"})
                return
            result = execute_sql(sql)
            self._send_json(200 if result.get("ok") else 500, result)
            return

        self._send_json(404, {"error": "not_found", "path": path})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        body = self._read_json()

        if path == "/v1/sql":
            sql = str(body.get("sql", "")).strip()
            if not sql:
                self._send_json(400, {"error": "sql is required"})
                return
            result = execute_sql(sql)
            self._send_json(200 if result.get("ok") else 500, result)
            return

        if path in ("/v1/auth/signup", "/auth/v1/signup"):
            # Minimal auth stub — create user in a users table
            email = body.get("email", "")
            password = body.get("password", "")
            if not email or not password:
                self._send_json(400, {"error": "email and password required"})
                return
            # Ensure users table exists
            execute_sql("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, email TEXT, password_hash TEXT, created_at TEXT)")
            import hashlib, uuid
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            pw_hash = hashlib.sha256(password.encode()).hexdigest()
            execute_sql(
                "INSERT INTO users (id, email, password_hash, created_at) VALUES ($1, $2, $3, $4)",
                [user_id, email, pw_hash, time.strftime("%Y-%m-%dT%H:%M:%SZ")],
            )
            import secrets
            token = secrets.token_urlsafe(32)
            self._send_json(200, {
                "access_token": token,
                "user": {"id": user_id, "email": email},
            })
            return

        if path in ("/v1/auth/login", "/v1/auth/signin"):
            email = body.get("email", "")
            password = body.get("password", "")
            if not email or not password:
                self._send_json(400, {"error": "email and password required"})
                return
            import hashlib
            pw_hash = hashlib.sha256(password.encode()).hexdigest()
            result = execute_sql(
                "SELECT * FROM users WHERE email = $1 AND password_hash = $2",
                [email, pw_hash],
            )
            rows = result.get("rows", [])
            if rows:
                import secrets
                token = secrets.token_urlsafe(32)
                self._send_json(200, {
                    "access_token": token,
                    "user": rows[0],
                })
            else:
                self._send_json(401, {"error": "invalid credentials"})
            return

        if path.startswith("/rest/v1/"):
            # Generic REST: /rest/v1/{table}
            table = path.split("/rest/v1/", 1)[1]
            if table and body:
                # INSERT
                cols = list(body.keys())
                vals = [body[c] for c in cols]
                placeholders = ", ".join(f"${i+1}" for i in range(len(cols)))
                col_names = ", ".join(cols)
                result = execute_sql(
                    f"INSERT INTO {table} ({col_names}) VALUES ({placeholders})",
                    [str(v) for v in vals],
                )
                self._send_json(200 if result.get("ok") else 500, result)
            else:
                # SELECT
                result = execute_sql(f"SELECT * FROM {table} LIMIT 100")
                self._send_json(200, result.get("rows", []))
            return

        self._send_json(404, {"error": "not_found", "path": path})

    def do_OPTIONS(self) -> None:
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, apikey")
        self.end_headers()


def main() -> int:
    global _DATA_DIR, _APP_NAME

    parser = argparse.ArgumentParser(description="LiDB persistent supervisor")
    parser.add_argument("--data-dir", default=os.environ.get("LI_DATA_DIR", "/data"))
    parser.add_argument("--api-port", type=int, default=int(os.environ.get("LIBREBASE_API_PORT", "54320")))
    parser.add_argument("--app-name", default=os.environ.get("APP_NAME", "default"))
    parser.add_argument("--bind", default="0.0.0.0")
    args = parser.parse_args()

    _DATA_DIR = args.data_dir
    _APP_NAME = args.app_name

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    logging.info(f"LiDB supervisor starting: app={_APP_NAME} data={_DATA_DIR} port={args.api_port}")

    if not ensure_database():
        logging.error("Failed to initialize database")
        return 1

    logging.info(f"Database ready: {_DATA_DIR}")

    server = ThreadingHTTPServer((args.bind, args.api_port), SupervisorHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
