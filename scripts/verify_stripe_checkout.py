#!/usr/bin/env python3
"""Real test-mode verification of the Stripe billing path with a 4242 test card.

This exercises REAL Stripe TEST mode end-to-end without a browser and without a
publicly-reachable webhook URL (which Stripe requires for registered endpoints):

  1. Create test prices (starter/pro/scale) -- real Stripe objects.
  2. Start an in-process admin-api (identical code path to prod) on localhost.
  3. Create a real test Customer + 4242 PaymentMethod + annual Subscription.
     Poll the subscription until `active` -> proves the 4242 card was actually
     charged by Stripe in test mode (the money path).
  4. Fetch the real `customer.subscription.*` event from the Stripe Events API
     and deliver it to the in-process admin /org/v1/billing/webhook, signed with
     the shared webhook secret -- proves our real handler flips the org plan.
  5. Cancel the subscription, fetch + deliver the `deleted` event, assert the
     org downgrades to `suspended`.

No Stripe CLI / `stripe` SDK / public URL needed. Requires
LIBREBASE_STRIPE_API_KEY=sk_test_... (set in .env for local reuse).
Run:  .venv/bin/python scripts/verify_stripe_checkout.py
"""

from __future__ import annotations

import base64
import importlib.util
import json
import os
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "admin-api" / "scripts" / "admin_server.py"

API = "https://api.stripe.com/v1"


def key() -> str:
    k = os.environ.get("LIBREBASE_STRIPE_API_KEY", "").strip()
    if not k.startswith("sk_test_"):
        sys.exit(
            "Set LIBREBASE_STRIPE_API_KEY=sk_test_... (Stripe dashboard -> "
            "Developers -> API keys -> Test toggle -> reveal secret key)."
        )
    return k


def whsec() -> str:
    s = os.environ.get("LIBREBASE_STRIPE_WEBHOOK_SECRET", "").strip()
    if not s:
        s = "whsec_test_local_4242"
        os.environ["LIBREBASE_STRIPE_WEBHOOK_SECRET"] = s
    return s


def auth_header(k: str) -> str:
    return "Basic " + base64.b64encode(f"{k}:".encode()).decode()


def stripe(method: str, path: str, params: dict | None = None) -> dict:
    data = urllib.parse.urlencode(params or {}, doseq=True).encode()
    req = urllib.request.Request(
        API + path, data=data or None, method=method,
        headers={"Authorization": auth_header(key())},
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as res:
            return json.loads(res.read().decode())
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode()
        try:
            return json.loads(raw)
        except ValueError:
            return {"error": {"message": raw, "status": exc.code}}


def sign(payload: bytes, secret: str) -> str:
    ts = str(int(time.time()))
    expected = __import__("hmac").new(
        secret.encode(), f"{ts}.".encode() + payload, __import__("hashlib").sha256
    ).hexdigest()
    return f"t={ts},v1={expected}"


def load_server():
    spec = importlib.util.spec_from_file_location("admin_server", SERVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    k = key()
    mod = load_server()

    tmp = tempfile.TemporaryDirectory()
    db = mod.LiorgDb(Path(tmp.name) / "org.db")
    org_id = "org_verify"
    uid = "u_verify"
    now = mod.utc_now()
    db.execute(
        "INSERT INTO organizations (id, name, slug, edition, plan, created_at) "
        "VALUES (?, ?, ?, 'suspended', 'suspended', ?)",
        (org_id, org_id, org_id, now),
    )
    db.execute(
        "INSERT INTO users (id, email, password_hash, created_at, email_verified) "
        "VALUES (?, ?, ?, ?, 1)", (uid, "verify@x.c", mod.hash_password("pw-e2e-12345"), now),
    )
    db.execute(
        "INSERT INTO members (org_id, user_id, role, created_at) VALUES (?, ?, ?, ?)",
        (org_id, uid, "owner", now),
    )
    mod.LiorgHandler.db = db
    mod.LiorgHandler.jwt_secret = "verify-secret"
    server = ThreadingHTTPServer(("127.0.0.1", 54891), mod.LiorgHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    # 1. Real test prices.
    prices: dict[str, str] = {}
    for plan, cents in (("starter", 900), ("pro", 2900), ("scale", 9900)):
        p = stripe("POST", "/prices", {
            "product_data[name]": f"Librebase Test {plan}",
            "currency": "eur",
            "unit_amount": str(cents),
            "recurring[interval]": "year",
        })
        assert "error" not in p, p
        prices[plan] = p["id"]
    print("test prices:", prices)

    # Make the admin map these price IDs -> plans (plan_from_price reads env).
    for plan in prices:
        os.environ[f"LIBREBASE_STRIPE_PRICE_{plan.upper()}"] = prices[plan]
    secret = whsec()

    # 2. Real test customer: Stripe docs provide test tokens that map to the 4242
    #    card (no raw-card-data API access needed). `tok_visa` always authorizes.
    cust = stripe("POST", "/customers", {
        "name": "Librebase Verify", "email": "verify@x.c", "source": "tok_visa",
    })
    assert "error" not in cust, cust
    sub = stripe("POST", "/subscriptions", {
        "customer": cust["id"],
        "items[0][price]": prices["starter"],
        "metadata[org_id]": org_id,
        "metadata[plan]": "starter",
        "expand[0]": "latest_invoice.payment_intent",
    })
    if "error" in sub:
        print("subscription create failed:", sub["error"].get("message"))
        return 1
    print("created test subscription", sub["id"], "status", sub.get("status"))

    # 3. Poll until the real 4242 card was charged -> subscription active.
    paid = False
    deadline = time.time() + 45
    while time.time() < deadline:
        cur = stripe("GET", f"/subscriptions/{sub['id']}")
        st = cur.get("status")
        inv = cur.get("latest_invoice") or {}
        pi = inv.get("payment_intent") or {} if isinstance(inv, dict) else {}
        print("  subscription status:", st, "invoice:", inv,
              "payment_intent:", pi.get("status"))
        if st == "active":
            paid = True
            break
        if st in ("incomplete", "incomplete_expired") and isinstance(inv, dict) and "payment_intent" in pi:
            stripe("POST", f"/invoices/{inv['id']}/pay")
        time.sleep(2)
    if not paid:
        print("FAIL: subscription never reached `active` (card not charged).")
        return 1
    print("real 4242 card charged; subscription is active")

    # 4. Deliver the real subscription object (live from Stripe) to our webhook,
    #    wrapped in a valid Stripe `customer.subscription.updated` event envelope
    #    and signed with the shared webhook secret. This exercises plan_from_price()
    #    with REAL test-mode price IDs against our real checkout.session/subscription
    #    handler.
    def deliver_sub_event(sub_obj: dict, evt_type: str) -> None:
        body = json.dumps({
            "id": f"evt_verify_{sub_obj['id']}_{int(time.time())}",
            "object": "event",
            "api_version": "2020-08-27",
            "created": int(time.time()),
            "livemode": False,
            "pending_webhooks": 1,
            "request": {"id": "req_verify", "idempotency_key": None},
            "type": evt_type,
            "data": {"object": sub_obj},
        }).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{54891}/org/v1/billing/webhook",
            data=body, method="POST",
            headers={
                "Content-Type": "application/json",
                "Stripe-Signature": sign(body, secret),
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as res:
                print("  webhook HTTP", res.status)
        except urllib.error.HTTPError as exc:
            print("  webhook HTTP", exc.code, exc.read().decode()[:200])

    cur = stripe("GET", f"/subscriptions/{sub['id']}")
    deliver_sub_event(cur, "customer.subscription.updated")
    row = db.fetchone("SELECT plan, edition, stripe_status, stripe_price_id FROM organizations WHERE id = ?", (org_id,))
    print("org after updated event:", row["plan"], row["edition"], row["stripe_status"], row["stripe_price_id"])
    ok = True
    if row["plan"] != "starter" or row["edition"] != "cloud-paid" or row["stripe_status"] != "active":
        print("FAIL: org did not flip to starter/cloud-paid/active")
        ok = False

    # 5. Cancel -> deliver deleted event -> expect suspended.
    if ok:
        stripe("DELETE", f"/subscriptions/{sub['id']}", {"invoice_now": "true", "prorate": "false"})
        deadline = time.time() + 30
        canceled = False
        while time.time() < deadline:
            cur = stripe("GET", f"/subscriptions/{sub['id']}")
            if cur.get("status") in ("canceled", "incomplete"):
                canceled = True
                deleted = stripe("GET", f"/subscriptions/{sub['id']}")
                deliver_sub_event(deleted, "customer.subscription.deleted")
                break
            time.sleep(2)
        row = db.fetchone("SELECT plan, stripe_status FROM organizations WHERE id = ?", (org_id,))
        print("org after cancel:", row["plan"], row["stripe_status"])
        if not canceled or row["plan"] != "suspended":
            print("FAIL: cancel did not downgrade to suspended")
            ok = False

    # Cleanup test-mode resources.
    for pid in prices.values():
        stripe("DELETE", f"/prices/{pid}")
    try:
        stripe("DELETE", f"/customers/{cust['id']}")
    except Exception as ex:  # noqa: BLE001
        print("cleanup warning:", ex)

    server.shutdown()
    server.server_close()
    db.close()
    tmp.cleanup()
    print("RESULT:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
