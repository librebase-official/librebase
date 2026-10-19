"""HTTP e2e against https://stage.librebase.xyz (verified TLS only).

Set LIBREBASE_STAGING_CHECKS=1 (CI staging-e2e job does this). There is no
insecure TLS fallback: a SAN/hostname mismatch must fail the job.
"""

from __future__ import annotations

from pathlib import Path as _P
import sys as _sys
_sys.path.insert(0, str(_P(__file__).resolve().parent))

import os
import ssl
import unittest

from https import STAGING_HOST, STAGING_ORIGIN, request, request_json, tls_handshake

_RUN = os.environ.get("LIBREBASE_STAGING_CHECKS") == "1"


@unittest.skipUnless(_RUN, "LIBREBASE_STAGING_CHECKS=1 not set")
class StagingE2E(unittest.TestCase):
    def test_origin_is_stage_librebase(self) -> None:
        self.assertEqual(STAGING_ORIGIN, "https://stage.librebase.xyz")
        self.assertEqual(STAGING_HOST, "stage.librebase.xyz")

    def test_tls_handshake_verifies_hostname(self) -> None:
        try:
            sock = tls_handshake()
        except ssl.SSLCertVerificationError as exc:
            self.fail(
                f"TLS hostname verification failed for {STAGING_HOST}: {exc}. "
                "Do not disable verification; fix the certificate SAN."
            )
        with sock:
            self.assertEqual(sock.server_hostname, STAGING_HOST)

    def test_home_responds_html(self) -> None:
        status, headers, body = request("/")
        self.assertLess(status, 500, f"GET / returned {status}")
        self.assertIn(status, {200, 302, 303, 307, 308})
        ctype = headers.get("content-type", "")
        if status == 200:
            self.assertTrue(
                "text/html" in ctype or "text/plain" in ctype or "application/json" in ctype,
                f"unexpected content-type {ctype!r}",
            )
            self.assertTrue(body, "empty body")

    def test_login_page(self) -> None:
        status, _headers, body = request("/login")
        self.assertIn(status, {200, 302, 303, 307, 308})
        self.assertLess(status, 500)
        if status == 200:
            text = body.decode("utf-8", errors="replace").lower()
            self.assertTrue(
                "login" in text or "sign" in text or "librebase" in text,
                "login page missing expected copy",
            )

    def test_well_known_mcp_json(self) -> None:
        status, headers, payload = request_json("/.well-known/mcp.json")
        self.assertEqual(status, 200, f"mcp.json status {status}")
        self.assertIn("application/json", headers.get("content-type", ""))
        self.assertIsInstance(payload, dict)
        blob = str(payload)
        self.assertIn(STAGING_HOST, blob)
        self.assertNotIn("app.librebase.xyz", blob)

    def test_oauth_metadata_json(self) -> None:
        status, _headers, payload = request_json("/.well-known/oauth-authorization-server")
        self.assertEqual(status, 200)
        self.assertIsInstance(payload, dict)
        issuer = str(payload.get("issuer") or "")
        self.assertTrue(
            issuer.startswith(STAGING_ORIGIN),
            f"issuer should be staging origin, got {issuer!r}",
        )

    def test_llms_txt(self) -> None:
        status, headers, body = request("/llms.txt")
        self.assertEqual(status, 200)
        ctype = headers.get("content-type", "")
        self.assertTrue("text/plain" in ctype or "text/markdown" in ctype, ctype)
        text = body.decode("utf-8", errors="replace")
        self.assertIn("Librebase", text)
        self.assertIn(STAGING_ORIGIN, text)

    def test_for_agents_page(self) -> None:
        status, _headers, body = request("/for-agents")
        self.assertIn(status, {200, 302, 303, 307, 308})
        self.assertLess(status, 500)
        if status == 200:
            self.assertTrue(body)

    def test_mcp_endpoint_exists(self) -> None:
        status, _headers, _body = request("/api/mcp")
        self.assertNotEqual(status, 404)
        self.assertLess(status, 500)
