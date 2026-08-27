#!/usr/bin/env python3
"""Real Hetzner verification of the host-provisioning substrate.

Spins up an in-process admin-api (identical code path to prod) on localhost,
points it at the REAL Hetzner Cloud API via LIBREBASE_HETZNER_API_TOKEN, and:

  1. Rents a VM (provider=hetzner) -> admin calls Hetzner create_server.
  2. Asserts the host row gets a real server_id + public ip, status=provisioning.
  3. Polls the real Hetzner API until the server is up (status=running), proving
     the golden image booted.
  4. Teardown: deletes the host -> admin calls Hetzner delete_server (no orphan).

Does NOT require the host agent (Phase 1) or instance scheduling yet; the agent
is what flips host status provisioning->running and places instances. This
verifies the substrate that unblocks them.

Requires LIBREBASE_HETZNER_API_TOKEN (Hetzner Cloud Access -> API Token,
Read+Write). Uses the cheapest image/server unless overridden:
  LIBREBASE_HETZNER_SERVER_TYPE, LIBREBASE_HETZNER_IMAGE_ID,
  LIBREBASE_HETZNER_SSH_KEY_ID, LIBREBASE_HETZNER_REGION.

Run:  python3 scripts/verify_hetzner_provision.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "admin-api" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import hcloud  # noqa: E402

SERVER = SCRIPTS / "admin_server.py"


def token() -> str:
    t = os.environ.get("LIBREBASE_HETZNER_API_TOKEN", "").strip()
    if not t:
        sys.exit(
            "Skipping real Hetzner verification: set LIBREBASE_HETZNER_API_TOKEN\n"
            "(Hetzner Cloud console -> Access -> API Token -> Read+Write). All "
            "mocks tests already passed; this step is the real-machine check."
        )
    return t


def load_server():
    spec = importlib.util.spec_from_file_location("admin_server_verify", SERVER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def http(method, base, path, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    hdrs = {"Content-Type": "application/json"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(base + path, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            raw = res.read().decode() or "{}"
            return res.status, json.loads(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode() or "{}"
        try:
            parsed = json.loads(raw)
        except ValueError:
            parsed = raw
        return exc.code, parsed


def main() -> int:
    token()  # gate / instructions
    mod = load_server()
    tmp = tempfile.TemporaryDirectory()
    db = mod.LiorgDb(Path(tmp.name) / "verify.db")
    now = mod.utc_now()

    org_id = "org_vh"
    db.execute(
        "INSERT INTO organizations (id, name, slug, edition, created_at, plan) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (org_id, "Verify Hetzner", "vh", "cloud-paid", now, "cloud-paid"),
    )
    db.execute(
        "INSERT INTO users (id, email, password_hash, created_at, email_verified) "
        "VALUES (?, ?, ?, ?, 1)",
        ("u_owner", "owner@vh.c", mod.hash_password("pw"), now),
    )
    db.execute(
        "INSERT INTO members (org_id, user_id, role, created_at) VALUES (?, ?, ?, ?)",
        (org_id, "u_owner", "owner", now),
    )

    mod.LiorgHandler.db = db
    mod.LiorgHandler.jwt_secret = "verify-jwt-secret"
    server = ThreadingHTTPServer(("127.0.0.1", 0), mod.LiorgHandler)
    base = f"http://127.0.0.1:{server.server_port}"
    threading.Thread(target=server.serve_forever, daemon=True).start()

    access_token = mod.issue_session(db, "verify-jwt-secret", "u_owner", org_id, "owner", "cloud-paid")[0]
    auth = {"Authorization": f"Bearer {access_token}"}

    created_host_id = None
    server_id = None
    result = 1
    try:
        region = os.environ.get("LIBREBASE_HETZNER_REGION", "nbg1").strip() or "nbg1"
        st, host = http(
            "POST",
            base,
            f"/org/v1/orgs/{org_id}/hosts",
            {"name": "verify-vm", "provider": "hetzner", "region": region, "memMb": 2048},
            headers=auth,
        )
        if st != 201:
            print(f"FAIL: create host {st} {host}", file=sys.stderr)
            return 1
        server_id = host.get("serverId")
        ip = host.get("ip")
        if not server_id or not ip or host.get("status") != "provisioning":
            print(f"FAIL: host not provisioned on Hetzner: {host}", file=sys.stderr)
            return 1
        created_host_id = host["id"]
        print(f"created Hetzner server_id={server_id} ip={ip} status={host['status']}")

        # 3) Poll the REAL Hetzner API until the VM reports running (golden image booted).
        booted = False
        for _ in range(40):  # ~4 min
            time.sleep(6)
            try:
                info = hcloud.get_server(int(server_id))
            except Exception as exc:
                print(f"poll error: {exc}", file=sys.stderr)
                continue
            print(f"polling Hetzner server {server_id}: status={info['status']} ip={info['ip']}", flush=True)
            if info.get("status") == "running" and info.get("ip"):
                booted = True
                break
        if not booted:
            print("FAIL: Hetzner server did not reach running within timeout", file=sys.stderr)
            return 1

        # Host row should still be tracked (status stays provisioning until the
        # host agent registers in Phase 1).
        st, h = http("GET", base, f"/org/v1/orgs/{org_id}/hosts/{created_host_id}", headers=auth)
        assert st == 200, f"GET host {st} {h}"
        assert h.get("serverId") == server_id, f"row lost server_id: {h}"
        print(f"RESULT: PASS (Hetzner VM server_id={server_id} ip={ip} booted + host row tracks it)")
        result = 0
    finally:
        if created_host_id:
            st, _ = http("DELETE", base, f"/org/v1/orgs/{org_id}/hosts/{created_host_id}", headers=auth)
            print(f"teardown DELETE host -> {st}")
            if st != 200:
                print(f"WARN: host delete returned {st} (delete Hetzner server {server_id} manually)", file=sys.stderr)
                result = 2
        server.shutdown()
        server.server_close()
        db.close()
        tmp.cleanup()
    return result


if __name__ == "__main__":
    raise SystemExit(main())
