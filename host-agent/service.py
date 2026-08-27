#!/usr/bin/env python3
"""Librebase host agent — runs on each rented VM.

Pure-stdlib control plane that lives on a Hetzner VM and is responsible for the
instance containers on that host:

  - registers itself with admin-api using the bearer token injected via
    cloud-init (`/etc/librebase/host-agent.env`), flipping the host
    `provisioning -> running`.
  - polls `GET /org/v1/host-agent/instances` (scoped to this host by token) and
    reconciles the matching Podman containers (run/stop/restart).
  - heartbeats so admin-api knows the box is alive.

Swappable seams (`_podman_*`, `_http`) make the reconcile loop unit-testable
without Podman or a network.

Config (env, from cloud-init):
  LIBREBASE_HOST_ID        host row id (host_<hex>)
  LIBREBASE_AGENT_TOKEN    bearer token bound at provisioning time
  LIBREBASE_ADMIN_URL      e.g. https://app.librebase.xyz (the console proxy -> admin)
  LIDB_RUNTIME_IMAGE       container image (default ghcr.io/librebase-official/lidb-runtime:latest)
  LIBREBASE_PODMAN_BIN     (tests) override the `podman` binary
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from typing import Any

RECONCILE_INTERVAL = int(os.environ.get("LIBREBASE_AGENT_RECONCILE_SECONDS", "20"))
HEARTBEAT_INTERVAL = int(os.environ.get("LIBREBASE_AGENT_HEARTBEAT_SECONDS", "30"))
RUNTIME_IMAGE = os.environ.get(
    "LIDB_RUNTIME_IMAGE", "ghcr.io/librebase-official/lidb-runtime:latest"
)


def podman_bin() -> str:
    return os.environ.get("LIBREBASE_PODMAN_BIN", "podman")


def admin_url() -> str:
    """Control-plane base URL for the agent.

    cloud-init writes LIBREBASE_AGENT_URL into /etc/librebase/host-agent.env;
    accept that or the legacy LIBREBASE_ADMIN_URL so the stack deploys to any
    machine without edits.
    """
    return (
        os.environ.get("LIBREBASE_AGENT_URL", "").strip().rstrip("/")
        or os.environ.get("LIBREBASE_ADMIN_URL", "").strip().rstrip("/")
        or "https://app.librebase.xyz"
    )


def _req(method: str, path: str, body: Any = None) -> tuple[int, Any]:
    url = admin_url() + path
    data = json.dumps(body).encode() if body is not None else None
    headers: dict[str, str] = {}
    token = os.environ.get("LIBREBASE_AGENT_TOKEN", "")
    if token:
        headers["Authorization"] = "Bearer " + token
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            raw = res.read().decode() or "{}"
            return res.status, json.loads(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode() or "{}"
        try:
            parsed = json.loads(raw)
        except ValueError:
            parsed = raw
        return exc.code, parsed


def container_name(instance_id: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "-", instance_id)
    return "librebase-" + safe[:64]


def _podman_run(instance: dict[str, Any]) -> tuple[bool, str]:
    name = container_name(instance["id"])
    ports = instance.get("ports") or {}
    api_port = int(ports.get("api", 54320))
    pg_port = int(ports.get("postgres", 54322))
    data_dir = instance.get("dataDir") or ("/var/lib/librebase/%s" % instance["id"])
    cmd = [
        podman_bin(),
        "run", "-d",
        "--name", name,
        "--restart=unless-stopped",
        "-p", "%d:%d" % (api_port, api_port),
        "-p", "%d:%d" % (pg_port, pg_port),
        "-v", "%s:/data" % data_dir,
        "-e", "LIDB_RUNTIME_MODE=production",
        "-e", "LIBREBASE_API_PORT=%d" % api_port,
        "-e", "LIBREBASE_PG_PORT=%d" % pg_port,
        "-e", "LI_DATA_DIR=/data",
        RUNTIME_IMAGE,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if res.returncode != 0:
        return False, (res.stderr or res.stdout).strip()
    return True, (res.stdout or "").strip()


def _podman_rm(name: str) -> tuple[bool, str]:
    res = subprocess.run([podman_bin(), "rm", "-f", name], capture_output=True, text=True, timeout=60)
    if res.returncode != 0:
        return False, (res.stderr or res.stdout).strip()
    return True, ""


def _podman_ps() -> list[str]:
    res = subprocess.run(
        [podman_bin(), "ps", "-q", "--filter", "name=librebase-"],
        capture_output=True, text=True, timeout=30,
    )
    if res.returncode != 0:
        return []
    return [c for c in (res.stdout or "").splitlines() if c.strip()]


def _running_containers() -> set[str]:
    res = subprocess.run(
        [podman_bin(), "ps", "-q", "--format", "{{.Names}}"],
        capture_output=True, text=True, timeout=30,
    )
    if res.returncode != 0:
        return set()
    names = set()
    for line in (res.stdout or "").splitlines():
        n = line.strip()
        if n.startswith("librebase-"):
            names.add(n)
    return names


def register() -> bool:
    host_id = os.environ.get("LIBREBASE_HOST_ID", "")
    if not host_id or not os.environ.get("LIBREBASE_AGENT_TOKEN"):
        return False
    # Public IPv4 of this VM (best-effort; Hetzner already knows it).
    ip = _detect_ip()
    body = {"hostId": host_id, "ip": ip}
    st, data = _req("POST", "/org/v1/host-agent/register", body)
    return st == 200


def heartbeat() -> None:
    host_id = os.environ.get("LIBREBASE_HOST_ID", "")
    if host_id:
        _req("POST", "/org/v1/host-agent/heartbeat", {"hostId": host_id})


def _detect_ip() -> str | None:
    try:
        with urllib.request.urlopen("https://1.1.1.1/cdn-cgi/trace", timeout=5) as res:
            for line in res.read().decode(errors="replace").splitlines():
                if line.startswith("ip="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        return None
    return None


def list_instances() -> list[dict[str, Any]]:
    st, data = _req("GET", "/org/v1/host-agent/instances")
    if st != 200 or not isinstance(data, list):
        return []
    return data


def reconcile() -> dict[str, int]:
    """Ensure Podman containers match the host's assigned instances."""
    desired = list_instances()
    wanted = {container_name(i["id"]): i for i in desired}
    running = _running_containers()
    started = 0
    stopped = 0
    for name, inst in wanted.items():
        if name in running:
            continue
        ok, msg = _podman_run(inst)
        if ok:
            started += 1
        else:
            sys.stderr.write("host-agent: run %s failed: %s\n" % (inst.get("id"), msg))
    for name in running:
        if name not in wanted:
            _podman_rm(name)
            stopped += 1
    return {"started": started, "stopped": stopped, "desired": len(wanted), "running": len(running)}


def loop(once: bool = False) -> None:
    last_heartbeat = 0.0
    last_reconcile = 0.0
    while True:
        now = time.time()
        if now - last_heartbeat >= HEARTBEAT_INTERVAL:
            heartbeat()
            last_heartbeat = now
        if now - last_reconcile >= RECONCILE_INTERVAL:
            reconcile()
            last_reconcile = now
        if once:
            break
        time.sleep(1)


def main() -> int:
    if not os.environ.get("LIBREBASE_HOST_ID") or not os.environ.get("LIBREBASE_AGENT_TOKEN"):
        sys.exit("host-agent requires LIBREBASE_HOST_ID + LIBREBASE_AGENT_TOKEN (injected by cloud-init)")
    if not register():
        sys.stderr.write("host-agent: initial registration failed; retrying in background\n")
    loop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
