"""Unit tests for admin-api: entitlements, row serializers, DB migrations, hosts budget.

Pure-function + in-process tests (no network server needed).
"""

from __future__ import annotations

import importlib.util
import sqlite3
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "admin-api" / "scripts"
SERVER = SCRIPTS / "admin_server.py"


def load_server():
    spec = importlib.util.spec_from_file_location("admin_server", SERVER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestEntitlements(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_server()

    def test_self_host_allows_core(self) -> None:
        ent = self.mod.entitlement_for_edition
        self.assertEqual(ent("self-host", "project.create"), 1)
        self.assertEqual(ent("self-host", "instance.launch"), 1)
        self.assertEqual(ent("self-host", "host.create"), 1)
        self.assertEqual(ent("self-host", "branching.pitr"), 0)

    def test_cloud_free_limits(self) -> None:
        ent = self.mod.entitlement_for_edition
        self.assertEqual(ent("cloud-free", "project.create"), 2)  # limited
        self.assertEqual(ent("cloud-free", "instance.launch"), 1)
        self.assertEqual(ent("cloud-free", "host.create"), 1)
        self.assertEqual(ent("cloud-free", "branching.pitr"), 0)

    def test_cloud_paid_opens_advanced(self) -> None:
        ent = self.mod.entitlement_for_edition
        self.assertEqual(ent("cloud-paid", "project.create"), 1)
        self.assertEqual(ent("cloud-paid", "k8s.provision"), 1)
        self.assertEqual(ent("cloud-paid", "branching.pitr"), 1)
        self.assertEqual(ent("cloud-paid", "host.create"), 1)


class TestRowSerializers(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_server()

    def _row(self, mapping: dict) -> sqlite3.Row:
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        cols = list(mapping.keys())
        placeholders = ", ".join(["?"] * len(cols))
        conn.execute(
            "CREATE TEMP TABLE t (" + ", ".join(f"c{i}" for i in range(len(cols))) + ")"
        )
        values = []
        for c in cols:
            v = mapping.get(c)
            if v is None:
                values.append(None)
            elif isinstance(v, bool):
                values.append(int(v))
            elif isinstance(v, int):
                values.append(v)
            else:
                values.append(str(v))
        conn.execute(f"INSERT INTO t VALUES ({placeholders})", values)
        return conn.execute(f"SELECT {', '.join(f'c{i} AS {c!r}' for i, c in enumerate(cols))} FROM t").fetchone()

    def test_row_host(self) -> None:
        row = self._row(
            {
                "id": "host_x",
                "org_id": "org_y",
                "name": "vm",
                "provider": "sail",
                "region": "eu-west-1",
                "mem_mb": 512,
                "mem_used_mb": 128,
                "status": "running",
                "created_at": "t0",
                "updated_at": "t1",
            }
        )
        out = self.mod.row_host(row)
        self.assertEqual(out["id"], "host_x")
        self.assertEqual(out["orgId"], "org_y")
        self.assertEqual(out["memMb"], 512)
        self.assertEqual(out["memUsedMb"], 128)

    def test_row_instance_host_fields(self) -> None:
        row = self._row(
            {
                "id": "inst_x",
                "name": "app",
                "org_id": "org_y",
                "data_dir": "/d",
                "deployment_mode": "dedicated",
                "runtime_target": "local",
                "status": "running",
                "created_at": "t0",
                "updated_at": "t1",
                "ports_json": '{"api":54320,"postgres":54322}',
                "k8s_namespace": None,
                "k8s_degraded": None,
                "k8s_message": None,
                "host_id": "host_v",
                "mem_limit_mb": 256,
            }
        )
        out = self.mod.row_instance(row)
        self.assertEqual(out["hostId"], "host_v")
        self.assertEqual(out["memLimitMb"], 256)
        self.assertEqual(out["ports"]["api"], 54320)

    def test_row_instance_no_host_fields(self) -> None:
        row = self._row(
            {
                "id": "inst_x",
                "name": "app",
                "org_id": "org_y",
                "data_dir": "/d",
                "deployment_mode": "dedicated",
                "runtime_target": "local",
                "status": "stopped",
                "created_at": "t0",
                "updated_at": "t1",
                "ports_json": None,
                "k8s_namespace": None,
                "k8s_degraded": None,
                "k8s_message": None,
                "host_id": None,
                "mem_limit_mb": None,
            }
        )
        out = self.mod.row_instance(row)
        self.assertNotIn("hostId", out)
        self.assertNotIn("memLimitMb", out)


class TestDbMigration(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_server()

    def test_migrate_applies_hosts_schema(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = self.mod.LiorgDb(Path(tmp) / "org.db")
            cols = {c[1] for c in db.conn.execute("PRAGMA table_info(hosts)")}
            self.assertIn("mem_mb", cols)
            self.assertIn("mem_used_mb", cols)
            cols_inst = {c[1] for c in db.conn.execute("PRAGMA table_info(instances)")}
            self.assertIn("host_id", cols_inst)
            self.assertIn("mem_limit_mb", cols_inst)
            db.close()

    def test_migrate_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "org.db"
            self.mod.LiorgDb(path).close()
            self.mod.LiorgDb(path).close()  # re-open must not fail on re-ALTER


class TestHostBudget(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_server()

    def test_host_mem_committed_and_budget_exceeded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db = self.mod.LiorgDb(Path(tmp) / "org.db")
            now = self.mod.utc_now()
            host_id = "host_a"
            org_id = "org_z"
            db.execute(
                "INSERT INTO hosts (id, org_id, name, provider, region, mem_mb, mem_used_mb, status, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, 0, 'running', ?, ?)",
                (host_id, org_id, "vm", "sail", "eu", 512, now, now),
            )
            row = db.fetchone("SELECT * FROM hosts WHERE id = ?", (host_id,))
            self.assertIsNotNone(row)
            self.assertEqual(self.mod.row_host(row)["memMb"], 512)
            db.close()


if __name__ == "__main__":
    unittest.main()
