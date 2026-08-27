"""Integration test — MCP server JSON-RPC: tool list + OAuth provider setup.

Spins up a fake KMS and a live admin-api, issues an MCP key for the setup org,
and drives the stdio MCP handlers via the same in-process _handle() the
main() loop uses.
"""

from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "admin-api" / "scripts"
MCP_MODULE = ROOT / "mcp" / "librebase_mcp" / "__main__.py"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("lb_mcp", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestMcpOAuth(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server_mod = load_module(SCRIPTS / "admin_server.py")
        cls._tmp = tempfile.TemporaryDirectory()

        from kms.server import KmsHandler
        from kms.store import KmsStore

        cls.kms_db = KmsStore(Path(cls._tmp.name) / "kms.db")
        KmsHandler.db = cls.kms_db
        KmsHandler.service_role = "kms-role"
        cls.kms = ThreadingHTTPServer(("127.0.0.1", 0), KmsHandler)
        cls.kms_port = cls.kms.server_address[1]
        Thread(target=cls.kms.serve_forever, daemon=True).start()

        cls.admin_db = cls.server_mod.LiorgDb(Path(cls._tmp.name) / "org.db")
        cls.server_mod.LiorgHandler.db = cls.admin_db
        cls.server_mod.LiorgHandler.jwt_secret = "admin-secret"
        os.environ["LIBREBASE_KMS_URL"] = f"http://127.0.0.1:{cls.kms_port}"
        os.environ["LIBREBASE_KMS_SERVICE_ROLE"] = "kms-role"
        cls.admin = ThreadingHTTPServer(("127.0.0.1", 0), cls.server_mod.LiorgHandler)
        cls.admin_port = cls.admin.server_address[1]
        Thread(target=cls.admin.serve_forever, daemon=True).start()

        # Seed an MCP key for an org created via /org/v1/setup.
        from urllib.request import Request, urlopen

        req = Request(
            f"http://127.0.0.1:{cls.admin_port}/org/v1/setup",
            data=json.dumps(
                {"name": "Acme", "ownerEmail": "o@a.test", "password": "hunter2hunter2"}
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req) as r:
            cls.org_id = json.loads(r.read())["orgId"]
        cls.mcp_key = cls.server_mod.issue_mcp_key(cls.admin_db, cls.org_id)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.admin.shutdown()
        cls.admin.server_close()
        cls.kms.shutdown()
        cls.kms.server_close()
        cls.admin_db.close()
        cls.kms_db.close()
        os.environ.pop("LIBREBASE_KMS_URL", None)
        os.environ.pop("LIBREBASE_KMS_SERVICE_ROLE", None)
        cls._tmp.cleanup()

    def _call(self, mcp: object, name: str, args: dict | None = None, msg_id: int = 1) -> dict:
        out = mcp._handle(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "method": "tools/call",
                "params": {"name": name, "arguments": args or {}},
            }
        )
        assert out is not None
        text = out["result"]["content"][0]["text"]
        return json.loads(text)

    def test_mcp_lists_oauth_tools(self) -> None:
        out = load_module(MCP_MODULE)._handle(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
        )
        names = {t["name"] for t in out["result"]["tools"]}
        self.assertIn("auth_provider_upsert", names)
        self.assertIn("auth_provider_list", names)

    def test_mcp_sets_up_oauth_provider(self) -> None:
        os.environ["LIBREBASE_ADMIN_URL"] = f"http://127.0.0.1:{self.admin_port}"
        os.environ["LIBREBASE_MCP_KEY"] = self.mcp_key
        mcp = load_module(MCP_MODULE)

        who = self._call(mcp, "org_whoami")
        self.assertEqual(who["orgId"], self.org_id)

        project = self._call(
            mcp,
            "project_create",
            {"name": "webapp", "instanceId": "inst_demo", "region": "local"},
        )
        self.assertEqual(project["orgId"], self.org_id)
        project_id = project["id"]

        provider = self._call(
            mcp,
            "auth_provider_upsert",
            {
                "projectId": project_id,
                "provider": "google",
                "clientId": "cid-oauth",
                "clientSecret": "top-secret",
                "redirectUris": ["https://app.example.com/auth/v1/callback"],
                "enabled": True,
            },
        )
        self.assertEqual(provider["clientId"], "cid-oauth")
        self.assertEqual(provider["provider"], "google")
        self.assertNotIn("clientSecret", provider)  # never leaked

        providers = self._call(mcp, "auth_provider_list", {"projectId": project_id})
        self.assertEqual(len(providers), 1)
        self.assertEqual(providers[0]["provider"], "google")
        self.assertNotIn("clientSecretEnc", providers[0])  # masked view via list


if __name__ == "__main__":
    unittest.main()
