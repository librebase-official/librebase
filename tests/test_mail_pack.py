"""LIB-139 Email Pack — draft → approval → send with mocked provider HTTP."""

from __future__ import annotations

import importlib.util
import json
import os
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


class TestMailPack(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = load_server()
        cls._tmp = tempfile.TemporaryDirectory()

        from kms.server import KmsHandler
        from kms.store import KmsStore

        cls.kms_db = KmsStore(Path(cls._tmp.name) / "kms.db")
        KmsHandler.db = cls.kms_db
        KmsHandler.service_role = "kms-role"
        cls.kms = ThreadingHTTPServer(("127.0.0.1", 0), KmsHandler)
        cls.kms_port = cls.kms.server_address[1]
        Thread(target=cls.kms.serve_forever, daemon=True).start()

        cls.db = cls.mod.LiorgDb(Path(cls._tmp.name) / "org.db")
        cls.mod.LiorgHandler.db = cls.db
        cls.mod.LiorgHandler.jwt_secret = "mail-pack-secret"
        os.environ["LIBREBASE_KMS_URL"] = f"http://127.0.0.1:{cls.kms_port}"
        os.environ["LIBREBASE_KMS_SERVICE_ROLE"] = "kms-role"

        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), cls.mod.LiorgHandler)
        cls.port = cls.httpd.server_address[1]
        Thread(target=cls.httpd.serve_forever, daemon=True).start()

        req = urllib.request.Request(
            f"http://127.0.0.1:{cls.port}/org/v1/setup",
            data=json.dumps(
                {"name": "MailOrg", "ownerEmail": "owner@t.c", "password": "hunter2hunter2"}
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as r:
            resp = json.loads(r.read())
            cls.org_id = resp["orgId"]
            cls.owner_token = resp["token"]
            cls.mcp_key = resp["mcpKey"]

        bot_req = cls._request(
            "POST",
            f"/org/v1/orgs/{cls.org_id}/bots",
            {"name": "Hermes", "profile": "office"},
            cls.owner_token,
        )
        cls.bot_id = bot_req[1]["id"]

    @classmethod
    def tearDownClass(cls) -> None:
        cls.mod.mail_pack.set_http_json(None)
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.kms.shutdown()
        cls.kms.server_close()
        cls.db.close()
        cls.kms_db.close()
        os.environ.pop("LIBREBASE_KMS_URL", None)
        os.environ.pop("LIBREBASE_KMS_SERVICE_ROLE", None)
        cls._tmp.cleanup()

    @classmethod
    def _request(cls, method: str, path: str, body: dict | None, token: str):
        data = None if body is None else json.dumps(body).encode()
        headers = {"Authorization": f"Bearer {token}"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(
            f"http://127.0.0.1:{cls.port}{path}",
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status, json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    def _http(self, method: str, path: str, body: dict | None = None, token: str | None = None):
        return self._request(method, path, body, token or self.owner_token)

    def test_klaut_draft_approve_send_idempotent(self) -> None:
        base = f"/org/v1/orgs/{self.org_id}/bots/{self.bot_id}/mail"
        st, draft = self._http(
            "POST",
            f"{base}/drafts",
            {
                "provider": "klaut",
                "to": ["user@example.com"],
                "subject": "Hello",
                "bodyText": "Body",
            },
        )
        self.assertEqual(st, 201, draft)
        self.assertEqual(draft["approvalState"], "pending")
        self.assertTrue(draft["contentHash"])

        st, approved = self._http(
            "POST",
            f"/org/v1/orgs/{self.org_id}/bots/{self.bot_id}/approvals/{draft['approvalId']}/approve",
            token=self.mcp_key,
        )
        self.assertEqual(st, 200, approved)

        st, sent = self._http("POST", f"{base}/send", {"draftId": draft["id"]})
        self.assertEqual(st, 200, sent)
        self.assertFalse(sent.get("idempotent"))
        self.assertTrue(sent["providerMessageId"].startswith("klaut-"))

        st, again = self._http("POST", f"{base}/send", {"draftId": draft["id"]})
        self.assertEqual(st, 200, again)
        self.assertTrue(again.get("idempotent"))
        self.assertEqual(sent["id"], again["id"])

    def test_gmail_send_mocked_http(self) -> None:
        calls: list[tuple[str, str]] = []

        def fake_http(method: str, url: str, headers: dict[str, str], body: bytes | None):
            calls.append((method, url))
            if "oauth2.googleapis.com/token" in url:
                return {"access_token": "at-mock"}
            if "gmail.googleapis.com" in url:
                return {"id": "gmail-msg-99"}
            raise AssertionError(f"unexpected url {url}")

        self.mod.mail_pack.set_http_json(fake_http)

        st, acct = self._http(
            "POST",
            f"/org/v1/orgs/{self.org_id}/mail/accounts",
            {
                "provider": "gmail_oauth",
                "fromAddress": "bot@example.com",
                "oauthTokens": {
                    "refresh_token": "rt",
                    "client_id": "cid",
                    "client_secret": "csec",
                },
            },
        )
        self.assertEqual(st, 201, acct)

        base = f"/org/v1/orgs/{self.org_id}/bots/{self.bot_id}/mail"
        st, draft = self._http(
            "POST",
            f"{base}/drafts",
            {
                "provider": "gmail_oauth",
                "accountId": acct["id"],
                "to": ["user@example.com"],
                "subject": "Gmail",
                "bodyText": "Hi",
            },
        )
        self.assertEqual(st, 201, draft)

        st, _ = self._http(
            "POST",
            f"/org/v1/orgs/{self.org_id}/bots/{self.bot_id}/approvals/{draft['approvalId']}/approve",
            token=self.mcp_key,
        )
        self.assertEqual(st, 200)

        st, sent = self._http("POST", f"{base}/send", {"draftId": draft["id"]})
        self.assertEqual(st, 200, sent)
        self.assertEqual(sent["providerMessageId"], "gmail-msg-99")
        gmail_calls = [u for _, u in calls if "gmail.googleapis.com" in u]
        self.assertEqual(len(gmail_calls), 1)

        self.mod.mail_pack.set_http_json(None)

    def test_patch_invalidates_approved_draft(self) -> None:
        base = f"/org/v1/orgs/{self.org_id}/bots/{self.bot_id}/mail"
        st, draft = self._http(
            "POST",
            f"{base}/drafts",
            {
                "provider": "klaut",
                "to": ["a@b.c"],
                "subject": "S",
                "bodyText": "One",
            },
        )
        self.assertEqual(st, 201)
        self._http(
            "POST",
            f"/org/v1/orgs/{self.org_id}/bots/{self.bot_id}/approvals/{draft['approvalId']}/approve",
            token=self.mcp_key,
        )
        st, patched = self._http(
            "PATCH",
            f"{base}/drafts/{draft['id']}",
            {"bodyText": "Two"},
        )
        self.assertEqual(st, 200, patched)
        self.assertEqual(patched["approvalState"], "pending")

        st, blocked = self._http("POST", f"{base}/send", {"draftId": draft["id"]})
        self.assertEqual(st, 403, blocked)

    def test_msgraph_stub_http_hook(self) -> None:
        def fake_http(method: str, url: str, headers: dict[str, str], body: bytes | None):
            if "graph.microsoft.com" in url:
                return {"id": "ms-1"}
            raise AssertionError(url)

        self.mod.mail_pack.set_http_json(fake_http)
        st, acct = self._http(
            "POST",
            f"/org/v1/orgs/{self.org_id}/mail/accounts",
            {
                "provider": "msgraph",
                "oauthTokens": {"access_token": "graph-token"},
            },
        )
        self.assertEqual(st, 201)
        base = f"/org/v1/orgs/{self.org_id}/bots/{self.bot_id}/mail"
        st, draft = self._http(
            "POST",
            f"{base}/drafts",
            {
                "provider": "msgraph",
                "accountId": acct["id"],
                "to": ["x@y.z"],
                "subject": "MS",
                "bodyText": "graph",
            },
        )
        self.assertEqual(st, 201)
        self._http(
            "POST",
            f"/org/v1/orgs/{self.org_id}/bots/{self.bot_id}/approvals/{draft['approvalId']}/approve",
            token=self.mcp_key,
        )
        st, sent = self._http("POST", f"{base}/send", {"draftId": draft["id"]})
        self.assertEqual(st, 200, sent)
        self.mod.mail_pack.set_http_json(None)

    def test_owner_cannot_approve_own_mail_draft(self) -> None:
        base = f"/org/v1/orgs/{self.org_id}/bots/{self.bot_id}/mail"
        st, draft = self._http(
            "POST",
            f"{base}/drafts",
            {
                "provider": "klaut",
                "to": ["z@z.z"],
                "subject": "Self",
                "bodyText": "x",
            },
        )
        self.assertEqual(st, 201)
        st, body = self._http(
            "POST",
            f"/org/v1/orgs/{self.org_id}/bots/{self.bot_id}/approvals/{draft['approvalId']}/approve",
        )
        self.assertEqual(st, 403)
        self.assertIn("own", body.get("error", "").lower())


if __name__ == "__main__":
    unittest.main()
