"""Verified HTTPS client for https://stage.librebase.xyz.

TLS hostname verification is always on. There is no insecure / -k path.
"""

from __future__ import annotations

import json
import socket
import ssl
import urllib.error
import urllib.request
from typing import Any

STAGING_HOST = "stage.librebase.xyz"
STAGING_ORIGIN = "https://stage.librebase.xyz"
TIMEOUT = 20

# Hostnames / networks that must not appear in public JSON.
INTERNAL_MARKERS = (
    "lip.lilangverse.xyz",
    "127.0.0.1",
    "0.0.0.0",
    "localhost",
    ".internal",
    ".local",
    "192.168.",
    "10.0.",
    "10.1.",
    "10.2.",
    "172.16.",
    "172.17.",
    "172.18.",
    "172.19.",
    "172.20.",
    "172.21.",
    "172.22.",
    "172.23.",
    "172.24.",
    "172.25.",
    "172.26.",
    "172.27.",
    "172.28.",
    "172.29.",
    "172.30.",
    "172.31.",
    "engine.librebase",
    "librebase_staging",
    "librebase_admin",
    ":54330",
    ":54331",
    ":54332",
    ":3007",
)


def verified_context() -> ssl.SSLContext:
    """Default OS trust store, hostname check required. Never CERT_NONE."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    if ctx.verify_mode != ssl.CERT_REQUIRED or not ctx.check_hostname:
        raise RuntimeError("refusing to run without TLS hostname verification")
    return ctx


def tls_handshake(host: str = STAGING_HOST, port: int = 443) -> ssl.SSLObject | ssl.SSLSocket:
    """Open a TLS socket with server_hostname=host. Raises on SAN / name mismatch."""
    if host != STAGING_HOST:
        raise RuntimeError(f"staging checks only allow {STAGING_HOST}, got {host}")
    ctx = verified_context()
    raw = socket.create_connection((host, port), timeout=TIMEOUT)
    return ctx.wrap_socket(raw, server_hostname=host)


def request(
    path: str,
    *,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = TIMEOUT,
) -> tuple[int, dict[str, str], bytes]:
    """HTTPS request to staging with full certificate + hostname verification."""
    if not path.startswith("/"):
        raise ValueError("path must be absolute")
    url = STAGING_ORIGIN + path
    req = urllib.request.Request(url, data=data, method=method)
    for key, value in (headers or {}).items():
        req.add_header(key, value)
    ctx = verified_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            body = resp.read()
            hdrs = {k.lower(): v for k, v in resp.headers.items()}
            return int(resp.status), hdrs, body
    except urllib.error.HTTPError as err:
        body = err.read()
        hdrs = {k.lower(): v for k, v in err.headers.items()} if err.headers else {}
        return int(err.code), hdrs, body
    except urllib.error.URLError as err:
        reason = err.reason
        if isinstance(reason, ssl.SSLError):
            raise reason from err
        raise


def request_json(path: str, **kwargs: Any) -> tuple[int, dict[str, str], Any]:
    status, hdrs, body = request(path, **kwargs)
    parsed: Any
    try:
        parsed = json.loads(body.decode("utf-8") if body else "null")
    except json.JSONDecodeError:
        parsed = None
    return status, hdrs, parsed


def collect_strings(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, str):
        found.append(value)
    elif isinstance(value, dict):
        for key, item in value.items():
            found.append(str(key))
            found.extend(collect_strings(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(collect_strings(item))
    return found


def leaked_internal_markers(value: Any) -> list[str]:
    hits: list[str] = []
    for text in collect_strings(value):
        lower = text.lower()
        for marker in INTERNAL_MARKERS:
            if marker.lower() in lower:
                hits.append(f"{marker!r} in {text!r}")
    return hits
