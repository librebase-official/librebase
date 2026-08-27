"""Unit tests for the Hetzner Cloud substrate (hcloud.py).

Uses a tiny fake Hetzner Cloud HTTP server (stdlib) — no network. Mirrors the
FakeStripe pattern from test_admin_api.py.
"""

from __future__ import annotations

import importlib.util
import json
import os
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "admin-api" / "scripts"


def load_hcloud():
    spec = importlib.util.spec_from_file_location("hcloud", SCRIPTS / "hcloud.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeHcloud(BaseHTTPRequestHandler):
    """Stateful fake Hetzner Cloud (servers CRUD)."""

    created: dict[int, dict] = {}

    def _send(self, code: int, obj: object) -> None:
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _require_auth(self) -> bool:
        return self.headers.get("Authorization") == "Bearer test-token"

    def do_POST(self) -> None:  # noqa: N802
        if not self._require_auth():
            self._send(401, {"error": {"code": "unauthorized"}}); return
        if self.path == "/v1/servers":
            raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            payload = json.loads(raw or b"{}")
            sid = int((payload.get("name", "x").split("-")[-1]) or 0) or 1
            srv = {
                "id": sid,
                "name": payload.get("name"),
                "status": "running",
                "public_net": {"ipv4": {"ip": f"192.0.2.{sid}"}},
            }
            _FakeHcloud.created[sid] = srv
            self._send(200, {"server": srv})
        else:
            self._send(404, {"error": {"code": "not_found"}})

    def do_GET(self) -> None:  # noqa: N802
        if not self._require_auth():
            self._send(401, {"error": {"code": "unauthorized"}}); return
        parts = self.path.rstrip("/").split("/")
        if len(parts) >= 4 and parts[1] == "v1" and parts[2] == "servers":
            sid = int(parts[3])
            srv = _FakeHcloud.created.get(sid)
            if srv:
                self._send(200, {"server": srv})
            else:
                self._send(404, {"error": {"code": "not_found"}})
            return
        self._send(404, {"error": {"code": "not_found"}})

    def do_DELETE(self) -> None:  # noqa: N802
        if not self._require_auth():
            self._send(401, {"error": {"code": "unauthorized"}}); return
        parts = self.path.rstrip("/").split("/")
        if len(parts) >= 4 and parts[1] == "v1" and parts[2] == "servers":
            sid = int(parts[3])
            _FakeHcloud.created.pop(sid, None)
            self._send(204, {})
            return
        self._send(404, {"error": {"code": "not_found"}})

    def log_message(self, fmt: str, *args: object) -> None:  # silence
        pass


class TestHcloud(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_hcloud()
        _FakeHcloud.created = {}
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeHcloud)
        self._base = f"http://127.0.0.1:{self.server.server_port}/v1"
        self._old = dict(os.environ)
        os.environ.update({
            "LIBREBASE_HETZNER_API_TOKEN": "test-token",
            "LIBREBASE_HETZNER_API_URL": self._base,
            "LIBREBASE_HETZNER_SSH_KEY_ID": "",
            "LIBREBASE_HETZNER_IMAGE_ID": "",
            "LIBREBASE_HETZNER_SERVER_TYPE": "",
        })
        self._thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self._thread.start()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._old)
        self.server.shutdown()
        self.server.server_close()

    def test_configured_and_helpers(self) -> None:
        self.assertTrue(self.mod.hcloud_configured())
        self.assertEqual(self.mod.hcloud_base(), self._base)
        self.assertEqual(self.mod.hcloud_server_type(), "cx23")

    def test_create_server_returns_id_ip(self) -> None:
        out = self.mod.create_server(name="lb-host-1", region="nbg1", user_data="#cloud-config\n")
        self.assertEqual(out["server_id"], 1)
        self.assertEqual(out["ip"], "192.0.2.1")
        self.assertEqual(out["status"], "running")

    def test_get_server_normalizes_ip(self) -> None:
        self.mod.create_server(name="lb-host-7", region="nbg1")
        info = self.mod.get_server(7)
        self.assertEqual(info["status"], "running")
        self.assertEqual(info["ip"], "192.0.2.7")
        self.assertEqual(info["name"], "lb-host-7")

    def test_delete_server(self) -> None:
        self.mod.create_server(name="lb-host-3", region="nbg1")
        self.assertIsNotNone(_FakeHcloud.created.get(3))
        self.mod.delete_server(3)
        self.assertNotIn(3, _FakeHcloud.created)

    def test_cloudinit_contains_token_and_host_id(self) -> None:
        cfg = self.mod.render_cloudinit("host_abc", "tok-123")
        self.assertIn("host_abc", cfg)
        self.assertIn("tok-123", cfg)
        self.assertIn("librebase-host-agent", cfg)
        self.assertIn("#cloud-config", cfg)

    def test_bad_credentials_raise_hcloud_error(self) -> None:
        os.environ["LIBREBASE_HETZNER_API_TOKEN"] = "wrong"
        with self.assertRaises(self.mod.HcloudError):
            self.mod.get_server(1)


if __name__ == "__main__":
    unittest.main()
