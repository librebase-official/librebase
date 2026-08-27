"""Unit tests for the Librebase host agent (host-agent/service.py).

Podman and admin HTTP are mocked — no network, no containers required.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / "host-agent" / "service.py"


def load_agent():
    spec = importlib.util.spec_from_file_location("librebase_host_agent", AGENT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["librebase_host_agent"] = module
    spec.loader.exec_module(module)
    return module


def inst(iid: str, api: int = 54320, pg: int = 54322, data_dir: str = "/d") -> dict:
    return {
        "id": iid,
        "name": "inst-" + iid,
        "ports": {"api": api, "postgres": pg},
        "dataDir": data_dir,
        "runtimeTarget": "local",
    }


class TestHostAgent(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_agent()
        old_env = dict(os.environ)
        os.environ.update(
            {
                "LIBREBASE_HOST_ID": "host_test",
                "LIBREBASE_AGENT_TOKEN": "tok",
                "LIBREBASE_AGENT_RECONCILE_SECONDS": "1",
                "LIBREBASE_AGENT_HEARTBEAT_SECONDS": "1",
            }
        )
        self._old_env = old_env
        # Patch I/O seams.
        self._req_calls: list[tuple[str, str, dict | None]] = []
        self._run_calls: list[dict] = []
        self._rm_calls: list[str] = []
        self._running = set()
        self.mod._req = self._fake_req  # type: ignore[assignment]
        self.mod._podman_run = self._fake_run  # type: ignore[assignment]
        self.mod._podman_rm = self._fake_rm  # type: ignore[assignment]
        self.mod._running_containers = self._fake_running  # type: ignore[assignment]
        self.mod._detect_ip = lambda: "198.51.100.9"  # type: ignore[assignment]

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self._old_env)

    def _fake_req(self, method, path, body=None):
        self._req_calls.append((method, path, body))
        if method == "GET" and path.endswith("/instances"):
            return 200, self._instances
        if method == "POST" and path.endswith("/register"):
            return 200, {"status": "running"}
        if method == "POST" and path.endswith("/heartbeat"):
            return 200, {"ok": True}
        return 404, {}

    def _fake_run(self, instance):
        self._run_calls.append(instance)
        name = self.mod.container_name(instance["id"])
        self._running.add(name)
        return True, ""

    def _fake_rm(self, name):
        self._rm_calls.append(name)
        self._running.discard(name)
        return True, ""

    def _fake_running(self):
        return set(self._running)

    def test_container_name_sanitized(self) -> None:
        self.assertEqual(self.mod.container_name("inst_abc-1"), "librebase-inst_abc-1")
        self.assertEqual(len(self.mod.container_name("i" * 200)), 64 + len("librebase-"))

    def test_reconcile_starts_missing_container(self) -> None:
        self._instances = [inst("i1")]
        out = self.mod.reconcile()
        self.assertEqual(out["started"], 1)
        self.assertEqual(out["stopped"], 0)
        self.assertEqual(len(self._run_calls), 1)

    def test_reconcile_skips_already_running(self) -> None:
        self._instances = [inst("i1"), inst("i2")]
        # Both already running.
        self._running = {self.mod.container_name("i1"), self.mod.container_name("i2")}
        out = self.mod.reconcile()
        self.assertEqual(out["started"], 0)
        self.assertEqual(out["stopped"], 0)

    def test_reconcile_stops_orphaned_container(self) -> None:
        self._instances = []  # nothing desired
        self._running = {"librebase-i3"}  # stale from a deleted instance
        out = self.mod.reconcile()
        self.assertEqual(out["stopped"], 1)
        self.assertEqual(self._rm_calls, ["librebase-i3"])

    def test_reconcile_full_cycle(self) -> None:
        self._instances = [inst("i1")]
        self._running = {"librebase-orphan"}
        out = self.mod.reconcile()
        self.assertEqual(out["started"], 1)  # i1 not running -> start
        self.assertEqual(out["stopped"], 1)  # orphan -> remove
        self.assertIn(self.mod.container_name("i1"), self._running)

    def test_register_posts_bearer_and_host_id(self) -> None:
        self._instances = []
        ok = self.mod.register()
        self.assertTrue(ok)
        method, path, body = self._req_calls[-1]
        self.assertEqual(method, "POST")
        self.assertEqual(path, "/org/v1/host-agent/register")
        self.assertEqual(body, {"hostId": "host_test", "ip": "198.51.100.9"})

    def test_register_without_token_fails(self) -> None:
        del os.environ["LIBREBASE_AGENT_TOKEN"]
        self.assertFalse(self.mod.register())

    def test_loop_once_runs_heartbeat_and_reconcile(self) -> None:
        self._instances = [inst("i1")]
        self.mod.loop(once=True)
        # Expect at least a heartbeat POST and a GET instances.
        methods = [c[0] for c in self._req_calls]
        self.assertIn("POST", methods)
        self.assertIn("GET", methods)


if __name__ == "__main__":
    unittest.main()
