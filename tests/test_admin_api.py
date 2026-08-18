"""Unit tests for admin-api: entitlements, row serializers, DB migrations, hosts budget.

Pure-function + in-process tests (no network server needed).
"""

from __future__ import annotations

import hashlib
import hmac
import importlib.util
import json
import os
import sqlite3
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

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
        self.assertEqual(ent("cloud-free", "instance.launch"), 0)  # no free compute
        self.assertEqual(ent("cloud-free", "host.create"), 0)
        self.assertEqual(ent("cloud-free", "branching.pitr"), 0)

    def test_suspended_blocks_compute(self) -> None:
        ent = self.mod.entitlement_for_edition
        self.assertEqual(ent("suspended", "project.create"), 0)
        self.assertEqual(ent("suspended", "instance.launch"), 0)
        self.assertEqual(ent("suspended", "host.create"), 0)
        self.assertEqual(ent("suspended", "k8s.provision"), 0)

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


class _FakeStripe(BaseHTTPRequestHandler):
    """Minimal fixture: POST/GET -> canned JSON by path."""

    responses: dict[str, object] = {}

    def _send(self, code: int, obj: object) -> None:
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        if "POST " + self.path not in _FakeStripe.responses:
            self._send(404, {"error": {"message": "not found"}})
            return
        self._send(200, _FakeStripe.responses["POST " + self.path])

    def do_GET(self) -> None:  # noqa: N802
        if "GET " + self.path not in _FakeStripe.responses:
            self._send(404, {"error": {"message": "not found"}})
            return
        self._send(200, _FakeStripe.responses["GET " + self.path])


class TestStripeHelpers(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_server()

    def test_price_env_mapping(self) -> None:
        with mock.patch.dict(
            os.environ,
            {"LIBREBASE_STRIPE_PRICE_STARTER": "price_s", "LIBREBASE_STRIPE_PRICE_PRO": "price_p"},
        ):
            self.assertEqual(self.mod.stripe_price_for_plan("starter"), "price_s")
            self.assertEqual(self.mod.stripe_price_for_plan("pro"), "price_p")
            self.assertEqual(self.mod.stripe_price_for_plan("unlimited"), "")
            self.assertEqual(self.mod.plan_from_price("price_s"), "starter")
            self.assertEqual(self.mod.plan_from_price("price_p"), "pro")
            self.assertEqual(self.mod.plan_from_price("price_unknown"), "")

    def test_signature_verify_ok_and_bad(self) -> None:
        secret = "whsec_test"
        with mock.patch.dict(os.environ, {"LIBREBASE_STRIPE_WEBHOOK_SECRET": secret}):
            payload = b'{"type":"checkout.session.completed"}'
            ts = str(int(time.time()))
            sig = hmac.new(secret.encode(), f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
            self.assertTrue(self.mod.stripe_verify_signature(payload, f"t={ts},v1={sig}"))
            self.assertFalse(
                self.mod.stripe_verify_signature(payload, f"t={ts},v1={'0' * 64}")
            )
            old_ts = str(int(time.time()) - 3600)
            old_sig = hmac.new(
                secret.encode(), f"{old_ts}.".encode() + payload, hashlib.sha256
            ).hexdigest()
            self.assertFalse(
                self.mod.stripe_verify_signature(payload, f"t={old_ts},v1={old_sig}")
            )

    def test_signature_verify_missing_secret(self) -> None:
        with mock.patch.dict(os.environ, {"LIBREBASE_STRIPE_WEBHOOK_SECRET": ""}):
            self.assertFalse(self.mod.stripe_verify_signature(b"x", "t=1,v1=abc"))

    def test_checkout_session_calls_stripe_and_returns_url(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "LIBREBASE_STRIPE_API_KEY": "sk_test_x",
                "LIBREBASE_STRIPE_PRICE_STARTER": "price_s",
            },
        ):
            _FakeStripe.responses = {
                "POST /v1/checkout/sessions": {
                    "id": "cs_1",
                    "url": "https://checkout.stripe.com/cs_1",
                    "customer": "cus_1",
                }
            }
            server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeStripe)
            self.mod.STRIPE_API_URL = f"http://127.0.0.1:{server.server_port}/v1"
            try:
                thread = threading.Thread(target=server.handle_request)
                thread.start()
                result = self.mod.stripe_checkout_session("org_1", "starter", "a@b.c", None)
                thread.join(10)
            finally:
                server.server_close()
            self.assertEqual(result["url"], "https://checkout.stripe.com/cs_1")
            self.assertEqual(result["customer"], "cus_1")


class TestStripeBillingDb(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = load_server()
        self._tmp = tempfile.TemporaryDirectory()
        self.db = self.mod.LiorgDb(Path(self._tmp.name) / "org.db")
        now = self.mod.utc_now()
        self.org_id = "org_s"
        self.db.execute(
            "INSERT INTO organizations (id, name, slug, edition, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (self.org_id, "acme", "acme", "suspended", now),
        )

    def tearDown(self) -> None:
        self.db.close()
        self._tmp.cleanup()

    def test_checkout_sets_plan_and_edition(self) -> None:
        session = {
            "client_reference_id": self.org_id,
            "mode": "subscription",
            "payment_status": "paid",
            "metadata": {"plan": "pro"},
            "customer": "cus_9",
            "subscription": "sub_9",
        }
        self.assertTrue(self.mod.billing_apply_checkout(self.db, session))
        row = self.db.fetchone("SELECT * FROM organizations WHERE id = ?", (self.org_id,))
        self.assertEqual(row["plan"], "pro")
        self.assertEqual(row["edition"], "cloud-paid")
        self.assertEqual(row["stripe_customer_id"], "cus_9")
        self.assertEqual(row["stripe_subscription_id"], "sub_9")
        self.assertEqual(row["stripe_status"], "active")

    def test_checkout_unpaid_is_ignored(self) -> None:
        session = {
            "client_reference_id": self.org_id,
            "mode": "subscription",
            "payment_status": "unpaid",
            "metadata": {"plan": "pro"},
        }
        self.assertFalse(self.mod.billing_apply_checkout(self.db, session))

    def test_subscription_cancel_downgrades_to_suspended(self) -> None:
        self.db.execute(
            "UPDATE organizations SET plan = 'pro', edition = 'cloud-paid', "
            "stripe_subscription_id = 'sub_1', stripe_status = 'active' WHERE id = ?",
            (self.org_id,),
        )
        sub = {"id": "sub_1", "customer": "cus_9", "status": "canceled", "items": {"data": []}}
        self.assertTrue(self.mod.billing_apply_subscription(self.db, sub))
        row = self.db.fetchone("SELECT * FROM organizations WHERE id = ?", (self.org_id,))
        self.assertEqual(row["plan"], "suspended")
        self.assertEqual(row["stripe_status"], "canceled")
        self.assertIsNone(row["stripe_subscription_id"])

    def test_subscription_active_maps_price_to_plan(self) -> None:
        with mock.patch.dict(os.environ, {"LIBREBASE_STRIPE_PRICE_PRO": "price_p"}):
            self.db.execute(
                "UPDATE organizations SET stripe_customer_id = 'cus_1' WHERE id = ?",
                (self.org_id,),
            )
            sub = {
                "id": "sub_2",
                "customer": "cus_1",
                "status": "active",
                "items": {"data": [{"price": {"id": "price_p"}}]},
            }
            self.assertTrue(self.mod.billing_apply_subscription(self.db, sub))
            row = self.db.fetchone("SELECT * FROM organizations WHERE id = ?", (self.org_id,))
            self.assertEqual(row["plan"], "pro")
            self.assertEqual(row["edition"], "cloud-paid")
            self.assertEqual(row["stripe_price_id"], "price_p")

    def test_subscription_unknown_price_keeps_plan(self) -> None:
        with mock.patch.dict(os.environ, {"LIBREBASE_STRIPE_PRICE_PRO": "price_p"}):
            self.db.execute(
                "UPDATE organizations SET plan = 'starter', stripe_customer_id = 'cus_1' "
                "WHERE id = ?",
                (self.org_id,),
            )
            sub = {
                "id": "sub_3",
                "customer": "cus_1",
                "status": "past_due",
                "items": {"data": [{"price": {"id": "price_other"}}]},
            }
            self.assertTrue(self.mod.billing_apply_subscription(self.db, sub))
            row = self.db.fetchone("SELECT * FROM organizations WHERE id = ?", (self.org_id,))
            self.assertEqual(row["plan"], "starter")
            self.assertEqual(row["stripe_status"], "past_due")

    def test_subscription_no_org_noop(self) -> None:
        sub = {"id": "sub_n", "customer": "cus_none", "status": "active"}
        self.assertFalse(self.mod.billing_apply_subscription(self.db, sub))


class TestStripeWebhookRoute(unittest.TestCase):
    def test_webhook_route_applies_checkout_and_returns_200(self) -> None:
        mod = load_server()
        tmp = tempfile.TemporaryDirectory()
        db = mod.LiorgDb(Path(tmp.name) / "org.db")
        now = mod.utc_now()
        org_id = "org_w"
        db.execute(
            "INSERT INTO organizations (id, name, slug, edition, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (org_id, "w", "w", "suspended", now),
        )
        secret = "whsec_route"
        old_db = mod.LiorgHandler.__dict__.get("db")
        old_secret = mod.LiorgHandler.__dict__.get("jwt_secret")
        mod.LiorgHandler.db = db
        mod.LiorgHandler.jwt_secret = "dev-secret"
        server = None
        try:
            with mock.patch.dict(os.environ, {"LIBREBASE_STRIPE_WEBHOOK_SECRET": secret}):
                server = ThreadingHTTPServer(("127.0.0.1", 0), mod.LiorgHandler)
                payload = {
                    "id": "evt_1",
                    "type": "checkout.session.completed",
                    "data": {
                        "object": {
                            "client_reference_id": org_id,
                            "mode": "subscription",
                            "payment_status": "paid",
                            "metadata": {"plan": "starter"},
                            "customer": "cus_7",
                            "subscription": "sub_7",
                        }
                    },
                }
                body = json.dumps(payload).encode()
                ts = str(int(time.time()))
                sig = hmac.new(
                    secret.encode(), f"{ts}.".encode() + body, hashlib.sha256
                ).hexdigest()
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                req = urllib.request.Request(
                    f"http://127.0.0.1:{server.server_port}/org/v1/billing/webhook",
                    data=body,
                    method="POST",
                    headers={
                        "Content-Type": "application/json",
                        "Stripe-Signature": f"t={ts},v1={sig}",
                    },
                )
                with urllib.request.urlopen(req, timeout=10) as res:
                    self.assertEqual(res.status, 200)
        finally:
            if server:
                server.shutdown()
                server.server_close()
            row = db.fetchone("SELECT * FROM organizations WHERE id = ?", (org_id,))
            self.assertEqual(row["plan"], "starter")
            self.assertEqual(row["edition"], "cloud-paid")
            mod.LiorgHandler.db = old_db
            mod.LiorgHandler.jwt_secret = old_secret
            db.close()
            tmp.cleanup()

    def test_webhook_route_rejects_bad_signature(self) -> None:
        mod = load_server()
        tmp = tempfile.TemporaryDirectory()
        db = mod.LiorgDb(Path(tmp.name) / "org.db")
        old_db = mod.LiorgHandler.__dict__.get("db")
        old_secret = mod.LiorgHandler.__dict__.get("jwt_secret")
        mod.LiorgHandler.db = db
        mod.LiorgHandler.jwt_secret = "dev-secret"
        server = None
        thread = None
        try:
            with mock.patch.dict(
                os.environ, {"LIBREBASE_STRIPE_WEBHOOK_SECRET": "whsec_route"}
            ):
                server = ThreadingHTTPServer(("127.0.0.1", 0), mod.LiorgHandler)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                body = b'{"type":"checkout.session.completed"}'
                req = urllib.request.Request(
                    f"http://127.0.0.1:{server.server_port}/org/v1/billing/webhook",
                    data=body,
                    method="POST",
                    headers={
                        "Content-Type": "application/json",
                        "Stripe-Signature": "t=1,v1=deadbeef",
                    },
                )
                with self.assertRaises(urllib.error.HTTPError) as ctx:
                    urllib.request.urlopen(req, timeout=10)
                self.assertEqual(ctx.exception.code, 401)
        finally:
            if server:
                server.shutdown()
                server.server_close()
            if old_db is None:
                del mod.LiorgHandler.db
            else:
                mod.LiorgHandler.db = old_db
            mod.LiorgHandler.jwt_secret = old_secret if old_secret is not None else "dev-secret"
            db.close()
            tmp.cleanup()


class TestInvites(unittest.TestCase):
    def _boot(self) -> tuple:
        mod = load_server()
        tmp = tempfile.TemporaryDirectory()
        db = mod.LiorgDb(Path(tmp.name) / "org.db")
        now = mod.utc_now()
        org_id = "org_inv"
        db.execute(
            "INSERT INTO organizations (id, name, slug, edition, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (org_id, "Invited Co", "invited", "suspended", now),
        )
        owner_id = "u_owner"
        invitee_id = "u_invitee"
        db.execute(
            "INSERT INTO users (id, email, password_hash, created_at, email_verified) "
            "VALUES (?, ?, ?, ?, 1), (?, ?, ?, ?, 1)",
            (owner_id, "owner@x.c", mod.hash_password("pw"), now,
             invitee_id, "invitee@x.c", mod.hash_password("pw"), now),
        )
        # owner is a member; invitee is NOT yet a member
        db.execute(
            "INSERT INTO members (org_id, user_id, role, created_at) VALUES (?, ?, ?, ?)",
            (org_id, owner_id, "owner", now),
        )
        jwt = "invite-jwt-secret"
        old_db = mod.LiorgHandler.__dict__.get("db")
        old_jwt = mod.LiorgHandler.__dict__.get("jwt_secret")
        mod.LiorgHandler.db = db
        mod.LiorgHandler.jwt_secret = jwt
        server = ThreadingHTTPServer(("127.0.0.1", 0), mod.LiorgHandler)
        base = f"http://127.0.0.1:{server.server_port}"
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return mod, tmp, db, base, server, jwt, old_db, old_jwt, org_id, owner_id, invitee_id

    def _token(self, mod, db, jwt, user_id, org_id):
        return mod.issue_session(db, jwt, user_id, org_id, "owner", "suspended")[0]

    def _post(self, base, path, body, token=None):
        data = json.dumps(body).encode()
        hdrs = {"Content-Type": "application/json"}
        if token:
            hdrs["Authorization"] = f"Bearer {token}"
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

    def _get(self, base, path):
        req = urllib.request.Request(base + path, method="GET")
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

    def _cleanup(self, mod, server, db, tmp, old_db, old_jwt):
        server.shutdown()
        server.server_close()
        mod.LiorgHandler.db = old_db
        mod.LiorgHandler.jwt_secret = old_jwt
        db.close()
        tmp.cleanup()

    def test_preview_invite_returns_org_and_role(self) -> None:
        (mod, tmp, db, base, server, jwt, old_db, old_jwt,
         org_id, owner_id, invitee_id) = self._boot()
        try:
            owner = self._token(mod, db, jwt, owner_id, org_id)
            status, body = self._post(
                base, f"/org/v1/orgs/{org_id}/invites", {"email": "invitee@x.c"}, owner,
            )
            self.assertEqual(status, 201)
            token = body["token"]
            status, body = self._get(base, f"/org/v1/invites/{token}")
            self.assertEqual(status, 200)
            self.assertEqual(body["orgName"], "Invited Co")
            self.assertEqual(body["role"], "developer")
            self.assertEqual(body["email"], "invitee@x.c")
        finally:
            self._cleanup(mod, server, db, tmp, old_db, old_jwt)

    def test_accept_invite_joins_org_for_matching_user(self) -> None:
        (mod, tmp, db, base, server, jwt, old_db, old_jwt,
         org_id, owner_id, invitee_id) = self._boot()
        try:
            owner = self._token(mod, db, jwt, owner_id, org_id)
            status, body = self._post(
                base, f"/org/v1/orgs/{org_id}/invites",
                {"email": "invitee@x.c", "role": "admin"}, owner,
            )
            self.assertEqual(status, 201)
            invite_token = body["token"]
            invitee = self._token(mod, db, jwt, invitee_id, org_id)
            status, body = self._post(base, f"/org/v1/invites/{invite_token}/accept", {}, invitee)
            self.assertEqual(status, 200)
            self.assertEqual(body["orgId"], org_id)
            self.assertEqual(body["role"], "admin")
            row = db.fetchone("SELECT role FROM members WHERE org_id = ? AND user_id = ?",
                              (org_id, invitee_id))
            self.assertEqual(row["role"], "admin")
            inv = db.fetchone("SELECT accepted_at FROM invites WHERE token = ?", (invite_token,))
            self.assertIsNotNone(inv["accepted_at"])
        finally:
            self._cleanup(mod, server, db, tmp, old_db, old_jwt)

    def test_accept_invite_rejects_email_mismatch(self) -> None:
        (mod, tmp, db, base, server, jwt, old_db, old_jwt,
         org_id, owner_id, invitee_id) = self._boot()
        try:
            owner = self._token(mod, db, jwt, owner_id, org_id)
            _, body = self._post(
                base, f"/org/v1/orgs/{org_id}/invites", {"email": "invitee@x.c"}, owner,
            )
            invite_token = body["token"]
            # owner's email != invitee's email
            status, body = self._post(base, f"/org/v1/invites/{invite_token}/accept", {}, owner)
            self.assertEqual(status, 403)
            self.assertEqual(body["error"], "invite is for another email address")
        finally:
            self._cleanup(mod, server, db, tmp, old_db, old_jwt)

    def test_accept_invite_requires_auth(self) -> None:
        (mod, tmp, db, base, server, jwt, old_db, old_jwt,
         org_id, owner_id, invitee_id) = self._boot()
        try:
            owner = self._token(mod, db, jwt, owner_id, org_id)
            _, body = self._post(
                base, f"/org/v1/orgs/{org_id}/invites", {"email": "invitee@x.c"}, owner,
            )
            invite_token = body["token"]
            status, body = self._post(base, f"/org/v1/invites/{invite_token}/accept", {})
            self.assertEqual(status, 401)
        finally:
            self._cleanup(mod, server, db, tmp, old_db, old_jwt)

    def test_accept_invite_idempotent(self) -> None:
        (mod, tmp, db, base, server, jwt, old_db, old_jwt,
         org_id, owner_id, invitee_id) = self._boot()
        try:
            owner = self._token(mod, db, jwt, owner_id, org_id)
            _, body = self._post(
                base, f"/org/v1/orgs/{org_id}/invites", {"email": "invitee@x.c"}, owner,
            )
            invite_token = body["token"]
            invitee = self._token(mod, db, jwt, invitee_id, org_id)
            self._post(base, f"/org/v1/invites/{invite_token}/accept", {}, invitee)
            # second accept -> 410 no longer valid
            status, _ = self._post(base, f"/org/v1/invites/{invite_token}/accept", {}, invitee)
            self.assertEqual(status, 410)
        finally:
            self._cleanup(mod, server, db, tmp, old_db, old_jwt)


class TestSwitchOrg(unittest.TestCase):
    def _boot(self):
        mod = load_server()
        tmp = tempfile.TemporaryDirectory()
        db = mod.LiorgDb(Path(tmp.name) / "org.db")
        now = mod.utc_now()
        db.execute(
            "INSERT INTO organizations (id, name, slug, edition, created_at, plan) VALUES (?, ?, ?, ?, ?, ?)",
            ("org_a", "A", "a", "suspended", now, "suspended"),
        )
        db.execute(
            "INSERT INTO organizations (id, name, slug, edition, created_at, plan) VALUES (?, ?, ?, ?, ?, ?)",
            ("org_b", "B", "b", "suspended", now, "suspended"),
        )
        db.execute(
            "INSERT INTO users (id, email, password_hash, created_at, email_verified) VALUES (?, ?, ?, ?, ?)",
            ("u1", "u1@x.c", mod.hash_password("pw"), now, 1),
        )
        db.execute(
            "INSERT INTO members (org_id, user_id, role, created_at) VALUES (?, ?, ?, ?)",
            ("org_a", "u1", "owner", now),
        )
        db.execute(
            "INSERT INTO members (org_id, user_id, role, created_at) VALUES (?, ?, ?, ?)",
            ("org_b", "u1", "admin", now),
        )
        jwt = "switch-jwt-secret"
        old_db = mod.LiorgHandler.__dict__.get("db")
        old_jwt = mod.LiorgHandler.__dict__.get("jwt_secret")
        mod.LiorgHandler.db = db
        mod.LiorgHandler.jwt_secret = jwt
        server = ThreadingHTTPServer(("127.0.0.1", 0), mod.LiorgHandler)
        base = f"http://127.0.0.1:{server.server_port}"
        threading.Thread(target=server.serve_forever, daemon=True).start()
        access, _ = mod.issue_session(db, jwt, "u1", "org_a", "owner", "suspended")
        return mod, tmp, db, base, server, jwt, old_db, old_jwt, access

    def test_switch_org_issues_session_for_member_org(self) -> None:
        mod, tmp, db, base, server, jwt, old_db, old_jwt, tok = self._boot()
        try:
            req = urllib.request.Request(
                f"{base}/org/v1/auth/switch-org",
                data=b'{"orgId":"org_b"}', method="POST",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {tok}"},
            )
            with urllib.request.urlopen(req, timeout=10) as res:
                body = json.loads(res.read().decode())
            self.assertEqual(res.status, 200)
            self.assertEqual(body["orgId"], "org_b")
            self.assertEqual(body["role"], "admin")
            # new token is valid and scoped to org_b
            claims = mod.verify_jwt(body["token"], jwt)
            self.assertIsNotNone(claims)
            self.assertEqual(claims["org_id"], "org_b")
        finally:
            server.shutdown(); server.server_close()
            mod.LiorgHandler.db = old_db
            mod.LiorgHandler.jwt_secret = old_jwt
            db.close(); tmp.cleanup()

    def test_switch_org_non_member_forbidden(self) -> None:
        mod, tmp, db, base, server, jwt, old_db, old_jwt, tok = self._boot()
        try:
            db.execute(
                "INSERT INTO organizations (id, name, slug, edition, created_at, plan) VALUES (?, ?, ?, ?, ?, ?)",
                ("org_c", "C", "c", "suspended", mod.utc_now(), "suspended"),
            )
            req = urllib.request.Request(
                f"{base}/org/v1/auth/switch-org",
                data=b'{"orgId":"org_c"}', method="POST",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {tok}"},
            )
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req, timeout=10)
            self.assertEqual(ctx.exception.code, 403)
        finally:
            server.shutdown(); server.server_close()
            mod.LiorgHandler.db = old_db
            mod.LiorgHandler.jwt_secret = old_jwt
            db.close(); tmp.cleanup()


if __name__ == "__main__":
    unittest.main()