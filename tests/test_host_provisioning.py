"""Admin-API host provisioning tests.

Covers the Hetzner substrate wiring in admin_server.py:
  - rent a VM with hcloud configured -> real server_id/ip + status "provisioning"
  - rent without hcloud -> bookkeeping row only (status "stopped")
  - agent register is gated by the provisioning-time agent bearer token
  - Hetzner create failure -> 502, no orphan host row
  - GET host syncs Hetzner status
"""

from __future__ import annotations

import importlib.util
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
import urllib.error
import urllib.request

SCRIPTS = Path(__file__).resolve().parents[1] / "admin-api" / "scripts"


def load_server():
    spec = importlib.util.spec_from_file_location("admin_server", SCRIPTS / "admin_server.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeHcloud:
    """In-process stand-in for admin-api/scripts/hcloud.py."""

    configured = True
    last_agent_token: str | None = None

    def hcloud_configured(self) -> bool:
        return self.configured

    def hcloud_base(self) -> str:
        return "http://127.0.0.1:0"

    def hcloud_image_id(self):
        return None

    def provision_host(self, host_id, name, region, agent_token):
        _FakeHcloud.last_agent_token = agent_token
        return {"server_id": 99, "ip": "203.0.113.9"}

    def get_server(self, server_id):
        return {"status": "running", "ip": "203.0.113.9", "name": "x"}

    def delete_server(self, server_id) -> None:
        pass


class TestHostProvisioning(unittest.TestCase):
    def _boot(self, hcloud_on):
        _FakeHcloud.last_agent_token = None
        mod = load_server()
        tmp = tempfile.TemporaryDirectory()
        db = mod.LiorgDb(Path(tmp.name) / "org.db")
        now = mod.utc_now()
        org_id = "org_hp"
        db.execute(
            "INSERT INTO organizations (id, name, slug, edition, created_at, plan) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (org_id, "HP Co", "hp", "cloud-paid", now, "cloud-paid"),
        )
        db.execute(
            "INSERT INTO users (id, email, password_hash, created_at, email_verified) "
            "VALUES (?, ?, ?, ?, 1)",
            ("u_owner", "owner@hp.c", mod.hash_password("pw"), now),
        )
        db.execute(
            "INSERT INTO members (org_id, user_id, role, created_at) VALUES (?, ?, ?, ?)",
            (org_id, "u_owner", "owner", now),
        )
        jwt = "hp-jwt-secret"
        old_db = mod.LiorgHandler.__dict__.get("db")
        old_jwt = mod.LiorgHandler.__dict__.get("jwt_secret")
        old_hcloud = getattr(mod, "_hcloud", None)
        mod.LiorgHandler.db = db
        mod.LiorgHandler.jwt_secret = jwt
        fake = _FakeHcloud()
        fake.configured = hcloud_on
        mod._hcloud = fake
        server = ThreadingHTTPServer(("127.0.0.1", 0), mod.LiorgHandler)
        base = "http://127.0.0.1:%d" % server.server_port
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return mod, tmp, db, base, server, jwt, old_db, old_jwt, old_hcloud, org_id

    def _token(self, mod, db, jwt):
        return mod.issue_session(db, jwt, "u_owner", "org_hp", "owner", "cloud-paid")[0]

    def _post(self, base, path, body, token=None):
        data = json.dumps(body).encode()
        hdrs = {"Content-Type": "application/json"}
        if token:
            hdrs["Authorization"] = "Bearer " + token
        req = urllib.request.Request(base + path, data=data, method="POST", headers=hdrs)
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

    def _get(self, base, path, token=None):
        hdrs = {}
        if token:
            hdrs["Authorization"] = "Bearer " + token
        req = urllib.request.Request(base + path, method="GET", headers=hdrs)
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

    def _cleanup(self, mod, server, db, tmp, old_db, old_jwt, old_hcloud):
        server.shutdown()
        server.server_close()
        mod.LiorgHandler.db = old_db
        mod.LiorgHandler.jwt_secret = old_jwt
        mod._hcloud = old_hcloud
        db.close()
        tmp.cleanup()

    def test_rent_provisions_real_server_when_hcloud_configured(self) -> None:
        mod, tmp, db, base, server, jwt, old_db, old_jwt, old_hcloud, org_id = self._boot(True)
        token = self._token(mod, db, jwt)
        try:
            st, host = self._post(
                base,
                "/org/v1/orgs/%s/hosts" % org_id,
                {"name": "vm-1", "provider": "hetzner", "region": "nbg1", "memMb": 1024},
                token=token,
            )
            self.assertEqual(st, 201)
            self.assertEqual(host["serverId"], 99)
            self.assertEqual(host["ip"], "203.0.113.9")
            self.assertEqual(host["status"], "provisioning")
        finally:
            self._cleanup(mod, server, db, tmp, old_db, old_jwt, old_hcloud)

    def test_rent_without_hcloud_is_bookkeeping_only(self) -> None:
        mod, tmp, db, base, server, jwt, old_db, old_jwt, old_hcloud, org_id = self._boot(False)
        token = self._token(mod, db, jwt)
        try:
            st, host = self._post(
                base,
                "/org/v1/orgs/%s/hosts" % org_id,
                {"name": "vm-1", "provider": "linative-cloud", "region": "local", "memMb": 512},
                token=token,
            )
            self.assertEqual(st, 201)
            self.assertIsNone(host["serverId"])
            self.assertIsNone(host["ip"])
            self.assertEqual(host["status"], "stopped")
        finally:
            self._cleanup(mod, server, db, tmp, old_db, old_jwt, old_hcloud)

    def test_agent_register_requires_provisioning_token(self) -> None:
        mod, tmp, db, base, server, jwt, old_db, old_jwt, old_hcloud, org_id = self._boot(True)
        token = self._token(mod, db, jwt)
        try:
            st, host = self._post(
                base,
                "/org/v1/orgs/%s/hosts" % org_id,
                {"name": "vm-2", "provider": "hetzner", "region": "nbg1", "memMb": 1024},
                token=token,
            )
            self.assertEqual(st, 201)
            hid = host["id"]
            # Wrong bearer (a user JWT, not the agent token) -> 401
            st2, _ = self._post(
                base,
                "/org/v1/orgs/%s/hosts/%s/register" % (org_id, hid),
                {"ip": "203.0.113.9"},
                token=token,
            )
            self.assertEqual(st2, 401)
        finally:
            self._cleanup(mod, server, db, tmp, old_db, old_jwt, old_hcloud)

    def test_provisioning_host_syncs_to_running_on_get(self) -> None:
        mod, tmp, db, base, server, jwt, old_db, old_jwt, old_hcloud, org_id = self._boot(True)
        token = self._token(mod, db, jwt)
        try:
            st, host = self._post(
                base,
                "/org/v1/orgs/%s/hosts" % org_id,
                {"name": "vm-3", "provider": "hetzner", "region": "nbg1", "memMb": 1024},
                token=token,
            )
            self.assertEqual(st, 201)
            hid = host["id"]
            # Simulate the agent having registered (status -> running, ip persisted).
            db.execute("UPDATE hosts SET status = 'running', ip = '203.0.113.9' WHERE id = ?", (hid,))
            st3, host2 = self._get(base, "/org/v1/orgs/%s/hosts/%s" % (org_id, hid), token=token)
            self.assertEqual(st3, 200)
            self.assertEqual(host2["status"], "running")
            self.assertEqual(host2["ip"], "203.0.113.9")
        finally:
            self._cleanup(mod, server, db, tmp, old_db, old_jwt, old_hcloud)

    def test_hetzner_failure_returns_502_and_no_orphan(self) -> None:
        mod, tmp, db, base, server, jwt, old_db, old_jwt, old_hcloud, org_id = self._boot(True)

        def boom(host_id, name, region, agent_token):
            raise RuntimeError("hcloud down")

        mod._hcloud.provision_host = boom  # type: ignore[assignment]
        token = self._token(mod, db, jwt)
        try:
            st, err = self._post(
                base,
                "/org/v1/orgs/%s/hosts" % org_id,
                {"name": "vm-1", "provider": "hetzner", "region": "nbg1", "memMb": 512},
                token=token,
            )
            self.assertEqual(st, 502)
            self.assertIn("provisioning failed", err["error"])
            # No host row should remain after a failed provision.
            self.assertEqual(db.fetchall("SELECT id FROM hosts WHERE org_id = ?", (org_id,)), [])
        finally:
            self._cleanup(mod, server, db, tmp, old_db, old_jwt, old_hcloud)

    def test_full_provisioning_smoke(self) -> None:
        """End-to-end: create host → Hetzner provisions → agent registers → running."""
        mod, tmp, db, base, server, jwt, old_db, old_jwt, old_hcloud, org_id = self._boot(True)
        token = self._token(mod, db, jwt)
        try:
            # 1. Create a host — should provision a real Hetzner server (via fake)
            st, host = self._post(
                base,
                "/org/v1/orgs/%s/hosts" % org_id,
                {"name": "smoke-vm", "provider": "hetzner", "region": "fsn1", "memMb": 1024},
                token=token,
            )
            self.assertEqual(st, 201, host)
            hid = host["id"]
            self.assertEqual(host["serverId"], 99)
            self.assertEqual(host["ip"], "203.0.113.9")
            self.assertEqual(host["status"], "provisioning")

            # 2. Retrieve the plaintext agent_token captured by the fake
            agent_token = _FakeHcloud.last_agent_token
            self.assertIsNotNone(agent_token)

            # 3. Agent registers — flip to running
            st2, reg = self._post(
                base,
                "/org/v1/host-agent/register",
                {"ip": "203.0.113.9"},
                token=agent_token,
            )
            self.assertEqual(st2, 200, reg)
            self.assertEqual(reg["status"], "running")

            # 4. Verify GET returns running
            st3, host2 = self._get(base, "/org/v1/orgs/%s/hosts/%s" % (org_id, hid), token=token)
            self.assertEqual(st3, 200)
            self.assertEqual(host2["status"], "running")
            self.assertEqual(host2["ip"], "203.0.113.9")
            self.assertEqual(host2["serverId"], 99)
        finally:
            self._cleanup(mod, server, db, tmp, old_db, old_jwt, old_hcloud)

    def test_hetzner_demo_fallback_without_hcloud(self) -> None:
        """When provider=hetzner but hcloud is not configured, host gets
        provisioning status with a placeholder IP (demo mode)."""
        mod, tmp, db, base, server, jwt, old_db, old_jwt, old_hcloud, org_id = self._boot(True)
        token = self._token(mod, db, jwt)
        try:
            # Disable hcloud configured check
            mod._hcloud.configured = False  # type: ignore[attr-defined]
            st, host = self._post(
                base,
                "/org/v1/orgs/%s/hosts" % org_id,
                {"name": "demo-vm", "provider": "hetzner", "region": "fsn1", "memMb": 512},
                token=token,
            )
            self.assertEqual(st, 201, host)
            self.assertEqual(host["status"], "provisioning")
            self.assertEqual(host["ip"], "192.0.2.1")
            self.assertEqual(host["serverId"], 0)
        finally:
            self._cleanup(mod, server, db, tmp, old_db, old_jwt, old_hcloud)


if __name__ == "__main__":
    unittest.main()
