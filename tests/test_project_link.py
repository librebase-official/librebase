"""Backend tests for linking an existing project to a database (PATCH project)."""

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
    spec = importlib.util.spec_from_file_location("admin_server_link", SCRIPTS / "admin_server.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestProjectLink(unittest.TestCase):
    def _boot(self):
        mod = load_server()
        tmp = tempfile.TemporaryDirectory()
        db = mod.LiorgDb(Path(tmp.name) / "link.db")
        now = mod.utc_now()
        org_id = "org_link"
        db.execute(
            "INSERT INTO organizations (id, name, slug, edition, created_at, plan) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (org_id, "Link Co", "link", "cloud-paid", now, "pro"),
        )
        db.execute(
            "INSERT INTO users (id, email, password_hash, created_at, email_verified) "
            "VALUES (?, ?, ?, ?, 1)",
            ("u_owner", "owner@link.c", mod.hash_password("pw"), now),
        )
        db.execute(
            "INSERT INTO members (org_id, user_id, role, created_at) VALUES (?, ?, ?, ?)",
            (org_id, "u_owner", "owner", now),
        )
        old_db = mod.LiorgHandler.__dict__.get("db")
        old_jwt = mod.LiorgHandler.__dict__.get("jwt_secret")
        mod.LiorgHandler.db = db
        mod.LiorgHandler.jwt_secret = "link-jwt"
        server = ThreadingHTTPServer(("127.0.0.1", 0), mod.LiorgHandler)
        base = "http://127.0.0.1:%d" % server.server_port
        threading.Thread(target=server.serve_forever, daemon=True).start()
        token = mod.issue_session(db, "link-jwt", "u_owner", org_id, "owner", "cloud-paid")[0]
        return mod, tmp, db, server, base, token, old_db, old_jwt, org_id

    def _req(self, method, base, path, body=None, token=None):
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

    def test_link_project_to_instance(self) -> None:
        mod, tmp, db, server, base, token, old_db, old_jwt, org_id = self._boot()
        try:
            st, inst1 = self._req("POST", base, "/org/v1/orgs/%s/instances" % org_id,
                                  {"name": "db-1", "runtimeTarget": "local",
                                   "ports": {"api": 54320, "postgres": 54322}}, token=token)
            self.assertEqual(st, 201)
            st, inst2 = self._req("POST", base, "/org/v1/orgs/%s/instances" % org_id,
                                  {"name": "db-2", "runtimeTarget": "local",
                                   "ports": {"api": 54330, "postgres": 54332}}, token=token)
            self.assertEqual(st, 201)
            st, proj = self._req("POST", base, "/org/v1/orgs/%s/projects" % org_id,
                                 {"name": "app", "instanceId": inst1["id"],
                                  "deploymentMode": "dedicated", "region": "local"}, token=token)
            self.assertEqual(st, 201)
            self.assertEqual(proj["instanceId"], inst1["id"])

            st, linked = self._req("PATCH", base, "/org/v1/orgs/%s/projects/%s" % (org_id, proj["id"]),
                                   {"instanceId": inst2["id"]}, token=token)
            self.assertEqual(st, 200)
            self.assertEqual(linked["instanceId"], inst2["id"])
            self.assertEqual(linked["deploymentMode"], "shared")

            st, missing = self._req("PATCH", base, "/org/v1/orgs/%s/projects/%s" % (org_id, proj["id"]),
                                    {"instanceId": "inst_does_not_exist"}, token=token)
            self.assertEqual(st, 404)

            st, nobody = self._req("PATCH", base, "/org/v1/orgs/%s/projects/%s" % (org_id, proj["id"]),
                                   {}, token=token)
            self.assertEqual(st, 400)
        finally:
            server.shutdown()
            server.server_close()
            mod.LiorgHandler.db = old_db
            mod.LiorgHandler.jwt_secret = old_jwt
            db.close()
            tmp.cleanup()

    def test_delete_project(self) -> None:
        mod, tmp, db, server, base, token, old_db, old_jwt, org_id = self._boot()
        try:
            st, inst = self._req("POST", base, "/org/v1/orgs/%s/instances" % org_id,
                                 {"name": "db", "runtimeTarget": "local",
                                  "ports": {"api": 54320, "postgres": 54322}}, token=token)
            self.assertEqual(st, 201)
            st, proj = self._req("POST", base, "/org/v1/orgs/%s/projects" % org_id,
                                 {"name": "app", "instanceId": inst["id"],
                                  "deploymentMode": "dedicated", "region": "local"}, token=token)
            self.assertEqual(st, 201)

            st, deld = self._req("DELETE", base, "/org/v1/orgs/%s/projects/%s" % (org_id, proj["id"]),
                                 token=token)
            self.assertEqual(st, 200)
            self.assertTrue(deld.get("ok"))
            gone = db.fetchone("SELECT * FROM projects WHERE id = ?", (proj["id"],))
            self.assertIsNone(gone)

            # deleting a non-existent project -> 404
            st, _ = self._req("DELETE", base, "/org/v1/orgs/%s/projects/nope" % org_id, token=token)
            self.assertEqual(st, 404)
        finally:
            server.shutdown()
            server.server_close()
            mod.LiorgHandler.db = old_db
            mod.LiorgHandler.jwt_secret = old_jwt
            db.close()
            tmp.cleanup()

    def test_delete_instance_unlinks_projects(self) -> None:
        mod, tmp, db, server, base, token, old_db, old_jwt, org_id = self._boot()
        try:
            # instance A + B
            st, inst_a = self._req("POST", base, "/org/v1/orgs/%s/instances" % org_id,
                                   {"name": "db-a", "runtimeTarget": "local",
                                    "ports": {"api": 54320, "postgres": 54322}}, token=token)
            self.assertEqual(st, 201)
            st, inst_b = self._req("POST", base, "/org/v1/orgs/%s/instances" % org_id,
                                   {"name": "db-b", "runtimeTarget": "local",
                                    "ports": {"api": 54330, "postgres": 54332}}, token=token)
            self.assertEqual(st, 201)
            # dedicated project on A
            st, proj_a = self._req("POST", base, "/org/v1/orgs/%s/projects" % org_id,
                                   {"name": "app-a", "instanceId": inst_a["id"],
                                    "deploymentMode": "dedicated", "region": "local"}, token=token)
            self.assertEqual(st, 201)
            # shared project pointing at A
            st, proj_b = self._req("POST", base, "/org/v1/orgs/%s/projects" % org_id,
                                   {"name": "app-b", "instanceId": inst_a["id"],
                                    "deploymentMode": "shared", "region": "local"}, token=token)
            self.assertEqual(st, 201)

            st, deld = self._req("DELETE", base, "/org/v1/orgs/%s/instances/%s" % (org_id, inst_a["id"]),
                                 token=token)
            self.assertEqual(st, 200)
            self.assertTrue(deld.get("ok"))
            gone = db.fetchone("SELECT * FROM instances WHERE id = ?", (inst_a["id"],))
            self.assertIsNone(gone)

            # both projects linked to A are deleted too (no dangling refs)
            self.assertIsNone(db.fetchone("SELECT * FROM projects WHERE id = ?", (proj_a["id"],)))
            self.assertIsNone(db.fetchone("SELECT * FROM projects WHERE id = ?", (proj_b["id"],)))

            # instance B remains (not deleted)
            kept = db.fetchone("SELECT * FROM instances WHERE id = ?", (inst_b["id"],))
            self.assertIsNotNone(kept)

            # deleting a non-existent instance -> 404
            st, _ = self._req("DELETE", base, "/org/v1/orgs/%s/instances/nope" % org_id, token=token)
            self.assertEqual(st, 404)
        finally:
            server.shutdown()
            server.server_close()
            mod.LiorgHandler.db = old_db
            mod.LiorgHandler.jwt_secret = old_jwt
            db.close()
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
