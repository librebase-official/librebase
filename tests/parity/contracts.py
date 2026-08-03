"""Wave A Supabase-parity contracts (HTTP/SQL).

Run via: python scripts/parity_runner.py
Without LIDB_ROOT+lis: runner skips (exit 0) — do not treat as production green.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Result:
    id: str
    status: str  # pass | fail | skip
    detail: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)


def _api_base() -> str:
    return os.environ.get("LIBREBASE_PARITY_API", "http://127.0.0.1:54321").rstrip("/")


def _http(
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 5.0,
) -> tuple[int, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    hdrs = {"Content-Type": "application/json", **(headers or {})}
    req = urllib.request.Request(_api_base() + path, data=data, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                return resp.status, {"raw": raw}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8")
        try:
            return e.code, json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return e.code, {"raw": raw}
    except Exception as e:  # noqa: BLE001
        return 0, {"error": str(e)}


def p_auth_01() -> Result:
    """Signup + login → JWT; Bearer whoami/session accepted."""
    email = os.environ.get("PARITY_EMAIL", "parity-user@example.com")
    password = os.environ.get("PARITY_PASSWORD", "parity-secret-change-me")
    status, body = _http("POST", "/v1/auth/signup", body={"email": email, "password": password})
    if status not in (200, 201, 409):
        return Result("P-AUTH-01", "fail", f"signup status={status}", {"body": body})
    status, body = _http("POST", "/v1/auth/login", body={"email": email, "password": password})
    token = None
    if isinstance(body, dict):
        token = body.get("access_token") or body.get("token") or (body.get("session") or {}).get("access_token")
    if status != 200 or not token:
        return Result("P-AUTH-01", "fail", f"login status={status}", {"body": body})
    status2, body2 = _http("GET", "/v1/auth/whoami", headers={"Authorization": f"Bearer {token}"})
    if status2 != 200:
        return Result("P-AUTH-01", "fail", f"whoami status={status2}", {"body": body2})
    return Result("P-AUTH-01", "pass", "signup/login/whoami OK", {"token_prefix": str(token)[:12]})


def p_auth_02() -> Result:
    """GoTrue-shaped /auth/v1 alias: signup + password token + user."""
    email = os.environ.get("PARITY_EMAIL_GOTRUE", "parity-gotrue@example.com")
    password = os.environ.get("PARITY_PASSWORD", "parity-secret-change-me")
    status, body = _http("POST", "/auth/v1/signup", body={"email": email, "password": password})
    if status not in (200, 201, 409):
        return Result("P-AUTH-02", "fail", f"/auth/v1/signup status={status}", {"body": body})
    status, body = _http(
        "POST",
        "/auth/v1/token?grant_type=password",
        body={"email": email, "password": password},
    )
    token = None
    if isinstance(body, dict):
        token = body.get("access_token") or body.get("token")
    if status != 200 or not token:
        return Result("P-AUTH-02", "fail", f"/auth/v1/token status={status}", {"body": body})
    status2, body2 = _http("GET", "/auth/v1/user", headers={"Authorization": f"Bearer {token}"})
    if status2 != 200:
        return Result("P-AUTH-02", "fail", f"/auth/v1/user status={status2}", {"body": body2})
    return Result("P-AUTH-02", "pass", "GoTrue alias signup/token/user OK", {"token_prefix": str(token)[:12]})


def p_rest_01() -> Result:
    """CRUD on /rest/v1/{table} with basic filter."""
    table = os.environ.get("PARITY_REST_TABLE", "parity_items")
    email = os.environ.get("PARITY_EMAIL", "parity-rest@example.com")
    password = os.environ.get("PARITY_PASSWORD", "parity-secret-change-me")
    _http("POST", "/v1/auth/signup", body={"email": email, "password": password})
    status_l, login = _http("POST", "/v1/auth/login", body={"email": email, "password": password})
    token = None
    if isinstance(login, dict):
        token = login.get("access_token") or login.get("token")
    if status_l != 200 or not token:
        return Result("P-REST-01", "fail", "need auth for RLS-backed rest", {"login": login})
    hdrs = {"Authorization": f"Bearer {token}"}
    status, body = _http(
        "POST",
        f"/rest/v1/{table}",
        body={"name": "wave-a"},
        headers=hdrs,
    )
    if status in (0,):
        return Result("P-REST-01", "fail", "API unreachable", {"body": body})
    if status in (404, 501, 405):
        return Result("P-REST-01", "fail", f"/rest/v1 not implemented (status={status})", {"body": body})
    if status not in (200, 201):
        return Result("P-REST-01", "fail", f"POST status={status}", {"body": body})
    status_g, body_g = _http("GET", f"/rest/v1/{table}?name=eq.wave-a", headers=hdrs)
    if status_g != 200:
        return Result("P-REST-01", "fail", f"GET status={status_g}", {"body": body_g})
    if isinstance(body_g, list) and len(body_g) < 1:
        return Result("P-REST-01", "fail", "GET returned no rows after POST", {"body": body_g})
    return Result("P-REST-01", "pass", "POST+GET OK", {"get": body_g})


def p_sql_01() -> Result:
    """Ensure table + DML — via REST health of fixture or SQL endpoint if present."""
    # Prefer dedicated SQL health when exposed; else infer from rest ensure.
    status, body = _http("GET", "/rest/v1/parity_items?limit=1")
    if status == 200:
        return Result("P-SQL-01", "pass", "fixture table readable via rest", {"body": body})
    if status in (404, 501):
        return Result(
            "P-SQL-01",
            "fail",
            "parity_items not available — need lidb migration ensure + rest",
            {"body": body},
        )
    if status == 0:
        return Result("P-SQL-01", "fail", "API unreachable", {"body": body})
    return Result("P-SQL-01", "fail", f"unexpected status={status}", {"body": body})


def p_rls_01() -> Result:
    """Cross-user row denied without matching JWT claim."""
    email_a = "parity-a@example.com"
    email_b = "parity-b@example.com"
    password = "parity-secret-change-me"
    for email in (email_a, email_b):
        _http("POST", "/v1/auth/signup", body={"email": email, "password": password})
    _, login_a = _http("POST", "/v1/auth/login", body={"email": email_a, "password": password})
    _, login_b = _http("POST", "/v1/auth/login", body={"email": email_b, "password": password})
    tok_a = (login_a or {}).get("access_token") or (login_a or {}).get("token")
    tok_b = (login_b or {}).get("access_token") or (login_b or {}).get("token")
    if not tok_a or not tok_b:
        return Result("P-RLS-01", "fail", "could not obtain two JWTs", {"a": login_a, "b": login_b})
    status, body = _http(
        "POST",
        "/rest/v1/parity_items",
        body={"name": "owned-by-a", "secret": "nope"},
        headers={"Authorization": f"Bearer {tok_a}"},
    )
    if status in (404, 501):
        return Result("P-RLS-01", "fail", "REST/RLS not wired", {"body": body})
    status_g, rows = _http(
        "GET",
        "/rest/v1/parity_items?name=eq.owned-by-a",
        headers={"Authorization": f"Bearer {tok_b}"},
    )
    if status_g != 200:
        return Result("P-RLS-01", "fail", f"GET as B status={status_g}", {"body": rows})
    if isinstance(rows, list) and len(rows) == 0:
        return Result("P-RLS-01", "pass", "B cannot see A's row")
    if isinstance(rows, dict) and not rows.get("data"):
        return Result("P-RLS-01", "pass", "B cannot see A's row", {"body": rows})
    return Result("P-RLS-01", "fail", "B saw A's row — RLS not enforced", {"body": rows})


def _find_embed() -> Path | None:
    raw = os.environ.get("LIDB_EMBED", "").strip()
    if raw and Path(raw).is_file():
        return Path(raw)
    root = os.environ.get("LIDB_ROOT", "").strip()
    if not root:
        return None
    for cand in (
        Path(root) / "build" / "lidb_embed.exe",
        Path(root) / "build" / "lidb_embed",
        Path(root) / "build" / "smoke" / "lidb_embed.exe",
        Path(root) / "build" / "smoke" / "lidb_embed",
    ):
        if cand.is_file():
            return cand
    return None


def p_io_01() -> Result:
    """Export → import SQL round-trip via lidb_embed (required)."""
    import shutil
    import subprocess
    import tempfile

    embed = _find_embed()
    if embed is None:
        return Result("P-IO-01", "fail", "LIDB_EMBED or LIDB_ROOT/build/lidb_embed required")
    tmp = Path(tempfile.mkdtemp(prefix="parity-io-"))
    data_a = tmp / "a"
    data_b = tmp / "b"
    dump = tmp / "parity.sql"
    data_a.mkdir()
    data_b.mkdir()
    try:
        mig_a = subprocess.run(
            [str(embed), "migrate", str(data_a)], capture_output=True, text=True, check=False
        )
        if mig_a.returncode != 0:
            return Result("P-IO-01", "fail", "migrate A failed", {"stderr": mig_a.stderr})
        ins = subprocess.run(
            [
                str(embed),
                "exec-json",
                str(data_a),
                "INSERT INTO parity_items (id, name, owner_id, secret) VALUES (?, ?, ?, ?)",
            ],
            input=json.dumps(
                [
                    "00000000-0000-4000-8000-00000000io01",
                    "parity-io",
                    "00000000-0000-4000-8000-00000000ownr",
                    "x",
                ]
            ),
            capture_output=True,
            text=True,
            check=False,
        )
        if ins.returncode != 0:
            return Result("P-IO-01", "fail", "insert failed", {"stderr": ins.stderr})
        exp = subprocess.run(
            [str(embed), "export", str(data_a), "parity_items", "sql", "-o", str(dump)],
            capture_output=True,
            text=True,
            check=False,
        )
        if exp.returncode != 0 or not dump.is_file() or "INSERT INTO parity_items" not in dump.read_text(
            encoding="utf-8"
        ):
            return Result("P-IO-01", "fail", "export failed", {"stderr": exp.stderr})
        mig_b = subprocess.run(
            [str(embed), "migrate", str(data_b)], capture_output=True, text=True, check=False
        )
        if mig_b.returncode != 0:
            return Result("P-IO-01", "fail", "migrate B failed", {"stderr": mig_b.stderr})
        imp = subprocess.run(
            [str(embed), "import", str(data_b), "sql", "-i", str(dump)],
            capture_output=True,
            text=True,
            check=False,
        )
        if imp.returncode != 0:
            return Result("P-IO-01", "fail", "import failed", {"stderr": imp.stderr})
        sel = subprocess.run(
            [str(embed), "exec-json", str(data_b), "SELECT name FROM parity_items WHERE name = ?"],
            input=json.dumps(["parity-io"]),
            capture_output=True,
            text=True,
            check=False,
        )
        if sel.returncode != 0:
            return Result("P-IO-01", "fail", "select after import failed", {"stderr": sel.stderr})
        payload = json.loads(sel.stdout or "{}")
        rows = payload.get("rows") or []
        if not rows or rows[0].get("name") != "parity-io":
            return Result("P-IO-01", "fail", "round-trip mismatch", {"payload": payload})
        bad = subprocess.run(
            [str(embed), "export", str(data_a), "not_allowlisted", "sql"],
            capture_output=True,
            text=True,
            check=False,
        )
        if bad.returncode == 0:
            return Result("P-IO-01", "fail", "expected export of unknown table to fail")
        return Result(
            "P-IO-01",
            "pass",
            "export/import SQL round-trip OK",
            {"dump_bytes": dump.stat().st_size},
        )
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def p_rt_01() -> Result:
    """Phoenix WS join on realtime endpoint (required — no soft skip)."""
    import asyncio

    ws_url = os.environ.get(
        "LIBREBASE_PARITY_WS",
        "ws://127.0.0.1:54323/realtime/v1/websocket",
    )
    try:
        import websockets
    except ImportError:
        return Result(
            "P-RT-01",
            "fail",
            "websockets package required for P-RT-01 (pip install websockets)",
        )

    async def _probe() -> Result:
        try:
            async with websockets.connect(ws_url, open_timeout=5, close_timeout=2) as ws:
                join = {
                    "topic": "realtime:parity",
                    "event": "phx_join",
                    "payload": {
                        "config": {
                            "postgres_changes": [
                                {
                                    "event": "INSERT",
                                    "schema": "public",
                                    "table": "parity_items",
                                }
                            ]
                        }
                    },
                    "ref": "1",
                    "join_ref": "1",
                }
                await ws.send(json.dumps(join))
                raw = await asyncio.wait_for(ws.recv(), timeout=5)
                msg = json.loads(raw) if isinstance(raw, str) else {}
                if msg.get("event") != "phx_reply":
                    return Result("P-RT-01", "fail", f"expected phx_reply got {msg.get('event')}", {"msg": msg})
                status = (msg.get("payload") or {}).get("status")
                if status != "ok":
                    return Result("P-RT-01", "fail", f"join status={status}", {"msg": msg})
                return Result("P-RT-01", "pass", "phx_join ok", {"ws": ws_url})
        except Exception as exc:  # noqa: BLE001
            return Result("P-RT-01", "fail", f"ws probe failed: {exc}", {"ws": ws_url})

    return asyncio.run(_probe())


CONTRACTS = [p_sql_01, p_rest_01, p_auth_01, p_auth_02, p_rls_01, p_io_01, p_rt_01]


def run_all() -> list[Result]:
    return [fn() for fn in CONTRACTS]
