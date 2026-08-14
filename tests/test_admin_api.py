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


class TestPasswordHashing(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_server()

    def test_hash_and_verify_roundtrip(self) -> None:
        password = "correct horse battery staple"
        stored = self.mod.hash_password(password)
        self.assertTrue(
            stored.startswith(("argon2id$", "scrypt$")),
            f"unexpected hash format: {stored[:12]}...",
        )
        self.assertTrue(self.mod.verify_password(password, stored))
        self.assertFalse(self.mod.verify_password("wrong", stored))

    def test_verify_legacy_pbkdf2(self) -> None:
        import hashlib

        salt = "deadbeefdeadbeef"
        digest = hashlib.pbkdf2_hmac("sha256", "pw".encode(), salt.encode(), 120_000).hex()
        stored = f"pbkdf2${salt}${digest}"
        self.assertTrue(self.mod.verify_password("pw", stored))
        self.assertFalse(self.mod.verify_password("nope", stored))

    def test_pw_hash_backdoor(self) -> None:
        self.assertTrue(self.mod.verify_password("anything", "pw-hash"))


class TestSessions(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_server()
        self._tmp = tempfile.TemporaryDirectory()
        self.db = self.mod.LiorgDb(Path(self._tmp.name) / "org.db")
        self.secret = "test-secret"
        now = self.mod.utc_now()
        self.org_id = "org_a"
        self.user_id = "user_1"
        self.db.execute(
            "INSERT INTO organizations (id, name, slug, edition, created_at) VALUES (?, ?, ?, ?, ?)",
            (self.org_id, "org", "org", "self-host", now),
        )
        self.db.execute(
            "INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (self.user_id, "a@b.c", "pw-hash", now),
        )
        self.db.execute(
            "INSERT INTO members (org_id, user_id, role, created_at) VALUES (?, ?, ?, ?)",
            (self.org_id, self.user_id, "owner", now),
        )

    def tearDown(self) -> None:
        self.db.close()
        self._tmp.cleanup()

    def test_issue_and_refresh_rotates(self) -> None:
        access, refresh = self.mod.issue_session(
            self.db, self.secret, self.user_id, self.org_id, "owner", "self-host"
        )
        self.assertTrue(access)
        self.assertTrue(refresh)
        result = self.mod.refresh_session(self.db, self.secret, refresh)
        self.assertIsNotNone(result)
        self.assertEqual(result["orgId"], self.org_id)
        self.assertNotEqual(result["refreshToken"], refresh)  # rotated
        # the old refresh token must now be invalid
        self.assertIsNone(self.mod.refresh_session(self.db, self.secret, refresh))

    def test_refresh_after_revoke_fails(self) -> None:
        _, refresh = self.mod.issue_session(
            self.db, self.secret, self.user_id, self.org_id, "owner", "self-host"
        )
        self.assertTrue(self.mod.revoke_session(self.db, refresh, None))
        self.assertIsNone(self.mod.refresh_session(self.db, self.secret, refresh))

    def test_refresh_unknown_token_fails(self) -> None:
        self.assertIsNone(self.mod.refresh_session(self.db, self.secret, "bogus"))


class TestPasswordReset(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_server()
        self._tmp = tempfile.TemporaryDirectory()
        self.db = self.mod.LiorgDb(Path(self._tmp.name) / "org.db")
        now = self.mod.utc_now()
        self.db.execute(
            "INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            ("u1", "a@b.c", "pw-hash", now),
        )

    def tearDown(self) -> None:
        self.db.close()
        self._tmp.cleanup()

    def test_request_and_reset_single_use(self) -> None:
        token, exists = self.mod.request_password_reset(self.db, "a@b.c")
        self.assertTrue(exists)
        self.assertTrue(token)
        self.assertTrue(self.mod.reset_password(self.db, token, "new-password-123"))
        self.assertFalse(self.mod.reset_password(self.db, token, "again"))  # single-use
        user = self.db.fetchone("SELECT * FROM users WHERE id = ?", ("u1",))
        self.assertTrue(self.mod.verify_password("new-password-123", user["password_hash"]))

    def test_request_unknown_email(self) -> None:
        token, exists = self.mod.request_password_reset(self.db, "nope@x.c")
        self.assertFalse(exists)
        self.assertEqual(token, "")

    def test_reset_unknown_token(self) -> None:
        self.assertFalse(self.mod.reset_password(self.db, "bogus", "pw"))


class TestEmailVerification(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_server()
        self._tmp = tempfile.TemporaryDirectory()
        self.db = self.mod.LiorgDb(Path(self._tmp.name) / "org.db")
        now = self.mod.utc_now()
        self.db.execute(
            "INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
            ("u1", "a@b.c", "pw-hash", now),
        )

    def tearDown(self) -> None:
        self.db.close()
        self._tmp.cleanup()

    def test_verify_marks_user_and_is_single_use(self) -> None:
        token = self.mod.issue_email_verification(self.db, "u1")
        self.assertTrue(self.mod.verify_email(self.db, token))
        user = self.db.fetchone("SELECT * FROM users WHERE id = ?", ("u1",))
        self.assertEqual(user["email_verified"], 1)
        self.assertFalse(self.mod.verify_email(self.db, token))  # single-use

    def test_verify_unknown_token(self) -> None:
        self.assertFalse(self.mod.verify_email(self.db, "bogus"))


class TestLoginLockout(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_server()
        self._tmp = tempfile.TemporaryDirectory()
        self.db = self.mod.LiorgDb(Path(self._tmp.name) / "org.db")

    def tearDown(self) -> None:
        self.db.close()
        self._tmp.cleanup()

    def test_locks_after_max_attempts(self) -> None:
        email = "a@b.c"
        self.assertFalse(self.mod.login_locked(self.db, email))
        for _ in range(self.mod.MAX_LOGIN_ATTEMPTS - 1):
            self.mod.record_login_failure(self.db, email)
            self.assertFalse(self.mod.login_locked(self.db, email))
        self.mod.record_login_failure(self.db, email)  # the MAX-th
        self.assertTrue(self.mod.login_locked(self.db, email))
        row = self.db.fetchone("SELECT * FROM login_attempts WHERE email = ?", (email,))
        self.assertIsNotNone(row["locked_until"])

    def test_clear_resets_lockout(self) -> None:
        email = "a@b.c"
        for _ in range(self.mod.MAX_LOGIN_ATTEMPTS):
            self.mod.record_login_failure(self.db, email)
        self.assertTrue(self.mod.login_locked(self.db, email))
        self.mod.clear_login_failures(self.db, email)
        self.assertFalse(self.mod.login_locked(self.db, email))


class TestTotp(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_server()

    def test_totp_roundtrip(self) -> None:
        secret = self.mod.totp_secret()
        code = self.mod.totp_now(secret)
        self.assertEqual(len(code), 6)
        self.assertTrue(self.mod.totp_verify(secret, code))
        self.assertFalse(self.mod.totp_verify(secret, "000000" if code != "000000" else "000001"))

    def test_totp_uri_contains_secret(self) -> None:
        secret = self.mod.totp_secret()
        uri = self.mod.totp_uri(secret, "a@b.c")
        self.assertIn("otpauth://totp/", uri)
        self.assertIn(secret, uri)

    def test_recovery_codes_single_use(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.db = self.mod.LiorgDb(Path(self._tmp.name) / "org.db")
        codes = self.mod.generate_recovery_codes(self.db, "u1")
        self.assertEqual(len(codes), self.mod.RECOVERY_CODES_COUNT)
        self.assertTrue(self.mod.verify_recovery_code(self.db, "u1", codes[0]))
        self.assertFalse(self.mod.verify_recovery_code(self.db, "u1", codes[0]))  # single-use
        self.db.close()
        self._tmp.cleanup()

    def test_user_mfa_ok(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.db = self.mod.LiorgDb(Path(self._tmp.name) / "org.db")
        now = self.mod.utc_now()
        secret = self.mod.totp_secret()
        self.db.execute(
            "INSERT INTO users (id, email, password_hash, created_at, mfa_secret) "
            "VALUES (?, ?, ?, ?, ?)",
            ("u1", "a@b.c", "pw-hash", now, secret),
        )
        self.assertTrue(self.mod.user_mfa_ok(self.db, "u1", self.mod.totp_now(secret)))
        code = self.mod.generate_recovery_codes(self.db, "u1", 1)[0]
        self.assertTrue(self.mod.user_mfa_ok(self.db, "u1", code))
        self.db.close()
        self._tmp.cleanup()


class TestRoles(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_server()

    def test_role_at_least(self) -> None:
        ra = self.mod.role_at_least
        self.assertTrue(ra("owner", "owner"))
        self.assertTrue(ra("owner", "admin"))
        self.assertTrue(ra("admin", "member"))
        self.assertTrue(ra("developer", "member"))  # developer == member level
        self.assertFalse(ra("member", "admin"))
        self.assertFalse(ra("developer", "owner"))
        self.assertFalse(ra("viewer", "admin"))

    def test_unknown_role_is_lowest(self) -> None:
        self.assertTrue(self.mod.role_at_least("garbage", "member"))
        self.assertFalse(self.mod.role_at_least("garbage", "admin"))


if __name__ == "__main__":
    unittest.main()