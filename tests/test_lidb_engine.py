"""Tests for scripts/lidb_engine.py dev runtime and port probe logic."""

from __future__ import annotations

import importlib.util
import json
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
ENGINE = SCRIPTS / "lidb_engine.py"
DEV_STUB = SCRIPTS / "dev_runtime_stub.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def run_engine(
    command: str,
    data_dir: str,
    api_port: int,
    postgres_port: int,
    env: dict[str, str] | None = None,
) -> tuple[int, dict]:
    merged = {**os.environ, **(env or {})}
    result = subprocess.run(
        [
            sys.executable,
            str(ENGINE),
            command,
            "--data-dir",
            data_dir,
            "--api-port",
            str(api_port),
            "--postgres-port",
            str(postgres_port),
        ],
        capture_output=True,
        text=True,
        env=merged,
        check=False,
    )
    payload = json.loads(result.stdout.strip())
    return result.returncode, payload


class LidbEngineStatusTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = self._tmp.name
        self._env_patch = {
            "LIDB_ROOT": "",
            "LIDB_RUNTIME_MODE": "",
        }

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_unavailable_without_lidb_root_or_dev_mode(self) -> None:
        api_port = free_port()
        pg_port = free_port()
        code, payload = run_engine(
            "status",
            self.data_dir,
            api_port,
            pg_port,
            env={"LIDB_ROOT": "", "LIDB_RUNTIME_MODE": ""},
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["status"], "stopped")
        self.assertEqual(payload["runtime_mode"], "unavailable")
        self.assertFalse(payload["running"])
        self.assertTrue(payload["degraded"])

    def test_dev_mode_stopped_when_ports_closed(self) -> None:
        api_port = free_port()
        pg_port = free_port()
        code, payload = run_engine(
            "status",
            self.data_dir,
            api_port,
            pg_port,
            env={"LIDB_RUNTIME_MODE": "dev", "LIDB_ROOT": ""},
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["runtime_mode"], "dev")
        self.assertEqual(payload["status"], "stopped")
        self.assertFalse(payload["running"])

    def test_dev_mode_running_when_ports_open(self) -> None:
        api_port = free_port()
        pg_port = free_port()
        proc = subprocess.Popen(
            [
                sys.executable,
                str(DEV_STUB),
                "--data-dir",
                self.data_dir,
                "--api-port",
                str(api_port),
                "--postgres-port",
                str(pg_port),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            for _ in range(30):
                code, payload = run_engine(
                    "status",
                    self.data_dir,
                    api_port,
                    pg_port,
                    env={"LIDB_RUNTIME_MODE": "dev", "LIDB_ROOT": ""},
                )
                if payload.get("running"):
                    break
                time.sleep(0.1)
            else:
                self.fail("dev stub never opened ports")

            self.assertEqual(code, 0)
            self.assertEqual(payload["status"], "running")
            self.assertEqual(payload["runtime_mode"], "dev")
            self.assertTrue(payload["running"])
            self.assertTrue(payload["api_reachable"])
            self.assertTrue(payload["postgres_reachable"])
        finally:
            proc.terminate()
            proc.wait(timeout=5)

    def test_ensure_dev_exits_zero_when_running(self) -> None:
        api_port = free_port()
        pg_port = free_port()
        code, payload = run_engine(
            "ensure",
            self.data_dir,
            api_port,
            pg_port,
            env={"LIDB_RUNTIME_MODE": "dev", "LIDB_ROOT": ""},
        )
        self.assertEqual(code, 0)
        self.assertEqual(payload["status"], "running")
        self.assertTrue(payload["running"])
        self.assertTrue(payload.get("launch_ok"))
        self.assertEqual(payload["runtime_mode"], "dev")


class PortProbeTests(unittest.TestCase):
    def test_port_open_detects_listener(self) -> None:
        engine = load_module("lidb_engine", ENGINE)
        port = free_port()

        def serve() -> None:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("127.0.0.1", port))
            sock.listen(1)
            conn, _ = sock.accept()
            conn.close()
            sock.close()

        thread = threading.Thread(target=serve, daemon=True)
        thread.start()
        time.sleep(0.05)
        self.assertTrue(engine._port_open("127.0.0.1", port))
        thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
