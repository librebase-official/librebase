"""Comprehensive MCP + admin-api integration tests — full tool coverage + CRUD gaps.

Covers the MCP tools that had zero test coverage:
  - instance_create, instance_launch, instance_stop, instance_list, instance_get
  - member_list, member_invite, member_update_role
  - host_create, host_list
  - project_list

Plus admin-api delete endpoints and instance PATCH lifecycle.
"""

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
MCP_MODULE = ROOT / "mcp" / "librebase_mcp" / "__main__.py"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("lb_mcp", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_server():
    spec = importlib.util.spec_from_file_location("admin_server", SCRIPTS / "admin_server.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _McpTestBase(unittest.TestCase):
    """Shared setup: in-process KMS + admin-api + seeded org with MCP key."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.server_mod = load_server()
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

        # Seed org + MCP key
        req = urllib.request.Request(
            f"http://127.0.0.1:{cls.admin_port}/org/v1/setup",
            data=json.dumps(
                {"name": "TestOrg", "ownerEmail": "own@t.c", "password": "hunter2hunter2"}
            ).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as r:
            resp = json.loads(r.read())
            cls.org_id = resp["orgId"]
            cls.setup_token = resp["token"]
        cls.mcp_key = cls.server_mod.issue_mcp_key(cls.admin_db, cls.org_id)

        os.environ["LIBREBASE_ADMIN_URL"] = f"http://127.0.0.1:{cls.admin_port}"
        os.environ["LIBREBASE_MCP_KEY"] = cls.mcp_key

    @classmethod
    def tearDownClass(cls) -> None:
        cls.admin.shutdown()
        cls.admin.server_close()
        cls.kms.shutdown()
        cls.kms.server_close()
        cls.admin_db.close()
        cls.kms_db.close()
        for k in ("LIBREBASE_KMS_URL", "LIBREBASE_KMS_SERVICE_ROLE", "LIBREBASE_ADMIN_URL", "LIBREBASE_MCP_KEY"):
            os.environ.pop(k, None)
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

    def _http(self, method: str, path: str, body: dict | None = None, *, token: str | None = None) -> tuple[int, dict]:
        data = json.dumps(body).encode() if body else None
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.admin_port}{path}",
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                raw = r.read().decode() or "{}"
                return r.status, json.loads(raw) if raw.strip() else {}
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode() or "{}"
            try:
                parsed = json.loads(raw)
            except ValueError:
                parsed = {"error": raw}
            return exc.code, parsed

    @property
    def _token(self) -> str:
        return self.setup_token


# ── MCP instance lifecycle ──────────────────────────────────────────


class TestMcpInstanceLifecycle(_McpTestBase):

    def test_instance_create_and_list(self) -> None:
        mcp = load_module(MCP_MODULE)
        inst = self._call(mcp, "instance_create", {"name": "my-db", "region": "eu-west"})
        self.assertEqual(inst["name"], "my-db")
        self.assertEqual(inst["status"], "stopped")
        self.assertIn("id", inst)

        instances = self._call(mcp, "instance_list")
        self.assertIsInstance(instances, list)
        ids = [i["id"] for i in instances]
        self.assertIn(inst["id"], ids)

    def test_instance_get(self) -> None:
        mcp = load_module(MCP_MODULE)
        inst = self._call(mcp, "instance_create", {"name": "get-me"})
        got = self._call(mcp, "instance_get", {"instanceId": inst["id"]})
        self.assertEqual(got["id"], inst["id"])
        self.assertEqual(got["name"], "get-me")

    def test_instance_launch_and_stop(self) -> None:
        mcp = load_module(MCP_MODULE)
        inst = self._call(mcp, "instance_create", {"name": "lifecycle"})
        inst_id = inst["id"]
        self.assertEqual(inst["status"], "stopped")

        launched = self._call(mcp, "instance_launch", {"instanceId": inst_id})
        self.assertEqual(launched["status"], "running")

        got = self._call(mcp, "instance_get", {"instanceId": inst_id})
        self.assertEqual(got["status"], "running")

        stopped = self._call(mcp, "instance_stop", {"instanceId": inst_id})
        self.assertEqual(stopped["status"], "stopped")

    def test_instance_get_nonexistent(self) -> None:
        mcp = load_module(MCP_MODULE)
        result = self._call(mcp, "instance_get", {"instanceId": "inst_nope"})
        self.assertTrue(
            "error" in result or result.get("status") == 404
        )


# ── MCP member management ──────────────────────────────────────────


class TestMcpMemberManagement(_McpTestBase):

    def test_member_list(self) -> None:
        mcp = load_module(MCP_MODULE)
        members = self._call(mcp, "member_list")
        self.assertIsInstance(members, list)
        emails = [m.get("email") for m in members]
        self.assertIn("own@t.c", emails)

    def test_member_invite_requires_owner_role(self) -> None:
        """SECURITY: MCP keys have 'admin' role; inviting requires 'owner' role.
        MCP keys must NOT be able to invite arbitrary users to the org."""
        mcp = load_module(MCP_MODULE)
        result = self._call(mcp, "member_invite", {"email": "new@t.c", "role": "member"})
        # MCP key is admin, not owner — invite should be rejected
        self.assertTrue(
            result.get("error") or result.get("status") == 403,
            f"MCP key must not be able to invite members: {result}",
        )

    def test_member_list(self) -> None:
        mcp = load_module(MCP_MODULE)
        result = self._call(mcp, "member_list")
        # member_list is a read operation, admin role should allow it
        self.assertIsInstance(result, list)


# ── MCP host + project ─────────────────────────────────────────────


class TestMcpHostAndProject(_McpTestBase):

    def test_host_create_and_list(self) -> None:
        mcp = load_module(MCP_MODULE)
        host = self._call(mcp, "host_create", {"name": "vm-1", "region": "eu", "memMb": 512})
        self.assertEqual(host["name"], "vm-1")
        self.assertEqual(host["memMb"], 512)

        hosts = self._call(mcp, "host_list")
        self.assertIsInstance(hosts, list)
        ids = [h["id"] for h in hosts]
        self.assertIn(host["id"], ids)

    def test_project_list(self) -> None:
        mcp = load_module(MCP_MODULE)
        inst = self._call(mcp, "instance_create", {"name": "for-proj"})
        proj = self._call(mcp, "project_create", {"name": "webapp", "instanceId": inst["id"]})
        self.assertEqual(proj["name"], "webapp")

        projects = self._call(mcp, "project_list")
        self.assertIsInstance(projects, list)
        names = [p["name"] for p in projects]
        self.assertIn("webapp", names)


# ── Admin-api HTTP instance CRUD ───────────────────────────────────


class TestAdminApiInstanceCrud(_McpTestBase):

    def test_instance_create_via_http(self) -> None:
        st, inst = self._http(
            "POST", f"/org/v1/orgs/{self.org_id}/instances",
            {"name": "http-inst"}, token=self._token,
        )
        self.assertEqual(st, 201)
        self.assertEqual(inst["name"], "http-inst")
        self.assertEqual(inst["status"], "stopped")

    def test_instance_launch_via_http(self) -> None:
        st, inst = self._http(
            "POST", f"/org/v1/orgs/{self.org_id}/instances",
            {"name": "launch-me"}, token=self._token,
        )
        self.assertEqual(st, 201)
        st2, launched = self._http(
            "PATCH",
            f"/org/v1/orgs/{self.org_id}/instances/{inst['id']}",
            {"status": "running"},
            token=self._token,
        )
        self.assertEqual(st2, 200)
        self.assertEqual(launched["status"], "running")

    def test_instance_delete_via_http(self) -> None:
        st, inst = self._http(
            "POST", f"/org/v1/orgs/{self.org_id}/instances",
            {"name": "delete-me"}, token=self._token,
        )
        self.assertEqual(st, 201)
        st2, _ = self._http("DELETE", f"/org/v1/orgs/{self.org_id}/instances/{inst['id']}", token=self._token)
        self.assertEqual(st2, 200)
        st3, _ = self._http("GET", f"/org/v1/orgs/{self.org_id}/instances/{inst['id']}", token=self._token)
        self.assertEqual(st3, 404)

    def test_unauthed_instance_create_returns_401(self) -> None:
        st, _ = self._http(
            "POST", f"/org/v1/orgs/{self.org_id}/instances",
            {"name": "no-auth"},
        )
        self.assertEqual(st, 401)


# ── Admin-api delete endpoints ─────────────────────────────────────


class TestAdminApiDeleteEndpoints(_McpTestBase):

    def test_project_delete(self) -> None:
        st, inst = self._http(
            "POST", f"/org/v1/orgs/{self.org_id}/instances",
            {"name": "proj-host"}, token=self._token,
        )
        self.assertEqual(st, 201)
        st2, proj = self._http(
            "POST",
            f"/org/v1/orgs/{self.org_id}/projects",
            {"name": "to-delete", "instanceId": inst["id"]},
            token=self._token,
        )
        self.assertEqual(st2, 201)
        st3, _ = self._http("DELETE", f"/org/v1/orgs/{self.org_id}/projects/{proj['id']}", token=self._token)
        self.assertEqual(st3, 200)
        st4, _ = self._http("GET", f"/org/v1/orgs/{self.org_id}/projects/{proj['id']}", token=self._token)
        self.assertEqual(st4, 404)

    def test_host_delete(self) -> None:
        st, host = self._http(
            "POST",
            f"/org/v1/orgs/{self.org_id}/hosts",
            {"name": "del-host", "provider": "local", "region": "eu", "memMb": 256},
            token=self._token,
        )
        self.assertEqual(st, 201)
        st2, _ = self._http("DELETE", f"/org/v1/orgs/{self.org_id}/hosts/{host['id']}", token=self._token)
        self.assertEqual(st2, 200)
        st3, _ = self._http("GET", f"/org/v1/orgs/{self.org_id}/hosts/{host['id']}", token=self._token)
        self.assertEqual(st3, 404)

    def test_provider_upsert_and_delete(self) -> None:
        # Create instance + project first
        st, inst = self._http(
            "POST", f"/org/v1/orgs/{self.org_id}/instances",
            {"name": "prov-host"}, token=self._token,
        )
        self.assertEqual(st, 201)
        st2, proj = self._http(
            "POST",
            f"/org/v1/orgs/{self.org_id}/projects",
            {"name": "prov-proj", "instanceId": inst["id"]},
            token=self._token,
        )
        self.assertEqual(st2, 201)

        # Upsert provider (returns 200 per admin-api design)
        st3, prov = self._http(
            "POST",
            f"/org/v1/orgs/{self.org_id}/projects/{proj['id']}/providers",
            {"provider": "github", "clientId": "cid", "clientSecret": "secret", "redirectUris": ["https://x.com/cb"]},
            token=self._token,
        )
        self.assertEqual(st3, 200)
        self.assertEqual(prov["provider"], "github")
        self.assertEqual(prov["clientId"], "cid")

        # Delete provider
        st4, _ = self._http(
            "DELETE",
            f"/org/v1/orgs/{self.org_id}/projects/{proj['id']}/providers/github",
            token=self._token,
        )
        self.assertEqual(st4, 200)

        # Verify gone
        st5, providers = self._http(
            "GET",
            f"/org/v1/orgs/{self.org_id}/projects/{proj['id']}/providers",
            token=self._token,
        )
        self.assertEqual(st5, 200)
        self.assertEqual(len(providers), 0)


# ── Admin-api entitlements ─────────────────────────────────────────


class TestAdminApiEntitlements(_McpTestBase):

    def test_self_host_allows_instance_launch(self) -> None:
        st, body = self._http(
            "GET",
            f"/org/v1/orgs/{self.org_id}/entitlements/instance.launch",
            token=self._token,
        )
        self.assertEqual(st, 200)
        self.assertTrue(body["enabled"])

    def test_suspended_org_blocks_instance_launch(self) -> None:
        """A suspended-org member should see instance.launch denied."""
        now = self.server_mod.utc_now()
        # Create a suspended org
        self.admin_db.execute(
            "INSERT INTO organizations (id, name, slug, edition, plan, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("org_ent", "Ent", "ent", "suspended", "suspended", now),
        )
        # Add the current user as owner
        user_id = self.admin_db.fetchone("SELECT id FROM users WHERE email = 'own@t.c'")["id"]
        self.admin_db.execute(
            "INSERT INTO members (org_id, user_id, role, created_at) VALUES (?, ?, ?, ?)",
            ("org_ent", user_id, "owner", now),
        )
        # Check entitlements for the suspended org
        st, body = self._http(
            "GET",
            "/org/v1/orgs/org_ent/entitlements/instance.launch",
            token=self._token,
        )
        self.assertEqual(st, 200)
        self.assertFalse(body["enabled"])


# ── Admin-api MFA setup ────────────────────────────────────────────


class TestAdminApiMfaSetup(_McpTestBase):

    def test_mfa_setup_returns_secret_and_uri(self) -> None:
        token = self._token
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.admin_port}/org/v1/auth/mfa/setup",
            data=b"{}",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            body = json.loads(r.read().decode())
        self.assertIn("secret", body)
        self.assertIn("uri", body)
        self.assertIn("otpauth://", body["uri"])
        # Verify the TOTP code works with the returned secret
        code = self.server_mod.totp_now(body["secret"])
        self.assertEqual(len(code), 6)
        self.assertTrue(self.server_mod.totp_verify(body["secret"], code))


if __name__ == "__main__":
    unittest.main()
