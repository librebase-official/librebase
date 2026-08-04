#!/usr/bin/env python3
"""Lean in-process E2E for Phase 1 deepen (no Playwright browser).

Signup → refresh → bucket create → upload → signed GET → list buckets.
Uses lis handle_request (same process) — keep RAM low vs full stack.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_default_candidates = [
    Path(__file__).resolve().parents[2] / ".." / "lis",
    Path(__file__).resolve().parents[2] / ".." / "li" / "lis",
    Path("/workspace/lis"),
    Path(r"C:\Users\Julian\Documents\Programming\li\lis"),
]
_LIS = Path(os.environ["LIS_ROOT"]).resolve() if os.environ.get("LIS_ROOT") else None
if _LIS is None or not _LIS.is_dir():
    _LIS = next((p.resolve() for p in _default_candidates if p.is_dir()), _default_candidates[0].resolve())
sys.path.insert(0, str(_LIS))

os.environ.setdefault("LI_JWT_SECRET", "e2e-deepen-secret")
os.environ.setdefault("LI_REGISTRY_MOCK", "1")
os.environ.setdefault("LI_AUTH_BACKEND", "mock")
os.environ["LI_OAUTH_ENABLED"] = "1"
os.environ["LI_OAUTH_MOCK"] = "1"
os.environ["LI_SMTP_MOCK"] = "1"
os.environ["LI_OTP_MOCK"] = "1"


def main() -> int:
    tmp = tempfile.mkdtemp(prefix="librebase-e2e-deepen-")
    os.environ["LI_DATA_DIR"] = tmp
    os.environ["LI_STORAGE_DIR"] = str(Path(tmp) / "storage")

    from routes.auth.oauth import reset_oauth_store
    from routes.auth.store import reset_auth_store
    from routes.registry.handlers import handle_request
    from routes.storage.handlers import reset_storage_for_tests

    reset_auth_store()
    reset_oauth_store(tmp)
    reset_storage_for_tests(Path(tmp) / "storage")

    def call(method: str, path: str, *, body: dict | bytes | None = None, token: str | None = None):
        headers: dict[str, str] = {}
        raw = b""
        if isinstance(body, dict):
            raw = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        elif isinstance(body, (bytes, bytearray)):
            raw = bytes(body)
            headers["Content-Type"] = "application/octet-stream"
        if token:
            headers["Authorization"] = f"Bearer {token}"
        status, hdrs, payload = handle_request(method, path, headers=headers, body=raw)
        try:
            data = json.loads(payload.decode()) if payload else {}
        except json.JSONDecodeError:
            data = payload
        return status, hdrs, data

    st, _, signup = call(
        "POST",
        "/auth/v1/signup",
        body={"email": "e2e@librebase.test", "password": "e2e-pass-12", "publisher_name": "e2e"},
    )
    assert st == 201, signup
    refresh = signup["refresh_token"]
    access = signup["access_token"]

    st, _, refreshed = call(
        "POST",
        "/auth/v1/token?grant_type=refresh_token",
        body={"refresh_token": refresh},
    )
    assert st == 200, refreshed
    access = refreshed["access_token"]

    st, _, bucket = call(
        "POST",
        "/storage/v1/bucket",
        body={"name": "e2e-media", "public": False},
        token=access,
    )
    assert st == 200, bucket

    st, _, _ = call(
        "PUT",
        "/storage/v1/object/e2e-media/hello.txt",
        body=b"hello-e2e",
        token=access,
    )
    assert st == 200

    st, _, signed = call(
        "POST",
        "/storage/v1/object/sign/e2e-media/hello.txt",
        body={"expiresIn": 60},
        token=access,
    )
    assert st == 200, signed
    url = signed["signedURL"]
    st, _, raw = call("GET", url)
    assert st == 200
    assert raw == b"hello-e2e" or (isinstance(raw, dict) and False)

    st, _, listed = call("GET", "/storage/v1/bucket", token=access)
    assert st == 200, listed
    names = [b["name"] for b in listed["buckets"]]
    assert "e2e-media" in names


    # SigV4 canonical signed GET
    st, _, signed_v4 = call(
        "POST",
        "/storage/v1/object/sign/e2e-media/hello.txt",
        body={"expiresIn": 60, "sigv4": True},
        token=access,
    )
    assert st == 200, signed_v4
    assert signed_v4.get("shaped") == "sigv4-query-canonical", signed_v4
    st, _, raw_v4 = call("GET", signed_v4["signedURL"])
    assert st == 200
    assert raw_v4 == b"hello-e2e"

    # Magiclink + SMTP mock
    from routes.auth.smtp import reset_smtp_outbox, get_smtp_outbox
    reset_smtp_outbox()
    st, _, otp = call("POST", "/auth/v1/otp", body={"email": "e2e-otp@librebase.test", "type": "magiclink"})
    assert st == 200, otp
    assert otp.get("email_delivery", {}).get("delivered") is True
    assert get_smtp_outbox(), "smtp outbox empty"
    st, _, sess = call(
        "POST",
        "/auth/v1/verify",
        body={"email": "e2e-otp@librebase.test", "token": otp["token"], "type": "magiclink"},
    )
    assert st == 200, sess
    assert sess.get("access_token")

    # GitHub OAuth (mock)
    status, _, payload = handle_request(
        "GET",
        "/auth/v1/authorize?provider=github&format=json",
        headers={"Accept": "application/json"},
    )
    start = json.loads(payload.decode())
    assert status == 200, start
    state = start["state"]
    status, _, payload = handle_request(
        "GET",
        f"/auth/v1/callback?provider=github&code=mock_e2e-oauth@librebase.test&state={state}",
    )
    oauth_sess = json.loads(payload.decode())
    assert status == 200, oauth_sess
    assert oauth_sess.get("access_token")
    assert oauth_sess.get("provider") == "github"

    print("e2e deepen: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
