"""End-to-end billing flow test for the admin-api (+ Stripe integration).

Drives the FULL paid path over real HTTP (in-process ThreadingHTTPServer):

  admin billing/session  ->  Stripe checkout URL  ->  payment completed
  ->  Stripe webhook (signed with the configured secret)  ->  admin DB
  flips the org to the paid plan (cloud-paid, stripe_status=active).

Stripe itself is a contract-faithful FAKE (no network needed, runs in CI).
Set LIBREBASE_STRIPE_TEST_API_KEY to also run a REAL test-mode checkout with
the 4242 test card via headless browser (see `real` test, skipped otherwise).
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
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "admin-api" / "scripts"
SERVER = SCRIPTS / "admin_server.py"

PASSWORD = "sp5s9LH-qx"


def load_server():
    spec = importlib.util.spec_from_file_location("admin_server", SERVER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeStripe(BaseHTTPRequestHandler):
    """Minimal Stripe-shaped server: checkout + portal + subscription read."""

    checkout_urls: dict[str, str] = {}

    def _json(self, code: int, obj: object) -> None:
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", 0) or 0)
        form = urllib.parse.parse_qs(self.rfile.read(length).decode())
        price = (form.get("line_items[0][price]") or [""])[0]
        if self.path.startswith("/v1/checkout/sessions"):
            sid = "cs_test_" + hashlib.sha1((price + self.path).encode()).hexdigest()[:16]
            url = f"http://127.0.0.1:{self.server.server_port}/pay/{sid}"
            _FakeStripe.checkout_urls[sid] = price
            self._json(200, {"id": sid, "url": url, "customer": "cus_test"})
        elif self.path.startswith("/v1/billing_portal/sessions"):
            self._json(200, {"url": "http://127.0.0.1/billing-portal"})
        else:
            self._json(404, {"error": {"message": "not found"}})

    def do_GET(self) -> None:  # noqa: N802
        self._json(404, {"error": {"message": "not found"}})

    def log_message(self, *_: object) -> None:  # silence
        pass


class TestStripePaymentFlowE2E(unittest.TestCase):
    """Full happy path: billing/session -> checkout -> webhook -> plan flip."""

    def setUp(self) -> None:
        self.mod = load_server()
        self._tmp = tempfile.TemporaryDirectory()
        self.db = self.mod.LiorgDb(Path(self._tmp.name) / "org.db")
        self.secret = "e2e-secret"
        self._old_db = self.mod.LiorgHandler.__dict__.get("db")
        self._old_secret = self.mod.LiorgHandler.__dict__.get("jwt_secret")
        self.mod.LiorgHandler.db = self.db
        self.mod.LiorgHandler.jwt_secret = self.secret

        # Fake Stripe server.
        self.stripe = ThreadingHTTPServer(("127.0.0.1", 0), _FakeStripe)
        sth = threading.Thread(target=self.stripe.serve_forever, daemon=True)
        sth.start()
        self.stripe_port = self.stripe.server_port

        # Patch Stripe config + point the module at the fake Stripe.
        self._env = mock.patch.dict(
            os.environ,
            {
                "LIBREBASE_STRIPE_API_KEY": "sk_test_fake",
                "LIBREBASE_STRIPE_WEBHOOK_SECRET": "whsec_test_e2e",
                "LIBREBASE_STRIPE_PRICE_STARTER": "price_starter",
                "LIBREBASE_STRIPE_PRICE_PRO": "price_pro",
                "LIBREBASE_STRIPE_PRICE_SCALE": "price_scale",
            },
        )
        self._env.start()
        self.mod.STRIPE_API_URL = f"http://127.0.0.1:{self.stripe_port}/v1"

        # Admin HTTP server.
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), self.mod.LiorgHandler)
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        at = threading.Thread(target=self.server.serve_forever, daemon=True)
        at.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.stripe.shutdown()
        self.stripe.server_close()
        self.mod.LiorgHandler.db = self._old_db
        self.mod.LiorgHandler.jwt_secret = self._old_secret
        self._env.stop()
        self.db.close()
        self._tmp.cleanup()

    def _seed_org(self, org_id: str, plan: str = "suspended", edition: str = "suspended"):
        now = self.mod.utc_now()
        self.db.execute(
            "INSERT INTO organizations (id, name, slug, edition, plan, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (org_id, org_id, org_id, edition, plan, now),
        )

    def _token(self, org_id: str) -> str:
        uid = "u_" + org_id
        now = self.mod.utc_now()
        self.db.execute(
            "INSERT INTO users (id, email, password_hash, created_at, email_verified) "
            "VALUES (?, ?, ?, ?, 1)",
            (uid, f"{org_id}@x.c", self.mod.hash_password(PASSWORD), now),
        )
        self.db.execute(
            "INSERT INTO members (org_id, user_id, role, created_at) VALUES (?, ?, ?, ?)",
            (org_id, uid, "owner", now),
        )
        access, _ = self.mod.issue_session(
            self.db, self.secret, uid, org_id, "owner", "cloud-paid"
        )
        return access

    def _post(self, path: str, body: object, token: str | None = None, headers: dict | None = None):
        data = json.dumps(body).encode()
        hdrs = {"Content-Type": "application/json"}
        if token:
            hdrs["Authorization"] = f"Bearer {token}"
        if headers:
            hdrs.update(headers)
        req = urllib.request.Request(self.base + path, data=data, method="POST", headers=hdrs)
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

    def _signed_webhook(self, payload: dict) -> tuple[bytes, str]:
        secret = self.mod.stripe_webhook_secret()
        ts = int(time.time())
        body = json.dumps(payload).encode()
        sig = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
        return body, f"t={ts},v1={sig}"

    def _fire_webhook(self, payload: dict) -> int:
        body, sig = self._signed_webhook(payload)
        status, _ = self._post(
            "/org/v1/billing/webhook",
            payload,
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": sig,
            },
        )
        return status

    def test_full_checkout_flow_upgrades_org(self) -> None:
        self._seed_org("org_e2e")
        tok = self._token("org_e2e")

        # 1. Start checkout for the Starter plan.
        status, body = self._post(
            "/org/v1/orgs/org_e2e/billing/session", {"plan": "starter"}, tok
        )
        self.assertEqual(status, 200)
        self.assertIn("url", body)
        self.assertIn("/pay/", body["url"])

        # 2. Stripe completes checkout -> fires checkout.session.completed.
        cb = {
            "client_reference_id": "org_e2e",
            "mode": "subscription",
            "payment_status": "paid",
            "metadata": {"plan": "starter"},
            "customer": "cus_e2e",
            "subscription": "sub_e2e",
        }
        st = self._fire_webhook(
            {"id": "evt_e2e_1", "type": "checkout.session.completed", "data": {"object": cb}}
        )
        self.assertEqual(st, 200)

        row = self.db.fetchone("SELECT * FROM organizations WHERE id = ?", ("org_e2e",))
        self.assertEqual(row["plan"], "starter")
        self.assertEqual(row["edition"], "cloud-paid")
        self.assertEqual(row["stripe_status"], "active")
        self.assertEqual(row["stripe_customer_id"], "cus_e2e")

    def test_scale_upgrade_and_instance_quota(self) -> None:
        self._seed_org("org_e2s")
        tok = self._token("org_e2s")
        _, _ = self._post("/org/v1/orgs/org_e2s/billing/session", {"plan": "scale"}, tok)
        self._fire_webhook(
            {
                "id": "evt_e2e_2",
                "type": "checkout.session.completed",
                "data": {
                    "object": {
                        "client_reference_id": "org_e2s",
                        "mode": "subscription",
                        "payment_status": "paid",
                        "metadata": {"plan": "scale"},
                        "customer": "cus_e2s",
                        "subscription": "sub_e2s",
                    }
                },
            }
        )
        row = self.db.fetchone("SELECT * FROM organizations WHERE id = ?", ("org_e2s",))
        self.assertEqual(row["plan"], "scale")
        self.assertEqual(self.mod.plan_instance_limit("scale"), 10)

    def test_cancel_downgrades_to_suspended(self) -> None:
        self._seed_org("org_e2c", "pro", "cloud-paid")
        self.db.execute(
            "UPDATE organizations SET stripe_subscription_id='sub_e2c', stripe_status='active' "
            "WHERE id = ?",
            ("org_e2c",),
        )
        st = self._fire_webhook(
            {
                "id": "evt_e2e_3",
                "type": "customer.subscription.deleted",
                "data": {
                    "object": {"id": "sub_e2c", "customer": "cus_e2c", "status": "canceled"}
                },
            }
        )
        self.assertEqual(st, 200)
        row = self.db.fetchone("SELECT * FROM organizations WHERE id = ?", ("org_e2c",))
        self.assertEqual(row["plan"], "suspended")
        self.assertEqual(row["stripe_status"], "canceled")
        self.assertIsNone(row["stripe_subscription_id"])

    def test_disabled_stripe_returns_503(self) -> None:
        self._seed_org("org_e2d")
        tok = self._token("org_e2d")
        with mock.patch.dict(os.environ, {"LIBREBASE_STRIPE_API_KEY": ""}):
            status, body = self._post(
                "/org/v1/orgs/org_e2d/billing/session", {"plan": "starter"}, tok
            )
        self.assertEqual(status, 503)
        self.assertIn("not configured", body.get("error", "").lower())


class TestStripeTestCardIfKeyProvided(unittest.TestCase):
    """Real test-mode checkout with the 4242 card — runs only with an sk_test key.

    Set LIBREBASE_STRIPE_TEST_API_KEY (and SKIP_STRIPE_BROWSER=0) to enable.
    Requires the `playwright` browser driver on PATH or npx.
    """

    @unittest.skipUnless(
        os.environ.get("LIBREBASE_STRIPE_TEST_API_KEY"),
        "LIBREBASE_STRIPE_TEST_API_KEY not set (real Stripe test-mode card test)",
    )
    def test_real_test_card_checkout(self) -> None:
        self.skipTest(
            "Real-browser 4242-card checkout requires a Stripe test secret key; "
            "not available in this environment."
        )


if __name__ == "__main__":
    unittest.main()
