"""Backend tests for the rename-organization endpoint (PATCH /org/v1/orgs/{org})."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "admin-api" / "scripts"


def load_server():
    spec = importlib.util.spec_from_file_location("admin_server_org", SCRIPTS / "admin_server.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _boot(role="owner"):
    mod = load_server()
    tmp = tempfile.TemporaryDirectory()
    db = mod.LiorgDb(Path(tmp.name) / "org.db")
    now = mod.utc_now()
    org_id = "org_rename"
    db.execute(
        "INSERT INTO organizations (id, name, slug, edition, created_at, plan) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (org_id, "Old Name", "rename", "self-host", now, "self-host"),
    )
    db.execute(
        "INSERT INTO users (id, email, password_hash, created_at, email_verified) "
        "VALUES (?, ?, ?, ?, 1)",
        ("u_owner", "owner@x.c", mod.hash_password("pw"), now),
    )
    db.execute(
        "INSERT INTO members (org_id, user_id, role, created_at) VALUES (?, ?, ?, ?)",
        (org_id, "u_owner", role, now),
    )
    old_db = mod.LiorgHandler.__dict__.get("db")
    old_jwt = mod.LiorgHandler.__dict__.get("jwt_secret")
    mod.LiorgHandler.db = db
    mod.LiorgHandler.jwt_secret = "rename-jwt"
    server = ThreadingHTTPServer(("127.0.0.1", 0), mod.LiorgHandler)
    base = "http://127.0.0.1:%d" % server.server_port
    threading.Thread(target=server.serve_forever, daemon=True).start()
    token = mod.issue_session(db, "rename-jwt", "u_owner", org_id, role, "self-host")[0]
    return mod, tmp, db, server, base, token, old_db, old_jwt, org_id


def _req(method, base, path, body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    hdrs = {}
    if token:
        hdrs["Authorization"] = "Bearer " + token
    if data is not None:
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(base + path, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            return res.status, json.loads(res.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode() or "{}"
        try:
            parsed = json.loads(raw)
        except ValueError:
            parsed = raw
        return exc.code, parsed


class TestOrgRename(unittest.TestCase):
    def _teardown(self, ctx):
        mod, tmp, db, server, *_ = ctx
        server.shutdown()
        server.server_close()
        _ = ctx[6]
        _ = ctx[7]
        mod.LiorgHandler.db = ctx[6]
        mod.LiorgHandler.jwt_secret = ctx[7]
        db.close()
        tmp.cleanup()

    def test_owner_renames_org(self) -> None:
        ctx = _boot()
        mod, tmp, db, server, base, token, old_db, old_jwt, org_id = ctx
        try:
            st, body = _req("PATCH", base, "/org/v1/orgs/%s" % org_id,
                            {"name": "Renamed Co"}, token=token)
            self.assertEqual(st, 200)
            self.assertEqual(body["name"], "Renamed Co")
            row = db.fetchone("SELECT name FROM organizations WHERE id=?", (org_id,))
            self.assertEqual(row["name"], "Renamed Co")
        finally:
            self._teardown(ctx)

    def test_missing_name_returns_400(self) -> None:
        ctx = _boot()
        _, _, _, _, base, token, _, _, org_id = ctx
        try:
            st, body = _req("PATCH", base, "/org/v1/orgs/%s" % org_id, {"name": "  "}, token=token)
            self.assertEqual(st, 400)
        finally:
            self._teardown(ctx)

    def test_non_owner_denied(self) -> None:
        ctx = _boot(role="developer")
        _, _, _, _, base, token, _, _, org_id = ctx
        try:
            st, _ = _req("PATCH", base, "/org/v1/orgs/%s" % org_id,
                         {"name": "Hijack"}, token=token)
            self.assertEqual(st, 403)
        finally:
            self._teardown(ctx)

    def test_me_includes_org_names(self) -> None:
        ctx = _boot()
        _, _, _, _, base, token, _, _, _ = ctx
        try:
            st, body = _req("GET", base, "/org/v1/me", token=token)
            self.assertEqual(st, 200)
            self.assertEqual(body["memberships"][0]["orgId"], "org_rename")
            self.assertEqual(body["memberships"][0]["name"], "Old Name")
        finally:
            self._teardown(ctx)


if __name__ == "__main__":
    unittest.main()