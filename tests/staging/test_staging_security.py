"""Defensive staging security checks against https://stage.librebase.xyz.

TLS hostname verification is required (no curl -k / CERT_NONE).
Checks: certificate hostname, public JSON must not leak internal hosts,
auth walls stay closed without credentials, basic security headers.

Does not send exploits, fuzzers, payloads, or attack procedures.
"""

from __future__ import annotations

from pathlib import Path as _P
import sys as _sys
_sys.path.insert(0, str(_P(__file__).resolve().parent))

import os
import ssl
import unittest

from https import (
    STAGING_HOST,
    leaked_internal_markers,
    request,
    request_json,
    tls_handshake,
    verified_context,
)

_RUN = os.environ.get("LIBREBASE_STAGING_CHECKS") == "1"

AUTH_WALL_GET = (
    "/api/projects",
    "/api/instances",
    "/api/hosts",
    "/api/admin/orgs",
    "/api/me/keys",
    "/api/logs",
    "/api/admin/mcp-keys",
    "/api/admin/billing",
    "/api/keys/placeholder/decrypt",
    "/api/admin-proxy/org/v1/me",
    "/api/admin-proxy/org/v1/orgs",
)

PUBLIC_JSON = (
    "/.well-known/mcp.json",
    "/.well-known/oauth-authorization-server",
)


@unittest.skipUnless(_RUN, "LIBREBASE_STAGING_CHECKS=1 not set")
class StagingSecurity(unittest.TestCase):
    def test_ssl_context_never_disables_verify(self) -> None:
        ctx = verified_context()
        self.assertTrue(ctx.check_hostname)
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)

    def test_tls_certificate_hostname_is_stage(self) -> None:
        try:
            sock = tls_handshake()
        except ssl.SSLCertVerificationError as exc:
            self.fail(
                f"TLS certificate does not match {STAGING_HOST}: {exc}. "
                "Expected SAN/CN for stage.librebase.xyz. Do not use insecure TLS."
            )
        with sock:
            cert = sock.getpeercert()
        self.assertTrue(cert)
        sans = []
        for typ, val in cert.get("subjectAltName", ()):
            if typ == "DNS":
                sans.append(val)
        self.assertIn(
            STAGING_HOST,
            sans,
            f"peer certificate SAN {sans!r} does not include {STAGING_HOST}",
        )

    def test_public_json_has_no_internal_hostname(self) -> None:
        for path in PUBLIC_JSON:
            with self.subTest(path=path):
                status, _headers, payload = request_json(path)
                self.assertEqual(status, 200, f"{path} status {status}")
                hits = leaked_internal_markers(payload)
                self.assertEqual(hits, [], f"{path} leaked internal hostnames: {hits}")

    def test_admin_proxy_status_json_has_no_internal_hostname(self) -> None:
        status, _headers, payload = request_json("/api/admin-proxy")
        if status in {401, 403}:
            return
        self.assertIsNotNone(payload, f"/api/admin-proxy status {status} produced no JSON")
        hits = leaked_internal_markers(payload)
        self.assertEqual(hits, [], f"/api/admin-proxy leaked internal hostnames: {hits}")

    def test_auth_walls_closed_without_credentials(self) -> None:
        for path in AUTH_WALL_GET:
            with self.subTest(path=path, method="GET"):
                status, _headers, body = request(path)
                self.assertNotIn(
                    status,
                    {200, 201, 204},
                    f"{path} returned {status} without credentials (body {body[:200]!r})",
                )
                self.assertIn(
                    status,
                    {401, 403, 404},
                    f"{path} expected 401/403/404 without credentials, got {status}",
                )

    def test_mutating_auth_walls_closed_without_credentials(self) -> None:
        cases = (
            ("POST", "/api/projects", b"{}"),
            ("POST", "/api/instances", b"{}"),
            ("POST", "/api/hosts", b"{}"),
            ("POST", "/api/admin/setup", b"{}"),
            ("POST", "/api/me/keys", b"{}"),
        )
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        for method, path, data in cases:
            with self.subTest(path=path, method=method):
                status, _headers, body = request(path, method=method, data=data, headers=headers)
                self.assertNotIn(
                    status,
                    {200, 201, 204},
                    f"{method} {path} returned {status} without credentials (body {body[:200]!r})",
                )
                self.assertIn(
                    status,
                    {401, 403, 404},
                    f"{method} {path} expected 401/403/404, got {status}",
                )

    def test_security_headers_on_html(self) -> None:
        status, headers, _body = request("/")
        self.assertLess(status, 500)
        self._assert_security_headers(headers, html=True)

    def test_security_headers_on_public_json(self) -> None:
        status, headers, _body = request("/.well-known/mcp.json")
        self.assertEqual(status, 200)
        self._assert_security_headers(headers, html=False)

    def _assert_security_headers(self, headers: dict[str, str], *, html: bool) -> None:
        xcto = headers.get("x-content-type-options", "").lower()
        self.assertEqual(xcto, "nosniff", f"X-Content-Type-Options={xcto!r}")

        xfo = headers.get("x-frame-options", "").upper()
        csp = headers.get("content-security-policy", "").lower()
        if html:
            framed = xfo in {"DENY", "SAMEORIGIN"} or "frame-ancestors" in csp
            self.assertTrue(
                framed,
                f"missing frame guard (X-Frame-Options={xfo!r} CSP={csp!r})",
            )

        hsts = headers.get("strict-transport-security", "").lower()
        self.assertIn("max-age=", hsts, f"missing HSTS: {hsts!r}")

        powered = headers.get("x-powered-by", "")
        self.assertEqual(powered, "", f"X-Powered-By leaked: {powered!r}")

        server = headers.get("server", "")
        hits = leaked_internal_markers(server)
        self.assertEqual(hits, [], f"Server header leaked internals: {hits}")
