#!/usr/bin/env python3
"""Smoke: health → setup → create instance/project → list (Bearer required)."""
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

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
SERVER = SCRIPTS / "admin_server.py"


def http(method: str, url: str, body: dict | None = None, token: str | None = None):
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


def main() -> int:
    port = int(os.environ.get("LIBREBASE_ADMIN_SMOKE_PORT", "54339"))
    base = f"http://127.0.0.1:{port}"
    sys.path.insert(0, str(SCRIPTS))
    from admin_server import LiorgDb  # noqa: E402

    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "smoke.db"
        # Idempotent migrate: open twice must not fail on re-ALTER.
        LiorgDb(db).close()
        LiorgDb(db).close()

        env = {
            **os.environ,
            "LIBREBASE_ADMIN_BIND": "127.0.0.1",
            "LIBREBASE_ADMIN_PORT": str(port),
            "LIBREBASE_ADMIN_DB_PATH": str(db),
            "LIBREBASE_ADMIN_JWT_SECRET": "smoke-secret",
        }
        proc = subprocess.Popen(
            [sys.executable, str(SERVER)],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        try:
            for _ in range(40):
                time.sleep(0.1)
                try:
                    st, body = http("GET", f"{base}/health")
                    if st == 200 and body.get("ok"):
                        break
                except Exception:
                    pass
            else:
                err = proc.stderr.read().decode() if proc.stderr else ""
                print("FAIL: admin never became healthy", err, file=sys.stderr)
                return 1

            st, setup = http(
                "POST",
                f"{base}/org/v1/setup",
                {
                    "name": "Smoke Org",
                    "ownerEmail": "smoke@localhost",
                    "password": "secret",
                },
            )
            if st != 201 or "token" not in setup:
                print("FAIL: setup", st, setup, file=sys.stderr)
                return 1
            token = setup["token"]
            org_id = setup["orgId"]

            st, _ = http("GET", f"{base}/org/v1/orgs/{org_id}/projects")
            if st != 401:
                print("FAIL: unauthenticated list expected 401", st, file=sys.stderr)
                return 1

            st, inst = http(
                "POST",
                f"{base}/org/v1/orgs/{org_id}/instances",
                {"name": "smoke-inst", "ports": {"api": 15420, "postgres": 15422}},
                token=token,
            )
            if st != 201:
                print("FAIL: create instance", st, inst, file=sys.stderr)
                return 1

            st, proj = http(
                "POST",
                f"{base}/org/v1/orgs/{org_id}/projects",
                {
                    "name": "smoke-proj",
                    "instanceId": inst["id"],
                    "deploymentMode": "dedicated",
                },
                token=token,
            )
            if st != 201:
                print("FAIL: create project", st, proj, file=sys.stderr)
                return 1

            st, projects = http(
                "GET", f"{base}/org/v1/orgs/{org_id}/projects", token=token
            )
            if st != 200 or not isinstance(projects, list) or len(projects) < 1:
                print("FAIL: list projects", st, projects, file=sys.stderr)
                return 1

            # Wave 10: entitlements gate (self-host edition allows project.create)
            st, ent = http(
                "GET",
                f"{base}/org/v1/orgs/{org_id}/entitlements/project.create",
                token=token,
            )
            if st != 200 or int(ent.get("enabled", 0)) < 1:
                print("FAIL: entitlement project.create", st, ent, file=sys.stderr)
                return 1

            # Hosts: create 512MB VM, place instances, enforce budget
            st, host = http(
                "POST",
                f"{base}/org/v1/orgs/{org_id}/hosts",
                {"name": "smoke-vm", "memMb": 512},
                token=token,
            )
            if st != 201:
                print("FAIL: create host", st, host, file=sys.stderr)
                return 1
            host_id = host["id"]

            st, hinst = http(
                "POST",
                f"{base}/org/v1/orgs/{org_id}/instances",
                {"name": "hosted-inst", "hostId": host_id, "memLimitMb": 256},
                token=token,
            )
            if st != 201 or hinst.get("hostId") != host_id or hinst.get("memLimitMb") != 256:
                print("FAIL: create instance on host", st, hinst, file=sys.stderr)
                return 1

            st, over = http(
                "POST",
                f"{base}/org/v1/orgs/{org_id}/instances",
                {"name": "over-budget", "hostId": host_id, "memLimitMb": 400},
                token=token,
            )
            if st != 409:
                print("FAIL: expected host budget 409, got", st, over, file=sys.stderr)
                return 1

            st, hosts = http(
                "GET", f"{base}/org/v1/orgs/{org_id}/hosts", token=token
            )
            if st != 200 or not isinstance(hosts, list) or hosts[0]["memUsedMb"] != 256:
                print("FAIL: host mem_used", st, hosts, file=sys.stderr)
                return 1

            print(json.dumps({"ok": True, "orgId": org_id, "projectId": proj["id"], "hostId": host_id}))
            return 0
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
