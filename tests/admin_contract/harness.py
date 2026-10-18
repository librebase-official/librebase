from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "admin-api" / "scripts"
PY_SERVER = SCRIPTS / "admin_server.py"
LI_BIN = ROOT / "admin-api" / "li" / "build" / "admin_server"


def http_json(method: str, url: str, body: dict | None = None, token: str | None = None):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            raw = res.read().decode()
            return res.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            payload = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            payload = {"raw": raw}
        return e.code, payload


class AdminServer:
    def __init__(self, runtime: str | None = None, port: int = 54341):
        self.runtime = (runtime or os.environ.get("LIBREBASE_ADMIN_RUNTIME", "python")).lower()
        self.port = port
        self.base_url = f"http://127.0.0.1:{port}"
        self._proc: subprocess.Popen | None = None
        self._tmpdir: tempfile.TemporaryDirectory | None = None

    def __enter__(self) -> "AdminServer":
        self._tmpdir = tempfile.TemporaryDirectory(prefix="lb-admin-contract-")
        db = Path(self._tmpdir.name) / "org.db"
        env = {
            **os.environ,
            "LIBREBASE_ADMIN_BIND": "127.0.0.1",
            "LIBREBASE_ADMIN_PORT": str(self.port),
            "LIBREBASE_ADMIN_DB_PATH": str(db),
            "LIBREBASE_ADMIN_JWT_SECRET": "contract-test-secret",
        }
        if self.runtime == "python":
            cmd = [sys.executable, str(PY_SERVER)]
        elif self.runtime == "li":
            if not LI_BIN.is_file():
                unittest_skip_li()
            cmd = [str(LI_BIN)]
        else:
            raise ValueError(f"unknown runtime {self.runtime!r}")
        self._proc = subprocess.Popen(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            deadline = time.time() + 8
            while time.time() < deadline:
                try:
                    st, body = http_json("GET", f"{self.base_url}/health")
                    if st == 200 and body.get("ok") is True:
                        return self
                except Exception:
                    time.sleep(0.1)
            err = self._proc.stderr.read().decode() if self._proc.stderr else ""
            raise RuntimeError(f"admin {self.runtime} failed to become healthy: {err}")
        except BaseException:
            if self._proc and self._proc.poll() is None:
                self._proc.terminate()
                try:
                    self._proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self._proc.kill()
            if self._proc and self._proc.stderr is not None and not self._proc.stderr.closed:
                self._proc.stderr.close()
            raise

    def __exit__(self, *args) -> None:
        if self._proc:
            if self._proc.poll() is None:
                self._proc.terminate()
                try:
                    self._proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self._proc.kill()
                    self._proc.wait(timeout=3)
            if self._proc.stderr is not None and not self._proc.stderr.closed:
                self._proc.stderr.close()
        if self._tmpdir:
            self._tmpdir.cleanup()


def unittest_skip_li():
    import unittest

    raise unittest.SkipTest("Li admin_server binary missing; build admin-api/li first")
