"""End-to-end (mocked) host provisioning.

Spins up:
  1. A *fake Hetzner Cloud* HTTP server (stdlib) that models server create/get/delete
     and retains the cloud-init `user_data` it received.
  2. The REAL admin-api server (admin_server.py) pointed at the fake Hetzner via
     LIBREBASE_HETZNER_API_TOKEN + LIBREBASE_HETZNER_API_URL.

Flow exercised end-to-end with mocks (no cloud charges):
  - rent a VM (POST /hosts, provider=hetzner) -> admin calls hcloud.create_server
    -> real Hetzner HTTP POST /servers -> host row gets server_id + ip + status=provisioning
  - the "host agent" (this test, standing in for the real agent on the box) reads the
    cloud-init token injected at provisioning time and calls POST /hosts/{id}/register
    -> host flips to running
  - GET /hosts reflects running status
  - delete host -> real Hetzner HTTP DELETE /servers -> row removed
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import urllib.error
import urllib.request

HERE = Path(__file__).resolve()
SCRIPTS = HERE.parents[2] / "admin-api" / "scripts"
import sys as _sys

if str(SCRIPTS) not in _sys.path:
    _sys.path.insert(0, str(SCRIPTS))


def load_server():
    spec = importlib.util.spec_from_file_location("admin_server_e2e", SCRIPTS / "admin_server.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeHcloudServer(BaseHTTPRequestHandler):
    """Fake Hetzner Cloud v1: /v1/servers CRUD, retains user_data."""

    created: dict[int, dict] = {}
    next_id = 1
    lock = threading.Lock()

    def _send(self, code: int, obj: object) -> None:
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _auth(self) -> bool:
        return self.headers.get("Authorization") == "Bearer test-hetzner-token"

    def do_POST(self) -> None:  # noqa: N802
        if not self._auth():
            self._send(401, {"error": {"code": "unauthorized"}}); return
        if self.path == "/v1/servers":
            raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            payload = json.loads(raw or b"{}")
            with _FakeHcloudServer.lock:
                sid = _FakeHcloudServer.next_id
                _FakeHcloudServer.next_id += 1
            srv = {
                "id": sid,
                "name": payload.get("name"),
                "status": "running",
                "public_net": {"ipv4": {"ip": "198.51.100.%d" % sid}},
                "user_data": payload.get("user_data"),
                "server_type": payload.get("server_type"),
            }
            _FakeHcloudServer.created[sid] = srv
            self._send(200, {"server": srv})
        else:
            self._send(404, {"error": {"code": "not_found"}})

    def do_GET(self) -> None:  # noqa: N802
        if not self._auth():
            self._send(401, {"error": {"code": "unauthorized"}}); return
        m = re.fullmatch(r"/v1/servers/(\d+)", self.path.rstrip("/"))
        if m:
            sid = int(m.group(1))
            srv = _FakeHcloudServer.created.get(sid)
            if srv:
                self._send(200, {"server": srv})
            else:
                self._send(404, {"error": {"code": "not_found"}})
            return
        self._send(404, {"error": {"code": "not_found"}})

    def do_DELETE(self) -> None:  # noqa: N802
        if not self._auth():
            self._send(401, {"error": {"code": "unauthorized"}}); return
        m = re.fullmatch(r"/v1/servers/(\d+)", self.path.rstrip("/"))
        if m:
            _FakeHcloudServer.created.pop(int(m.group(1)), None)
            self._send(204, {})
            return
        self._send(404, {"error": {"code": "not_found"}})

    def log_message(self, fmt: str, *args: object) -> None:
        pass


def _boot_admin(mod, db_path: Path):
    db = mod.LiorgDb(db_path)
    now = mod.utc_now()
    org_id = "org_e2e"
    db.execute(
        "INSERT INTO organizations (id, name, slug, edition, created_at, plan) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (org_id, "E2E Co", "e2e", "cloud-paid", now, "cloud-paid"),
    )
    db.execute(
        "INSERT INTO users (id, email, password_hash, created_at, email_verified) "
        "VALUES (?, ?, ?, ?, 1)",
        ("u_owner", "owner@e2e.c", mod.hash_password("pw"), now),
    )
    db.execute(
        "INSERT INTO members (org_id, user_id, role, created_at) VALUES (?, ?, ?, ?)",
        (org_id, "u_owner", "owner", now),
    )
    mod.LiorgHandler.db = db
    mod.LiorgHandler.jwt_secret = "e2e-jwt-secret"
    server = ThreadingHTTPServer(("127.0.0.1", 0), mod.LiorgHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return mod, db, server


def _req(method: str, base: str, path: str, body=None, token=None):
    data = json.dumps(body).encode() if body is not None else None
    hdrs = {}
    if token:
        hdrs["Authorization"] = "Bearer " + token
    if data is not None:
        hdrs["Content-Type"] = "application/json"
    req = urllib.request.Request(base + path, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=10) as res:
            raw = res.read().decode() or "{}"
            return res.status, json.loads(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode() or "{}"
        try:
            parsed = json.loads(raw)
        except ValueError:
            parsed = raw
        return exc.code, parsed


class TestHostProvisioningE2E(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_server()
        self._tmp = tempfile.TemporaryDirectory()
        self._fake = ThreadingHTTPServer(("127.0.0.1", 0), _FakeHcloudServer)
        self._hcloud_url = "http://127.0.0.1:%d/v1" % self._fake.server_port
        _FakeHcloudServer.created = {}
        _FakeHcloudServer.next_id = 1
        threading.Thread(target=self._fake.serve_forever, daemon=True).start()
        self._old_env = dict(os.environ)
        os.environ.update(
            {
                "LIBREBASE_HETZNER_API_TOKEN": "test-hetzner-token",
                "LIBREBASE_HETZNER_API_URL": self._hcloud_url,
                "LIBREBASE_HETZNER_IMAGE_ID": "",
                "LIBREBASE_HETZNER_SSH_KEY_ID": "",
                "LIBREBASE_HETZNER_SERVER_TYPE": "cx22",
            }
        )
        self._old_modules = dict(os.environ)  # keep reference
        self.mod, self.db, self.server = _boot_admin(self.mod, Path(self._tmp.name) / "e2e.db")
        self.base = "http://127.0.0.1:%d" % self.server.server_port

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self._fake.shutdown()
        self._fake.server_close()
        self.mod.LiorgHandler.db = None
        self.mod.LiorgHandler.jwt_secret = None
        os.environ.clear()
        os.environ.update(self._old_env)
        self.db.close()
        self._tmp.cleanup()

    def _token(self) -> str:
        return self.mod.issue_session(
            self.db, "e2e-jwt-secret", "u_owner", "org_e2e", "owner", "cloud-paid"
        )[0]

    def test_rent_register_provision_teardown(self) -> None:
        token = self._token()
        # 1) Rent a VM on Hetzner (real hcloud client -> fake API).
        st, host = _req(
            "POST",
            self.base,
            "/org/v1/orgs/org_e2e/hosts",
            {"name": "e2e-vm", "provider": "hetzner", "region": "nbg1", "memMb": 1024},
            token=token,
        )
        self.assertEqual(st, 201)
        self.assertEqual(host["serverId"], 1)
        self.assertEqual(host["ip"], "198.51.100.1")
        self.assertEqual(host["status"], "provisioning")
        self.assertIn(1, _FakeHcloudServer.created)
        user_data = _FakeHcloudServer.created[1].get("user_data") or ""
        self.assertIn("#cloud-config", user_data)
        self.assertIn("librebase-host-agent", user_data)

        # 2) The host agent (this test) reads its cloud-init token and registers.
        m = re.search(r"LIBREBASE_AGENT_TOKEN=(\S+)", user_data)
        self.assertIsNotNone(m)
        agent_token = m.group(1)
        st, reg = _req(
            "POST",
            self.base,
            "/org/v1/host-agent/register",
            {"ip": "198.51.100.1"},
            token=agent_token,
        )
        self.assertEqual(st, 200)
        self.assertEqual(reg["status"], "running")

        # 3) GET host now reports running (no hcloud get needed; agent set it).
        st, host2 = _req(
            self.base, "/org/v1/orgs/org_e2e/hosts", token=token
        ) if False else _req("GET", self.base, "/org/v1/orgs/org_e2e/hosts", token=token)
        self.assertEqual(st, 200)
        self.assertEqual(host2[0]["status"], "running")
        self.assertEqual(host2[0]["ip"], "198.51.100.1")

        # 4) Delete the host -> fake Hetzner server removed + row deleted.
        import urllib.request as _ur

        req = _ur.Request(
            self.base + "/org/v1/orgs/org_e2e/hosts/%s" % host["id"],
            method="DELETE",
            headers={"Authorization": "Bearer " + token},
        )
        with _ur.urlopen(req, timeout=10) as res:
            self.assertEqual(res.status, 200)
        self.assertNotIn(1, _FakeHcloudServer.created)


if __name__ == "__main__":
    unittest.main()
