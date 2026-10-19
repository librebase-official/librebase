"""LIB-162 / saas PR #134: per-token MCP rotation, auth causes, revoke-all."""

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


def mint_bot_token(port: int, org_id: str, bot_id: str, jwt: str) -> tuple[str, str]:
    status, body = http_json(
        port,
        "POST",
        f"/org/v1/orgs/{org_id}/bots/{bot_id}/mcp-tokens",
        {},
        token=jwt,
    )
    assert status == 200, body
    return body["accessToken"], body["tokenId"]


def rotate_token(port: int, org_id: str, token_id: str, jwt: str) -> tuple[str, str]:
    status, body = http_json(
        port,
        "POST",
        f"/org/v1/orgs/{org_id}/mcp-tokens/{token_id}/rotate",
        {},
        token=jwt,
    )
    assert status == 200, body
    return body["accessToken"], body["tokenId"]


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
        token_a, id_a = mint_bot_token(self.port, self.org_id, self.bot_a, self.owner_jwt)
        token_b, _id_b = mint_bot_token(self.port, self.org_id, self.bot_b, self.owner_jwt)

        status, _ = http_json(self.port, "GET", "/org/v1/mcp/org", token=token_b)
        self.assertEqual(status, 200)

        new_a, _new_id = rotate_token(self.port, self.org_id, id_a, self.owner_jwt)

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
        self.assertEqual(body.get("cause"), "unknown")

        token, token_id = mint_bot_token(self.port, self.org_id, self.bot_a, self.owner_jwt)
        http_json(
            self.port,
            "POST",
            f"/org/v1/orgs/{self.org_id}/mcp-tokens/{token_id}/revoke",
            {},
            token=self.owner_jwt,
        )
        status, body = http_json(self.port, "GET", "/org/v1/mcp/org", token=token)
        self.assertEqual(status, 401)
        self.assertEqual(body.get("cause"), "revoked")

    def test_revoke_all_invalidates_org_and_agent_tokens(self) -> None:
        agent_tok, _ = mint_bot_token(self.port, self.org_id, self.bot_b, self.owner_jwt)
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
        agent_tok, _ = mint_bot_token(self.port, self.org_id, self.bot_a, self.owner_jwt)
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

    def test_device_flow_token_has_device_code_id(self) -> None:
        _, start = http_json(
            self.port,
            "POST",
            "/org/v1/mcp/device/start",
            {"clientName": "test-agent", "botId": self.bot_a},
        )
        self.assertIn("deviceCodeId", start)
        device_code_id = start["deviceCodeId"]
        user_code = start["userCode"]

        http_json(
            self.port,
            "POST",
            f"/org/v1/mcp/device/{user_code}/approve",
            {"orgId": self.org_id, "botId": self.bot_a},
            token=self.owner_jwt,
        )
        _, poll = http_json(
            self.port,
            "POST",
            "/org/v1/mcp/device/token",
            {"deviceCode": start["deviceCode"]},
        )
        self.assertIn("accessToken", poll)
        self.assertEqual(poll.get("deviceCodeId"), device_code_id)

        _, tokens = http_json(
            self.port,
            "GET",
            f"/org/v1/orgs/{self.org_id}/mcp-tokens?botId={self.bot_a}",
            token=self.owner_jwt,
        )
        bound = [t for t in tokens if t.get("deviceCodeId") == device_code_id]
        self.assertEqual(len(bound), 1)


if __name__ == "__main__":
    unittest.main()
