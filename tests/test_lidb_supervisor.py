"""Tests for scripts/lidb_supervisor.py — persistent LiDB HTTP supervisor."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest import mock

# Add scripts to path
REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "scripts"
sys.path.insert(0, str(SCRIPTS))

import lidb_supervisor as sup


def _embed_available() -> bool:
    """Check if lidb-engine is available on the system."""
    embed = sup.shutil.which("lidb-engine")
    if embed:
        return True
    for candidate in (
        "/usr/local/bin/lidb-engine",
        "/opt/li/lidb/build/lidb-engine",
    ):
        if Path(candidate).is_file():
            return True
    return False


EMBED_AVAILABLE = _embed_available()
SKIP_REASON = "lidb-engine not available" if not EMBED_AVAILABLE else None


class TestLidbSupervisorUnit(unittest.TestCase):
    """Unit tests that don't require lidb-engine."""

    def test_ddl_regex(self):
        self.assertRegex("CREATE TABLE foo (id INT)", sup._DDL_RE)
        self.assertRegex("INSERT INTO foo VALUES (1)", sup._DDL_RE)
        self.assertRegex("UPDATE foo SET x=1", sup._DDL_RE)
        self.assertRegex("DELETE FROM foo", sup._DDL_RE)
        self.assertNotRegex("SELECT * FROM foo", sup._DDL_RE)

    def test_select_regex(self):
        self.assertRegex("SELECT 1", sup._SELECT_RE)
        self.assertRegex("select * from foo", sup._SELECT_RE)
        self.assertNotRegex("INSERT INTO foo", sup._SELECT_RE)

    def test_table_regex(self):
        m = sup._TABLE_RE.match("CREATE TABLE IF NOT EXISTS todos (id INT)")
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "todos")

    def test_find_embed_missing(self):
        """_find_embed raises when no binary found."""
        old = sup._EMBED
        sup._EMBED = None
        try:
            with mock.patch("shutil.which", return_value=None):
                with mock.patch.dict(os.environ, {"LIDB_ENGINE": ""}, clear=False):
                    with self.assertRaises(RuntimeError):
                        sup._find_embed()
        finally:
            sup._EMBED = old

    def test_handler_health(self):
        """SupervisorHandler responds to /health."""
        with tempfile.TemporaryDirectory() as td:
            sup._DATA_DIR = td
            sup._APP_NAME = "test"
            sup._EMBED = None  # Don't need embed for health check

            server = ThreadingHTTPServer(("127.0.0.1", 0), sup.SupervisorHandler)
            port = server.server_address[1]
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            try:
                resp = urllib.request.urlopen(f"http://127.0.0.1:{port}/health")
                data = json.loads(resp.read())
                self.assertEqual(data["status"], "running")
                self.assertEqual(data["app"], "test")
                self.assertEqual(data["runtime_mode"], "lidb")
            finally:
                server.shutdown()

    def test_handler_404(self):
        """SupervisorHandler returns 404 for unknown paths."""
        with tempfile.TemporaryDirectory() as td:
            sup._DATA_DIR = td
            sup._APP_NAME = "test"

            server = ThreadingHTTPServer(("127.0.0.1", 0), sup.SupervisorHandler)
            port = server.server_address[1]
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            try:
                req = urllib.request.Request(f"http://127.0.0.1:{port}/unknown")
                try:
                    urllib.request.urlopen(req)
                    self.fail("Expected 404")
                except urllib.error.HTTPError as e:
                    self.assertEqual(e.code, 404)
            finally:
                server.shutdown()


@unittest.skipUnless(EMBED_AVAILABLE, SKIP_REASON)
class TestLidbSupervisorIntegration(unittest.TestCase):
    """Integration tests requiring lidb-engine."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="lidb-test-")
        self._orig_data = sup._DATA_DIR
        self._orig_app = sup._APP_NAME
        self._orig_embed = sup._EMBED
        sup._DATA_DIR = self.tmpdir
        sup._APP_NAME = "test"
        sup._EMBED = None  # Let it re-discover
        # Reset the module-level engine state
        sup._LIDB_ENGINE = None

    def tearDown(self):
        sup._DATA_DIR = self._orig_data
        sup._APP_NAME = self._orig_app
        sup._EMBED = self._orig_embed
        sup._LIDB_ENGINE = None
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_ensure_database(self):
        result = sup.ensure_database()
        self.assertTrue(result)
        self.assertTrue(Path(self.tmpdir, ".lidb", "catalog.heap").is_file())

    def test_create_and_select(self):
        sup.ensure_database()
        r1 = sup.execute_sql("CREATE TABLE IF NOT EXISTS test_tbl (id INTEGER PRIMARY KEY, val TEXT)")
        self.assertTrue(r1["ok"])

        r2 = sup.execute_sql("INSERT INTO test_tbl VALUES (1, 'hello')")
        self.assertTrue(r2["ok"])

        r3 = sup.execute_sql("SELECT * FROM test_tbl")
        self.assertTrue(r3["ok"])
        self.assertEqual(len(r3["rows"]), 1)
        self.assertEqual(r3["rows"][0]["val"], "hello")

    def test_persistence_across_calls(self):
        sup.ensure_database()
        sup.execute_sql("CREATE TABLE IF NOT EXISTS persist (id INTEGER PRIMARY KEY, data TEXT)")
        sup.execute_sql("INSERT INTO persist VALUES (42, 'test')")

        # Simulate a new request by calling execute_sql again
        result = sup.execute_sql("SELECT * FROM persist")
        self.assertTrue(result["ok"])
        self.assertEqual(len(result["rows"]), 1)
        self.assertEqual(result["rows"][0]["data"], "test")

    def test_http_server_full_cycle(self):
        """Start server, create table, insert, select via HTTP."""
        server = ThreadingHTTPServer(("127.0.0.1", 0), sup.SupervisorHandler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        try:
            base = f"http://127.0.0.1:{port}"

            # Health
            resp = json.loads(urllib.request.urlopen(f"{base}/health").read())
            self.assertEqual(resp["status"], "running")

            # Create table
            body = json.dumps({"sql": "CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, name TEXT)"}).encode()
            req = urllib.request.Request(f"{base}/v1/sql", data=body, method="POST",
                                        headers={"Content-Type": "application/json"})
            resp = json.loads(urllib.request.urlopen(req).read())
            self.assertTrue(resp["ok"])

            # Insert
            body = json.dumps({"sql": "INSERT INTO items VALUES (1, 'widget')"}).encode()
            req = urllib.request.Request(f"{base}/v1/sql", data=body, method="POST",
                                        headers={"Content-Type": "application/json"})
            resp = json.loads(urllib.request.urlopen(req).read())
            self.assertTrue(resp["ok"])

            # Select
            body = json.dumps({"sql": "SELECT * FROM items"}).encode()
            req = urllib.request.Request(f"{base}/v1/sql", data=body, method="POST",
                                        headers={"Content-Type": "application/json"})
            resp = json.loads(urllib.request.urlopen(req).read())
            self.assertTrue(resp["ok"])
            self.assertEqual(len(resp["rows"]), 1)
            self.assertEqual(resp["rows"][0]["name"], "widget")
        finally:
            server.shutdown()


if __name__ == "__main__":
    unittest.main()
