#!/usr/bin/env python3
"""Standalone Librebase SaaS admin dashboard API.

Separate from the core admin-api. Reads the same SQLite database
(synced from the VPS) and proxies VM operations to the core admin-api.

Env:
  ADMIN_PORT                  (default 54341)
  ADMIN_BIND                  (default 0.0.0.0)
  ADMIN_DB_PATH               (path to admin.db, synced from VPS)
  ADMIN_DASHBOARD_TOKEN       (required — bearer token for all /admin/v1/* routes)
  LIBREBASE_HETZNER_API_TOKEN (for direct Hetzner cost queries + VM operations)
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Any

PORT = int(os.environ.get("ADMIN_PORT", "54341"))
BIND = os.environ.get("ADMIN_BIND", "0.0.0.0")
DB_PATH = os.environ.get("ADMIN_DB_PATH", "/data/admin.db")
DASHBOARD_TOKEN = os.environ.get("ADMIN_DASHBOARD_TOKEN", "")
HETZNER_TOKEN = os.environ.get("LIBREBASE_HETZNER_API_TOKEN", "")


def get_db() -> sqlite3.Connection:
    """Open a read-only connection to the admin database."""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _db_write(sql: str, params: tuple = ()) -> None:
    """Execute a write statement against the admin database."""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(sql, params)
        conn.commit()
    finally:
        conn.close()


def _hcloud_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {HETZNER_TOKEN}",
        "Content-Type": "application/json",
    }





class AdminHandler(BaseHTTPRequestHandler):
    """Serves the /admin/v1/* dashboard API."""

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write(f"[admin-dash] {self.address_string()} {fmt % args}\n")

    # ── Auth ──────────────────────────────────────────────────────────
    def require_admin_token(self) -> bool:
        # SECURITY: Read from env at request time, not from the module-level
        # DASHBOARD_TOKEN captured at import.  This allows env-var updates to
        # take effect without a restart and makes the test setup reliable.
        token = os.environ.get("ADMIN_DASHBOARD_TOKEN", "").strip()
        if not token:
            self._json(503, {"error": "admin dashboard not configured"})
            return False
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or auth[7:].strip() != token:
            self._json(401, {"error": "invalid admin token"})
            return False
        return True

    # ── Helpers ───────────────────────────────────────────────────────
    def _json(self, status: int, data: Any) -> None:
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw) if raw else {}

    # ── GET ───────────────────────────────────────────────────────────
    def do_GET(self) -> None:  # noqa: N802
        path = self.path.rstrip("/") or "/"
        if path == "/health":
            self._json(200, {"ok": True})
            return
        if not path.startswith("/admin/v1/"):
            self._json(404, {"error": "not found"})
            return
        if not self.require_admin_token():
            return

        db = get_db()
        try:
            self._handle_get(path, db)
        finally:
            db.close()

    def _handle_get(self, path: str, db: sqlite3.Connection) -> None:
        if path == "/admin/v1/overview":
            org_count = db.execute("SELECT COUNT(*) AS n FROM organizations").fetchone()["n"]
            user_count = db.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
            instance_count = db.execute("SELECT COUNT(*) AS n FROM instances").fetchone()["n"]
            host_count = db.execute("SELECT COUNT(*) AS n FROM hosts").fetchone()["n"]
            project_count = db.execute("SELECT COUNT(*) AS n FROM projects").fetchone()["n"]
            plan_dist = db.execute(
                "SELECT plan, COUNT(*) AS n FROM organizations GROUP BY plan"
            ).fetchall()
            instance_by_state = db.execute(
                "SELECT status, COUNT(*) AS n FROM instances GROUP BY status"
            ).fetchall()
            host_by_state = db.execute(
                "SELECT status, COUNT(*) AS n FROM hosts GROUP BY status"
            ).fetchall()
            self._json(200, {
                "orgCount": org_count,
                "userCount": user_count,
                "instanceCount": instance_count,
                "hostCount": host_count,
                "projectCount": project_count,
                "planDistribution": {r["plan"]: r["n"] for r in plan_dist},
                "instanceByState": {r["status"]: r["n"] for r in instance_by_state},
                "hostByState": {r["status"]: r["n"] for r in host_by_state},
            })
            return

        if path == "/admin/v1/orgs":
            rows = db.execute(
                "SELECT o.id, o.name, o.slug, o.edition, o.plan, o.stripe_status, o.created_at, "
                "(SELECT COUNT(*) FROM members WHERE org_id = o.id) AS member_count, "
                "(SELECT COUNT(*) FROM instances WHERE org_id = o.id) AS instance_count, "
                "(SELECT COUNT(*) FROM projects WHERE org_id = o.id) AS project_count "
                "FROM organizations o ORDER BY o.created_at"
            ).fetchall()
            self._json(200, [dict(r) for r in rows])
            return

        if path == "/admin/v1/users":
            rows = db.execute(
                "SELECT u.id, u.email, u.mfa_enabled, u.created_at, "
                "(SELECT GROUP_CONCAT(o.name) FROM members m JOIN organizations o ON o.id = m.org_id "
                "WHERE m.user_id = u.id) AS org_names "
                "FROM users u ORDER BY u.created_at"
            ).fetchall()
            self._json(200, [dict(r) for r in rows])
            return

        if path == "/admin/v1/instances":
            rows = db.execute(
                "SELECT i.id, i.name, i.status, i.host_id, i.org_id, i.mem_limit_mb, i.created_at, "
                "o.name AS org_name, h.name AS host_name, h.ip AS host_ip "
                "FROM instances i "
                "LEFT JOIN organizations o ON o.id = i.org_id "
                "LEFT JOIN hosts h ON h.id = i.host_id "
                "ORDER BY i.created_at"
            ).fetchall()
            self._json(200, [dict(r) for r in rows])
            return

        if path == "/admin/v1/hosts":
            rows = db.execute(
                "SELECT h.id, h.name, h.provider, h.server_id, h.ip, h.status, "
                "h.region, h.mem_mb, h.org_id, h.created_at, "
                "o.name AS org_name, "
                "(SELECT COUNT(*) FROM instances WHERE host_id = h.id) AS instance_count "
                "FROM hosts h LEFT JOIN organizations o ON o.id = h.org_id ORDER BY h.created_at"
            ).fetchall()
            # Enrich with live Hetzner status
            out = []
            for r in rows:
                d = dict(r)
                if HETZNER_TOKEN and d.get("server_id"):
                    try:
                        srv_resp = urllib.request.urlopen(
                            urllib.request.Request(
                                f"https://api.hetzner.cloud/v1/servers/{d['server_id']}",
                                headers=_hcloud_headers(),
                            ),
                            timeout=10,
                        )
                        srv = json.loads(srv_resp.read()).get("server", {})
                        d["status"] = srv.get("status", d.get("status", ""))
                    except Exception:  # noqa: BLE001
                        pass
                out.append(d)
            self._json(200, out)
            return

        if path == "/admin/v1/hetzner/costs":
            if not HETZNER_TOKEN:
                self._json(200, {"servers": [], "pricing": {}, "totalMonthly": 0})
                return
            try:
                hdr = _hcloud_headers()
                srv_resp = urllib.request.urlopen(
                    urllib.request.Request("https://api.hetzner.cloud/v1/servers", headers=hdr),
                    timeout=15,
                )
                servers = json.loads(srv_resp.read()).get("servers", [])
                price_resp = urllib.request.urlopen(
                    urllib.request.Request("https://api.hetzner.cloud/v1/pricing", headers=hdr),
                    timeout=15,
                )
                pricing = json.loads(price_resp.read()).get("pricing", {})
            except Exception as exc:  # noqa: BLE001
                self._json(502, {"error": str(exc)})
                return
            type_prices = {}
            for st in pricing.get("server_types", []):
                for tp in st.get("prices", []):
                    if tp.get("location") == "fsn1":
                        type_prices[st["name"]] = float(tp["price_monthly"]["gross"])
            total = 0.0
            out = []
            for s in servers:
                stype = s.get("server_type", {}).get("name", "")
                monthly = type_prices.get(stype, 0.0)
                total += monthly
                out.append({
                    "id": s["id"],
                    "name": s["name"],
                    "status": s["status"],
                    "serverType": stype,
                    "ip": s.get("public_net", {}).get("ipv4", {}).get("ip", ""),
                    "region": s.get("datacenter", {}).get("location", {}).get("name", ""),
                    "monthlyCost": monthly,
                    "createdAt": s.get("created", ""),
                })
            self._json(200, {"servers": out, "pricing": type_prices, "totalMonthly": round(total, 2)})
            return

        if path == "/admin/v1/mcp/usage":
            try:
                total = db.execute("SELECT COUNT(*) AS n FROM mcp_usage_log").fetchone()["n"]
            except Exception:
                self._json(200, {"totalCalls": 0, "callsToday": 0, "byOrg": [], "byTool": [], "hourly": []})
                return
            today = db.execute(
                "SELECT COUNT(*) AS n FROM mcp_usage_log WHERE created_at >= date('now')"
            ).fetchone()["n"]
            by_org = db.execute(
                "SELECT org_id, COUNT(*) as cnt, MAX(created_at) as last_call "
                "FROM mcp_usage_log GROUP BY org_id ORDER BY cnt DESC LIMIT 50"
            ).fetchall()
            by_tool = db.execute(
                "SELECT tool_name, COUNT(*) as cnt, AVG(latency_ms) as avg_ms, "
                "SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors "
                "FROM mcp_usage_log GROUP BY tool_name ORDER BY cnt DESC"
            ).fetchall()
            hourly = db.execute(
                "SELECT strftime('%Y-%m-%dT%H:00:00Z', created_at) as hour, COUNT(*) as cnt "
                "FROM mcp_usage_log WHERE created_at >= datetime('now', '-24 hours') "
                "GROUP BY hour ORDER BY hour"
            ).fetchall()
            self._json(200, {
                "totalCalls": total,
                "callsToday": today,
                "byOrg": [dict(r) for r in by_org],
                "byTool": [dict(r) for r in by_tool],
                "hourly": [dict(r) for r in hourly],
            })
            return

        self._json(404, {"error": "not found"})

    # ── POST (direct Hetzner + local DB update) ──────────────────────
    def do_POST(self) -> None:  # noqa: N802
        path = self.path.rstrip("/") or "/"
        if not path.startswith("/admin/v1/"):
            self._json(404, {"error": "not found"})
            return
        if not self.require_admin_token():
            return

        stop_match = re.fullmatch(r"/admin/v1/hosts/([^/]+)/stop", path)
        if stop_match:
            host_id = stop_match.group(1)
            db = get_db()
            try:
                row = db.execute("SELECT * FROM hosts WHERE id = ?", (host_id,)).fetchone()
            finally:
                db.close()
            if not row:
                self._json(404, {"error": "host not found"})
                return
            if HETZNER_TOKEN and row.get("server_id"):
                try:
                    req = urllib.request.Request(
                        f"https://api.hetzner.cloud/v1/servers/{row['server_id']}/actions/poweroff",
                        method="POST", headers=_hcloud_headers(),
                    )
                    urllib.request.urlopen(req, timeout=30)
                except Exception as exc:  # noqa: BLE001
                    self._json(502, {"error": str(exc)})
                    return
            _db_write("UPDATE hosts SET status = 'stopped' WHERE id = ?", (host_id,))
            self._json(200, {"ok": True, "status": "stopped"})
            return

        start_match = re.fullmatch(r"/admin/v1/hosts/([^/]+)/start", path)
        if start_match:
            host_id = start_match.group(1)
            db = get_db()
            try:
                row = db.execute("SELECT * FROM hosts WHERE id = ?", (host_id,)).fetchone()
            finally:
                db.close()
            if not row:
                self._json(404, {"error": "host not found"})
                return
            if HETZNER_TOKEN and row.get("server_id"):
                try:
                    req = urllib.request.Request(
                        f"https://api.hetzner.cloud/v1/servers/{row['server_id']}/actions/poweron",
                        method="POST", headers=_hcloud_headers(),
                    )
                    urllib.request.urlopen(req, timeout=30)
                except Exception as exc:  # noqa: BLE001
                    self._json(502, {"error": str(exc)})
                    return
            _db_write("UPDATE hosts SET status = 'running' WHERE id = ?", (host_id,))
            self._json(200, {"ok": True, "status": "running"})
            return

        self._json(404, {"error": "not found"})

    # ── DELETE (direct Hetzner + local DB delete) ─────────────────────
    def do_DELETE(self) -> None:  # noqa: N802
        path = self.path.rstrip("/") or "/"
        if not path.startswith("/admin/v1/"):
            self._json(404, {"error": "not found"})
            return
        if not self.require_admin_token():
            return

        host_del = re.fullmatch(r"/admin/v1/hosts/([^/]+)", path)
        if host_del:
            host_id = host_del.group(1)
            db = get_db()
            try:
                row = db.execute("SELECT * FROM hosts WHERE id = ?", (host_id,)).fetchone()
            finally:
                db.close()
            if not row:
                self._json(404, {"error": "host not found"})
                return
            server_id = row["server_id"] if "server_id" in row.keys() else None
            if server_id and HETZNER_TOKEN:
                try:
                    req = urllib.request.Request(
                        f"https://api.hetzner.cloud/v1/servers/{server_id}",
                        method="DELETE", headers=_hcloud_headers(),
                    )
                    urllib.request.urlopen(req, timeout=30)
                except Exception as exc:  # noqa: BLE001
                    self._json(502, {"error": str(exc)})
                    return
            _db_write("DELETE FROM hosts WHERE id = ?", (host_id,))
            self._json(200, {"ok": True})
            return

        self._json(404, {"error": "not found"})


def main() -> None:
    if not DASHBOARD_TOKEN:
        print("WARNING: ADMIN_DASHBOARD_TOKEN not set — dashboard is disabled", file=sys.stderr)
    if not DB_PATH or not os.path.exists(DB_PATH):
        print(f"WARNING: admin.db not found at {DB_PATH}", file=sys.stderr)

    server = HTTPServer((BIND, PORT), AdminHandler)
    print(f"saas-admin-api listening on {BIND}:{PORT} (db={DB_PATH})", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.", flush=True)
        server.server_close()


if __name__ == "__main__":
    main()
