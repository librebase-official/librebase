#!/usr/bin/env python3
"""Local end-to-end Stripe testing with REAL webhooks forwarded to your dev admin.

Unblocks the #1 local problem — "Stripe won't deliver webhooks to localhost" —
by running the Stripe CLI's `stripe listen` bridge (works headless with STRIPE_API_KEY,
no browser login, no public URL, no Stripe CLI auth):

  1. Creates real test-mode prices (starter/pro/scale).
  2. Starts your REAL admin-api (admin-api/scripts/admin_server.py) on port 54900,
     configured with those price IDs + a shared webhook secret.
  3. Starts `stripe listen --forward-to http://127.0.0.1:54900/org/v1/billing/webhook`
     and captures the real webhook signing secret Stripe will use.
  4. Seeds a temp DB with an org + owner.
  5. Creates a real test Customer (tok_visa = 4242) + real Subscription with
     metadata org_id.
  6. Stripe fires customer.subscription.* (and, if you hit billing/session,
     checkout.session.completed) → forwarded by `stripe listen` to your live
     admin handler → the org flips to starter/cloud-paid/active in the DB.

Requires: `brew install stripe` (Stripe CLI v1.50+) and LIBREBASE_STRIPE_API_KEY=sk_test_...
Run:  . ./.env && .venv/bin/python scripts/run_local_stripe_dev.py
"""

from __future__ import annotations

import base64
import hmac
import importlib.util
import re
import sqlite3
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "admin-api" / "scripts" / "admin_server.py"
API = "https://api.stripe.com/v1"
ADMIN_HOST, ADMIN_PORT = "127.0.0.1", 54900
FORWARD_PATH = f"http://{ADMIN_HOST}:{ADMIN_PORT}/org/v1/billing/webhook"


def stripe(method, path, params=None, key=None):
    key = key or import_key()
    data = urllib.parse.urlencode(params or {}, doseq=True).encode()
    req = urllib.request.Request(
        API + path, data=data or None, method=method,
        headers={"Authorization": "Basic " + base64.b64encode(f"{key}:".encode()).decode()},
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as res:
            return res.status, res.read().decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()


def import_key():
    import os
    k = os.environ.get("LIBREBASE_STRIPE_API_KEY", "").strip()
    if not k.startswith("sk_test_"):
        sys.exit("Set LIBREBASE_STRIPE_API_KEY=sk_test_... in .env or env.")
    return k


def _json(status, text):
    import json
    try:
        return json.loads(text)
    except ValueError:
        return {"raw": text}


def main() -> int:
    key = import_key()

    # 1. Real test prices.
    prices = {}
    for plan, cents in (("starter", 900), ("pro", 2900), ("scale", 9900)):
        st, txt = stripe("POST", "/prices", {
            "product_data[name]": f"Librebase Local {plan}", "currency": "eur",
            "unit_amount": str(cents), "recurring[interval]": "year",
        })
        obj = _json(st, txt)
        if "error" in obj:
            print("price create failed:", obj["error"].get("message")); return 1
        prices[plan] = obj["id"]
    print("test prices:", prices)

    # 2. Temp DB seeded via the REAL admin schema (LiorgDb runs all migrations).
    import os, tempfile, importlib.util
    tmp = tempfile.TemporaryDirectory()
    db_path = Path(tmp.name) / "org.db"
    spec = importlib.util.spec_from_file_location("admin_server", SERVER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    db = mod.LiorgDb(db_path)
    now = mod.utc_now()
    org_id = "org_local"
    db.execute(
        "INSERT INTO organizations (id, name, slug, edition, created_at, plan) VALUES (?, ?, ?, ?, ?, ?)",
        (org_id, "Local Org", "local-org", "suspended", now, "suspended"),
    )
    db.execute(
        "INSERT INTO users (id, email, password_hash, created_at, email_verified) VALUES (?, ?, ?, ?, ?)",
        ("u_local", "dev@x.c", mod.hash_password("pw"), now, 1),
    )
    db.execute(
        "INSERT INTO members (org_id, user_id, role, created_at) VALUES (?, ?, ?, ?)",
        (org_id, "u_local", "owner", now),
    )
    db.close()

    # 3. Start `stripe listen` first to capture its signing secret.
    listen = subprocess.Popen(
        ["stripe", "listen",
         "--api-key", key,
         "--forward-to", FORWARD_PATH,
         "--events", "checkout.session.completed,customer.subscription.created,"
         "customer.subscription.updated,customer.subscription.deleted"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    def _pipe() -> None:
        while True:
            line = listen.stdout.readline()
            if not line:
                break
            print("  [stripe listen]", line.rstrip())
    threading.Thread(target=_pipe, daemon=True).start()
    secret = None
    deadline = time.time() + 20
    while time.time() < deadline:
        line = listen.stdout.readline()
        if not line:
            if listen.poll() is not None:
                print("stripe listen exited early:", listen.stdout.read()); return 1
            continue
        print("  [stripe listen]", line.rstrip())
        m = re.search(r"webhook signing secret is (whsec_\S+)", line)
        if m:
            secret = m.group(1); break
    if not secret:
        print("FAIL: could not capture Stripe webhook signing secret"); listen.terminate()
        return 1

    # 4. Start the real admin server with the shared webhook secret + price IDs.
    env = dict(os.environ)
    env.update({
        "LIBREBASE_ADMIN_BIND": ADMIN_HOST, "LIBREBASE_ADMIN_PORT": str(ADMIN_PORT),
        "LIBREBASE_ADMIN_DB_PATH": str(db_path), "LIBREBASE_ADMIN_JWT_SECRET": "local-dev-secret",
        "LIBREBASE_STRIPE_API_KEY": key, "LIBREBASE_STRIPE_WEBHOOK_SECRET": secret,
        "LIBREBASE_STRIPE_PRICE_STARTER": prices["starter"],
        "LIBREBASE_STRIPE_PRICE_PRO": prices["pro"],
        "LIBREBASE_STRIPE_PRICE_SCALE": prices["scale"],
    })
    admin = subprocess.Popen([sys.executable, str(SERVER)], env=env)
    time.sleep(1.5)
    if admin.poll() is not None:
        print("admin server failed to start"); return 1

    # 5. Real test customer (tok_visa = 4242) + subscription with metadata org_id.
    st, txt = stripe("POST", "/customers", {"name": "Local Dev", "email": "local@x.c", "source": "tok_visa"})
    cust = _json(st, txt)
    if "error" in cust:
        print("customer create failed:", cust["error"].get("message")); _stop(listen, admin, tmp); return 1
    st, txt = stripe("POST", "/subscriptions", {
        "customer": cust["id"], "items[0][price]": prices["starter"],
        "metadata[org_id]": org_id, "metadata[plan]": "starter",
    })
    sub = _json(st, txt)
    if "error" in sub:
        print("subscription create failed:", sub["error"].get("message")); _stop(listen, admin, tmp); return 1
    print("created test subscription", sub["id"], "status", sub.get("status"))

    # 6. Poll the admin DB (flipped by the REAL forwarded Stripe webhook event).
    ok = False
    deadline = time.time() + 35
    while time.time() < deadline:
        c = sqlite3.connect(db_path); c.row_factory = sqlite3.Row
        row = c.execute("SELECT plan, edition, stripe_status, stripe_price_id FROM organizations WHERE id=?", (org_id,)).fetchone()
        c.close()
        print("  org:", row["plan"], row["edition"], row["stripe_status"], row["stripe_price_id"])
        if row and row["plan"] == "starter" and row["edition"] == "cloud-paid":
            ok = True; break
        time.sleep(2)

    _stop(listen, admin, tmp)
    for pid in prices.values():
        stripe("DELETE", f"/prices/{pid}")
    try:
        stripe("DELETE", f"/customers/{cust['id']}")
    except Exception as ex:  # noqa: BLE001
        print("cleanup warning:", ex)
    print("RESULT:", "PASS — live webhook flipped the org" if ok else "FAIL — org not flipped")
    return 0 if ok else 1


def _stop(listen, admin, tmp):
    try:
        listen.terminate(); listen.wait(timeout=5)
    except Exception:  # noqa: BLE001
        pass
    try:
        admin.terminate(); admin.wait(timeout=5)
    except Exception:  # noqa: BLE001
        pass
    tmp.cleanup()


if __name__ == "__main__":
    import os, urllib.error
    raise SystemExit(main())
