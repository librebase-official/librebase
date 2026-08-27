#!/usr/bin/env python3
"""Build a reusable golden Hetzner image for rented VMs.

The image has Podman + the Librebase host agent baked in, so cloud-init on each
new VM only injects networking/keys and starts the agent service. Builds a
Hetzner *snapshot* image from a throwaway base server:

  1. Create a temporary Hetzner server (Ubuntu, with your SSH key).
  2. scp the host agent + systemd unit, then ssh in and run `install_script()`
     (install Podman, drop the agent binary + unit, enable).
  3. Power off the server.
  4. Create a snapshot image from it and print the new image id.
  5. Delete the temporary server (the snapshot survives).

Gated behind LIBREBASE_HETZNER_API_TOKEN. Needs an SSH key already uploaded to
Hetzner (LIBREBASE_HETZNER_SSH_KEY_ID) and a matching private key on disk
(LIBREBASE_SSH_PRIVATE_KEY) so the script can SSH the base server.

Run:
  LIBREBASE_HETZNER_API_TOKEN=... LIBREBASE_HETZNER_SSH_KEY_ID=<id> \\
    LIBREBASE_SSH_PRIVATE_KEY=~/.ssh/hetzner \\
    python3 scripts/build_hetzner_image.py
"""
from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import hcloud

AGENT_BIN = Path("host-agent/service.py")
AGENT_SERVICE = Path("host-agent/librebase-host-agent.service")
AGENT_DEST = "/usr/local/bin/host-agent"
UNIT_DEST = "/etc/systemd/system/librebase-host-agent.service"
ENV_FILE = "/etc/librebase/host-agent.env"

DEFAULT_BASE_IMAGE = "ubuntu-22.04"


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def install_script() -> str:
    """Shell script run over SSH to bake Podman + the host agent into the image.

    The control-plane URL baked here is a placeholder — cloud-init overwrites
    /etc/librebase/host-agent.env at provisioning time (hcloud.render_cloudinit).
    """
    agent_url = (
        os.environ.get("LIBREBASE_AGENT_URL", "").strip().rstrip("/")
        or os.environ.get("LIBREBASE_CONSOLE_URL", "").strip().rstrip("/")
        or "https://app.librebase.xyz"
    )
    return (
        "set -e\n"
        "apt-get update\n"
        "apt-get install -y podman python3\n"
        "install -d /etc/librebase\n"
        f"install -m 0600 /dev/stdin {ENV_FILE} <<'EOF'\n"
        "LIBREBASE_HOST_ID=host_image\n"
        "LIBREBASE_AGENT_TOKEN=__set_at_provision_time__\n"
        f"LIBREBASE_AGENT_URL={agent_url}\n"
        "EOF\n"
        f"install -m 0755 /tmp/host-agent {AGENT_DEST}\n"
        f"install -m 0644 /tmp/librebase-host-agent.service {UNIT_DEST}\n"
        "systemctl daemon-reload\n"
        "systemctl enable librebase-host-agent\n"
        "podman --version\n"
    )


def ssh_keyfile() -> str:
    return os.environ["LIBREBASE_SSH_PRIVATE_KEY"]


def scp_cmd(host: str, port: int, src: Path, dst: str) -> list[str]:
    return [
        "scp",
        "-o", "StrictHostKeyChecking=no",
        "-o", "BatchMode=yes",
        "-i", ssh_keyfile(),
        "-P", str(port),
        str(src),
        f"root@{host}:{dst}",
    ]


def ssh_cmd(host: str, port: int, script: str) -> list[str]:
    return [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "BatchMode=yes",
        "-i", ssh_keyfile(),
        "-P", str(port),
        f"root@{host}",
        script,
    ]


def ssh_run(host: str, port: int, script: str) -> None:
    subprocess.run(ssh_cmd(host, port, script), check=True)


def scp_file(host: str, port: int, src: Path, dst: str) -> None:
    subprocess.run(scp_cmd(host, port, src, dst), check=True)


def ssh_reachable(host: str, port: int, timeout: int = 5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def wait_for_ssh(host: str, port: int, tries: int = 60) -> bool:
    for _ in range(tries):
        if ssh_reachable(host, port):
            # Give sshd a moment to be ready to accept logins.
            time.sleep(3)
            return True
        time.sleep(5)
    return False


def build_image(name: str = "librebase-host-golden") -> int:
    token()  # gate + instructions
    key_id = os.environ.get("LIBREBASE_HETZNER_SSH_KEY_ID", "").strip()
    if not key_id:
        sys.exit("set LIBREBASE_HETZNER_SSH_KEY_ID (Hetzner -> Access -> Security -> SSH Keys)")
    keyfile = os.environ.get("LIBREBASE_SSH_PRIVATE_KEY", "").strip()
    if not keyfile or not os.path.exists(keyfile):
        sys.exit("set LIBREBASE_SSH_PRIVATE_KEY to an existing private key file matching the Hetzner SSH key")

    root = repo_root()
    # Point the shared hcloud client at the base image + SSH key.
    os.environ["LIBREBASE_HETZNER_IMAGE_ID"] = (
        os.environ.get("LIBREBASE_HETZNER_BASE_IMAGE_ID", "").strip() or DEFAULT_BASE_IMAGE
    )
    os.environ["LIBREBASE_HETZNER_SSH_KEY_ID"] = key_id

    server_type = os.environ.get("LIBREBASE_HETZNER_SERVER_TYPE", "").strip() or "cx22"
    region = os.environ.get("LIBREBASE_HETZNER_REGION", "nbg1").strip()
    os.environ["LIBREBASE_HETZNER_SERVER_TYPE"] = server_type

    print(f"creating temporary base server in {region} ({server_type})...")
    created = hcloud.create_server(
        name=name + "-base",
        region=region,
        user_data=None,
    )
    # hcloud.create_server reads image/ssh key from env (set above). The returned
    # ip/status reflect the boot; we need the real server_id + ip to SSH in.
    server_id = created["server_id"]
    ip = created.get("ip")
    if not server_id or not ip:
        print(f"FAIL: base server not ready: {created}", file=sys.stderr)
        return 1
    print(f"  server_id={server_id} ip={ip}")

    try:
        if not wait_for_ssh(ip, 22):
            print("FAIL: SSH never became reachable", file=sys.stderr)
            return 1

        print("  scp host agent + unit, then install Podman...")
        scp_file(ip, 22, root / AGENT_BIN, "/tmp/host-agent")
        scp_file(ip, 22, root / AGENT_SERVICE, "/tmp/librebase-host-agent.service")
        ssh_run(ip, 22, install_script())

        print("powering off + snapshotting...")
        hcloud._request("POST", f"/servers/{server_id}/actions/poweroff")  # noqa: SLF001
        if not _wait_shutdown(ip, server_id):
            print("WARN: server did not report off; snapshot may fail", file=sys.stderr)

        resp = hcloud._request(  # noqa: SLF001
            "POST",
            f"/servers/{server_id}/actions/create_image",
            {"type": "snapshot", "description": name},
        )
        image = resp.get("image") or resp
        image_id = image["id"]
        print(f"created image_id={image_id}")
        print(f"RESULT: PASS golden image created: LIBREBASE_HETZNER_IMAGE_ID={image_id}")
        return 0
    finally:
        _cleanup(server_id)


def _wait_shutdown(ip: str, server_id, tries: int = 60) -> bool:
    import time as _t

    start = _t.time()
    while _t.time() - start < tries * 2:
        try:
            info = hcloud.get_server(int(server_id))
            if info.get("status") in ("off", "error"):
                return True
        except Exception:
            pass
        _t.sleep(2)
    return False


def _cleanup(server_id) -> None:
    if server_id:
        try:
            hcloud.delete_server(int(server_id))
        except Exception as exc:
            print(f"WARN: could not delete base server {server_id}: {exc}", file=sys.stderr)


def token() -> str:
    t = os.environ.get("LIBREBASE_HETZNER_API_TOKEN", "").strip()
    if not t:
        sys.exit(
            "Skipping golden-image build: set LIBREBASE_HETZNER_API_TOKEN\n"
            "(Hetzner Cloud console -> Access -> API Token -> Read+Write) plus\n"
            "LIBREBASE_HETZNER_SSH_KEY_ID and LIBREBASE_SSH_PRIVATE_KEY."
        )
    return t


if __name__ == "__main__":
    raise SystemExit(build_image())
