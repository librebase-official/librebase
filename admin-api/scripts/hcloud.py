#!/usr/bin/env python3
"""Hetzner Cloud substrate for rented VMs.

Stdlib-only HTTP client against the Hetzner Cloud v1 API. All network access
funnels through the module-level ``_request`` helper so tests can swap in a
fake (either by monkeypatching ``_request`` or by pointing
``LIBREBASE_HETZNER_API_URL`` at a mock server).

Env:
  LIBREBASE_HETZNER_API_TOKEN  (required for create/destroy/get)
  LIBREBASE_HETZNER_API_URL    (optional; defaults to https://api.hetzner.cloud/v1;
                               point at a mock for tests)
  LIBREBASE_HETZNER_SSH_KEY_ID (optional; default 0 = reuse project key)
  LIBREBASE_HETZNER_IMAGE_ID   (optional; base snapshot image for the golden image)
  LIBREBASE_HETZNER_SERVER_TYPE (optional; default "cx22")
  LIBREBASE_SSH_PUBLIC_KEY     (optional; the runtime's SSH key, for status probes)
"""
from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


class HcloudError(Exception):
    """Non-2xx from the Hetzner Cloud API."""

    def __init__(self, method: str, path: str, status: int, body: str):
        super().__init__(f"Hetzner {method} {path} -> {status}: {body}")
        self.method = method
        self.path = path
        self.status = status
        self.body = body


def hcloud_configured() -> bool:
    return bool(os.environ.get("LIBREBASE_HETZNER_API_TOKEN", "").strip())


def hcloud_api_key() -> str:
    token = os.environ.get("LIBREBASE_HETZNER_API_TOKEN", "").strip()
    if not token:
        raise HcloudError("GET", "/servers", 401, "LIBREBASE_HETZNER_API_TOKEN not set")
    return token


def hcloud_base() -> str:
    return (
        os.environ.get("LIBREBASE_HETZNER_API_URL", "").strip()
        or "https://api.hetzner.cloud/v1"
    )


def hcloud_ssh_key_id() -> int | None:
    raw = os.environ.get("LIBREBASE_HETZNER_SSH_KEY_ID", "").strip()
    if raw:
        try:
            return int(raw)
        except ValueError:
            return None
    return None


def hcloud_image_id() -> int | None:
    raw = os.environ.get("LIBREBASE_HETZNER_IMAGE_ID", "").strip()
    if raw:
        try:
            return int(raw)
        except ValueError:
            return None
    return None


def hcloud_server_type() -> str:
    return os.environ.get("LIBREBASE_HETZNER_SERVER_TYPE", "").strip() or "cx23"


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {hcloud_api_key()}",
        "Content-Type": "application/json",
        "User-Agent": "librebase-admin-api",
    }


def _request(method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    """Single network chokepoint. Tests may monkeypatch this."""
    url = hcloud_base().rstrip("/") + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers=_headers())
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            raw = res.read()
            status = res.status
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        status = exc.code
        exc.close()
    if status >= 400:
        raise HcloudError(method, path, status, raw.decode("utf-8", errors="replace"))
    if not raw:
        return {}
    return json.loads(raw.decode("utf-8"))


def _ipv4(server: dict[str, Any]) -> str | None:
    public = server.get("public_net") or {}
    ipv4 = public.get("ipv4") or {}
    if isinstance(ipv4, dict):
        return ipv4.get("ip")
    return None


def get_server(server_id: int) -> dict[str, Any]:
    """GET /servers/{id} -> normalized {status, ip, name}."""
    payload = _request("GET", f"/servers/{server_id}")
    server = payload.get("server") or payload
    return {
        "status": server.get("status"),
        "ip": _ipv4(server),
        "name": server.get("name"),
    }


def delete_server(server_id: int) -> None:
    _request("DELETE", f"/servers/{server_id}")


def power_off_server(server_id: int) -> None:
    """Gracefully shut down a Hetzner server (poweroff action)."""
    _request("POST", f"/servers/{server_id}/actions/poweroff")


def power_on_server(server_id: int) -> None:
    """Start a powered-off Hetzner server."""
    _request("POST", f"/servers/{server_id}/actions/poweron")


def render_cloudinit(host_id: str, agent_token: str) -> str:
    """Self-contained cloud-init that boots a working Librebase host.

    Ships the host agent + systemd unit inline (base64) and installs Podman if
    the base image lacks it, so provisioning works on any Ubuntu image — no
    golden image required. The agent reaches the control plane via
    LIBREBASE_AGENT_URL, falling back to LIBREBASE_CONSOLE_URL.
    """
    agent_url = (
        os.environ.get("LIBREBASE_AGENT_URL", "").strip().rstrip("/")
        or os.environ.get("LIBREBASE_CONSOLE_URL", "").strip().rstrip("/")
        or "https://app.librebase.xyz"
    )
    agent_b64, unit_b64 = _agent_files_b64()
    return (
        "#cloud-config\n"
        "write_files:\n"
        "  - path: /etc/librebase/host-agent.env\n"
        "    owner: root:root\n"
        "    permissions: '0600'\n"
        "    content: |\n"
        f"      LIBREBASE_HOST_ID={host_id}\n"
        f"      LIBREBASE_AGENT_TOKEN={agent_token}\n"
        f"      LIBREBASE_AGENT_URL={agent_url}\n"
        "  - path: /usr/local/bin/host-agent\n"
        "    owner: root:root\n"
        "    permissions: '0755'\n"
        "    encoding: b64\n"
        f"    content: {agent_b64}\n"
        "  - path: /etc/systemd/system/librebase-host-agent.service\n"
        "    owner: root:root\n"
        "    permissions: '0644'\n"
        "    encoding: b64\n"
        f"    content: {unit_b64}\n"
        "runcmd:\n"
        "  - [sh, -c, \"which podman >/dev/null 2>&1 || (apt-get update && apt-get install -y podman)\"]\n"
        "  - systemctl daemon-reload\n"
        "  - systemctl enable --now librebase-host-agent\n"
    )


def _agent_files_b64() -> tuple[str, str]:
    """Read the host-agent payloads as base64, resolving them relative to this
    module (container: /app/host-agent; dev repo: admin-api/../host-agent)."""
    import base64

    here = Path(__file__).resolve().parent
    for candidate in (
        here.parent / "host-agent",
        here.parent.parent / "host-agent",
        here / "host-agent",
    ):
        agent = candidate / "service.py"
        unit = candidate / "librebase-host-agent.service"
        if agent.is_file() and unit.is_file():
            return (
                base64.b64encode(agent.read_bytes()).decode(),
                base64.b64encode(unit.read_bytes()).decode(),
            )
    # Last resort: read from this repo via env override.
    override = (
        os.environ.get("LIBREBASE_HOST_AGENT_SOURCE_DIR", "").strip()
    )
    if override:
        agent = Path(override) / "service.py"
        unit = Path(override) / "librebase-host-agent.service"
        if agent.is_file() and unit.is_file():
            return (
                base64.b64encode(agent.read_bytes()).decode(),
                base64.b64encode(unit.read_bytes()).decode(),
            )
    raise FileNotFoundError(
        "host-agent/service.py + librebase-host-agent.service not found next to hcloud.py"
    )


def create_server(
    name: str,
    region: str,
    image_id: int | None = None,
    ssh_key_ids: list[int] | None = None,
    user_data: str | None = None,
) -> dict[str, Any]:
    """POST /servers -> normalized {server_id, ip, status}."""
    if region and region != "local":
        location = region
    else:
        location = None
    body: dict[str, Any] = {
        "name": name,
        "server_type": hcloud_server_type(),
        "start_after_create": True,
    }
    if image_id is not None:
        body["image"] = image_id
    else:
        img = hcloud_image_id()
        if img is not None:
            body["image"] = img
        else:
            # No custom snapshot configured — fall back to a public Ubuntu image
            # name (Hetzner accepts image names in addition to IDs).
            body["image"] = "ubuntu-24.04"
    if ssh_key_ids:
        body["ssh_keys"] = ssh_key_ids
    elif hcloud_ssh_key_id() is not None:
        body["ssh_keys"] = [hcloud_ssh_key_id()]
    if location:
        body["location"] = location
    if user_data is not None:
        body["user_data"] = user_data
    payload = _request("POST", "/servers", body)
    server = payload.get("server") or payload
    return {
        "server_id": server.get("id"),
        "ip": _ipv4(server),
        "status": server.get("status"),
    }


def provision_host(
    host_id: str,
    name: str,
    region: str,
    agent_token: str,
) -> dict[str, Any]:
    """Create the real Hetzner server for a host and return its identity."""
    user_data = render_cloudinit(host_id, agent_token)
    created = create_server(
        name=name or f"lb-{host_id}",
        region=region,
        user_data=user_data,
    )
    return {
        "server_id": created["server_id"],
        "ip": created["ip"],
    }
