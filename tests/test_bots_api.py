"""Librebase Agents — bots CRUD and approvals smoke tests."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "admin-api" / "scripts"


def load_server():
    spec = importlib.util.spec_from_file_location("admin_server", SCRIPTS / "admin_server.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestBotsApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = load_server()
        cls._tmp = tempfile.TemporaryDirectory()
        cls.db = cls.mod.LiorgDb(Path(cls._tmp.name) / "org.db")
        cls.mod.LiorgHandler.db = cls.db
        cls.mod.LiorgHandler.jwt_secret = "bots-secret"
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), cls.mod.LiorgHandler)
        cls.port = cls.httpd.server_address[1]
        Thread(target=cls.httpd.serve_forever, daemon=True).start()
        req = urllib.request.Request(
            f"http://127.0.0.1:{cls.port}/org/v1/setup",
            data=json.dumps(
                {"name": "BotsOrg", "ownerEmail": "bots@t.c", "password": "hunter2hunter2"}
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as r:
            resp = json.loads(r.read())
            cls.org_id = resp["orgId"]
            cls.token = resp["token"]

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.db.close()
        cls._tmp.cleanup()

    def _http(self, method: str, path: str, body: dict | None = None):
        data = None if body is None else json.dumps(body).encode()
        headers = {"Authorization": f"Bearer {self.token}"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            raw = e.read().decode()
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = {"error": raw}
            return e.code, parsed

    def _create_bot(self, name: str = "Mail", **extra: object) -> dict:
        payload = {"name": name, "instructions": "Triage inbox.", "profile": "office"}
        payload.update(extra)
        st, bot = self._http("POST", f"/org/v1/orgs/{self.org_id}/bots", payload)
        self.assertEqual(st, 201, bot)
        return bot

    def test_create_and_list_office_bot(self) -> None:
        bot = self._create_bot("Mail")
        self.assertEqual(bot["name"], "Mail")
        self.assertEqual(bot["profile"], "office")
        self.assertEqual(bot["harness"], "pi")
        self.assertTrue(bot["id"].startswith("bot_"))

        st, listed = self._http("GET", f"/org/v1/orgs/{self.org_id}/bots")
        self.assertEqual(st, 200)
        self.assertGreaterEqual(len(listed), 1)
        ids = {b["id"] for b in listed}
        self.assertIn(bot["id"], ids)

        st, one = self._http("GET", f"/org/v1/orgs/{self.org_id}/bots/{bot['id']}")
        self.assertEqual(st, 200)
        self.assertEqual(one["id"], bot["id"])

    def test_reject_coding_profile(self) -> None:
        st, body = self._http(
            "POST",
            f"/org/v1/orgs/{self.org_id}/bots",
            {"name": "Dev", "profile": "coding"},
        )
        self.assertEqual(st, 400)
        self.assertIn("coding", body.get("error", "").lower())

    def test_patch_and_delete_bot(self) -> None:
        bot = self._create_bot("PatchMe")
        st, updated = self._http(
            "PATCH",
            f"/org/v1/orgs/{self.org_id}/bots/{bot['id']}",
            {"name": "Renamed", "instructions": "New brief."},
        )
        self.assertEqual(st, 200)
        self.assertEqual(updated["name"], "Renamed")
        self.assertEqual(updated["instructions"], "New brief.")

        st, body = self._http("DELETE", f"/org/v1/orgs/{self.org_id}/bots/{bot['id']}")
        self.assertEqual(st, 200)
        self.assertTrue(body.get("ok"))

        st, one = self._http("GET", f"/org/v1/orgs/{self.org_id}/bots/{bot['id']}")
        self.assertEqual(st, 404)

    def test_approval_create_list_approve(self) -> None:
        bot = self._create_bot("Approver")
        base = f"/org/v1/orgs/{self.org_id}/bots/{bot['id']}/approvals"
        payload = {"to": "user@example.com", "subject": "Hello", "body": "Draft text"}
        st, created = self._http(
            "POST",
            base,
            {"toolName": "email.send", "payload": payload},
        )
        self.assertEqual(st, 201, created)
        self.assertEqual(created["toolName"], "email.send")
        self.assertEqual(created["state"], "pending")
        self.assertEqual(created["payload"], payload)
        self.assertTrue(created["id"].startswith("apr_"))
        self.assertTrue(created["payloadHash"])

        st, pending = self._http("GET", f"{base}?state=pending")
        self.assertEqual(st, 200)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["id"], created["id"])

        st, approved = self._http("POST", f"{base}/{created['id']}/approve")
        self.assertEqual(st, 200)
        self.assertEqual(approved["state"], "approved")
        self.assertIsNotNone(approved["resolvedAt"])
        self.assertTrue(approved["resolvedBy"])

        st, again = self._http("POST", f"{base}/{created['id']}/approve")
        self.assertEqual(st, 409)

    def test_approval_reject(self) -> None:
        bot = self._create_bot("RejectBot")
        base = f"/org/v1/orgs/{self.org_id}/bots/{bot['id']}/approvals"
        st, created = self._http(
            "POST",
            base,
            {"toolName": "email.send", "payload": {"subject": "x"}},
        )
        self.assertEqual(st, 201)
        st, rejected = self._http("POST", f"{base}/{created['id']}/reject")
        self.assertEqual(st, 200)
        self.assertEqual(rejected["state"], "rejected")

        st, listed = self._http("GET", f"{base}?state=rejected")
        self.assertEqual(st, 200)
        self.assertEqual(len(listed), 1)


if __name__ == "__main__":
    unittest.main()
