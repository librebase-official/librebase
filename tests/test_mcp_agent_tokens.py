"""LIB-162: per-agent MCP tokens — rotation isolation, auth causes, revoke-all."""

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


def http_json(
    port: int,
    method: str,
    path: str,
    body: dict | None = None,
    token: str | None = None,
) -> tuple[int, dict]:
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode()
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"error": raw}
        return exc.code, payload


class McpAgentTokenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = load_server()
        cls._tmp = tempfile.TemporaryDirectory()
        cls.db = cls.mod.LiorgDb(Path(cls._tmp.name) / "org.db")
        cls.mod.LiorgHandler.db = cls.db
        cls.mod.LiorgHandler.jwt_secret = "test-secret"
        cls.admin = ThreadingHTTPServer(("127.0.0.1", 0), cls.mod.LiorgHandler)
        cls.port = cls.admin.server_address[1]
        Thread(target=cls.admin.serve_forever, daemon=True).start()

        _, setup = http_json(
            cls.port,
            "POST",
            "/org/v1/setup",
            {"name": "Acme", "ownerEmail": "o@ac.me", "password": "password12"},
        )
        cls.org_id = setup["orgId"]
        cls.owner_jwt = setup["token"]
        cls.org_key = cls.mod.issue_mcp_key(cls.db, cls.org_id)

        _, bot_a = http_json(
            cls.port,
            "POST",
            f"/org/v1/orgs/{cls.org_id}/bots",
            {"name": "Agent A"},
            token=cls.owner_jwt,
        )
        _, bot_b = http_json(
            cls.port,
            "POST",
            f"/org/v1/orgs/{cls.org_id}/bots",
            {"name": "Agent B"},
            token=cls.owner_jwt,
        )
        cls.bot_a = bot_a["id"]
        cls.bot_b = bot_b["id"]

    @classmethod
    def tearDownClass(cls) -> None:
        cls.admin.shutdown()
        cls._tmp.cleanup()

    def test_rotate_agent_a_leaves_agent_b_token_valid(self) -> None:
        _, rot_a = http_json(
            self.port,
            "POST",
            f"/org/v1/orgs/{self.org_id}/bots/{self.bot_a}/mcp-tokens/rotate",
            {},
            token=self.owner_jwt,
        )
        _, rot_b = http_json(
            self.port,
            "POST",
            f"/org/v1/orgs/{self.org_id}/bots/{self.bot_b}/mcp-tokens/rotate",
            {},
            token=self.owner_jwt,
        )
        token_a = rot_a["accessToken"]
        token_b = rot_b["accessToken"]

        status, _ = http_json(self.port, "GET", "/org/v1/mcp/org", token=token_b)
        self.assertEqual(status, 200)

        _, rot_a2 = http_json(
            self.port,
            "POST",
            f"/org/v1/orgs/{self.org_id}/bots/{self.bot_a}/mcp-tokens/rotate",
            {},
            token=self.owner_jwt,
        )
        new_a = rot_a2["accessToken"]

        status_old, body_old = http_json(self.port, "GET", "/org/v1/mcp/org", token=token_a)
        self.assertEqual(status_old, 401)
        self.assertEqual(body_old.get("cause"), "revoked")

        status_b, _ = http_json(self.port, "GET", "/org/v1/mcp/org", token=token_b)
        self.assertEqual(status_b, 200)

        status_new, _ = http_json(self.port, "GET", "/org/v1/mcp/org", token=new_a)
        self.assertEqual(status_new, 200)

    def test_auth_error_causes(self) -> None:
        status, body = http_json(
            self.port,
            "GET",
            "/org/v1/mcp/org",
            token="lb_mcp_" + ("x" * 40),
        )
        self.assertEqual(status, 401)
        self.assertEqual(body.get("cause"), "unknown_token")

        _, rot = http_json(
            self.port,
            "POST",
            f"/org/v1/orgs/{self.org_id}/bots/{self.bot_a}/mcp-tokens/rotate",
            {},
            token=self.owner_jwt,
        )
        revoked = rot["accessToken"]
        _, tokens = http_json(
            self.port,
            "GET",
            f"/org/v1/orgs/{self.org_id}/bots/{self.bot_a}/mcp-tokens",
            token=self.owner_jwt,
        )
        active = next(t for t in tokens if not t.get("revoked"))
        http_json(
            self.port,
            "POST",
            f"/org/v1/orgs/{self.org_id}/bots/{self.bot_a}/mcp-tokens/{active['id']}/revoke",
            {},
            token=self.owner_jwt,
        )
        status, body = http_json(self.port, "GET", "/org/v1/mcp/org", token=revoked)
        self.assertEqual(status, 401)
        self.assertEqual(body.get("cause"), "revoked")

    def test_revoke_all_invalidates_org_and_agent_tokens(self) -> None:
        _, rot = http_json(
            self.port,
            "POST",
            f"/org/v1/orgs/{self.org_id}/bots/{self.bot_b}/mcp-tokens/rotate",
            {},
            token=self.owner_jwt,
        )
        agent_tok = rot["accessToken"]
        org_key = self.mod.issue_mcp_key(self.db, self.org_id)

        status, payload = http_json(
            self.port,
            "POST",
            f"/org/v1/orgs/{self.org_id}/mcp-keys/revoke-all",
            {},
            token=self.owner_jwt,
        )
        self.assertEqual(status, 200)
        self.assertGreaterEqual(payload.get("revoked", 0), 2)

        for tok in (agent_tok, org_key):
            st, body = http_json(self.port, "GET", "/org/v1/mcp/org", token=tok)
            self.assertEqual(st, 401)
            self.assertEqual(body.get("cause"), "revoked")

    def test_org_key_rotate_does_not_revoke_agent_token(self) -> None:
        _, rot = http_json(
            self.port,
            "POST",
            f"/org/v1/orgs/{self.org_id}/bots/{self.bot_a}/mcp-tokens/rotate",
            {},
            token=self.owner_jwt,
        )
        agent_tok = rot["accessToken"]
        old_org = self.org_key
        status, rotate_body = http_json(
            self.port,
            "POST",
            f"/org/v1/orgs/{self.org_id}/mcp-keys/rotate",
            {},
            token=self.owner_jwt,
        )
        self.assertEqual(status, 200)
        new_org = rotate_body["mcpKey"]

        st_agent, _ = http_json(self.port, "GET", "/org/v1/mcp/org", token=agent_tok)
        self.assertEqual(st_agent, 200)

        st_old_org, body = http_json(self.port, "GET", "/org/v1/mcp/org", token=old_org)
        self.assertEqual(st_old_org, 401)
        self.assertEqual(body.get("cause"), "revoked")

        st_new_org, _ = http_json(self.port, "GET", "/org/v1/mcp/org", token=new_org)
        self.assertEqual(st_new_org, 200)


if __name__ == "__main__":
    unittest.main()
