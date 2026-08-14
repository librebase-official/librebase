"""Unit tests for the KMS — crypto core + key store + HTTP API."""

from __future__ import annotations

import base64
import json
import tempfile
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.request import Request, urlopen

from kms import crypto
from kms.server import KmsHandler
from kms.store import KmsStore


def _b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


class TestCryptoCore(unittest.TestCase):
    def test_envelope_wrap_unwrap(self) -> None:
        kek = crypto.generate_kek()
        dek = crypto.generate_dek()
        blob = crypto.wrap(kek, dek)
        self.assertEqual(crypto.unwrap(kek, blob), dek)

    def test_seal_open(self) -> None:
        dek = crypto.generate_dek()
        ct = crypto.seal(dek, b"hello world")
        self.assertEqual(crypto.open_seal(dek, ct), b"hello world")
        with self.assertRaises(Exception):
            crypto.open_seal(crypto.generate_dek(), ct)

    def test_ed25519_sign_verify(self) -> None:
        sk, pk = crypto.generate_ed25519()
        msg = b"sign me"
        sig = crypto.ed25519_sign(sk, msg)
        self.assertTrue(crypto.ed25519_verify(pk, msg, sig))
        self.assertFalse(crypto.ed25519_verify(pk, b"tampered", sig))
        other_sk, _ = crypto.generate_ed25519()
        self.assertFalse(crypto.ed25519_verify(pk, msg, crypto.ed25519_sign(other_sk, msg)))


class TestKmsStore(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.store = KmsStore(Path(self._tmp.name) / "kms.db")

    def tearDown(self) -> None:
        self.store.close()
        self._tmp.cleanup()

    def test_create_and_roundtrip(self) -> None:
        key = self.store.create_key("proj_1")
        self.assertEqual(key["projectId"], "proj_1")
        self.assertEqual(key["version"], 1)

        row = self.store.get_key(key["keyId"])
        ct = self.store.encrypt(row, b"secret-value")
        self.assertEqual(self.store.decrypt(row, ct), b"secret-value")

        sig = self.store.sign(row, b"message")
        self.assertTrue(self.store.verify(row, b"message", sig))

    def test_create_is_idempotent_and_rotate_versions(self) -> None:
        k1 = self.store.create_key("proj_1")
        k2 = self.store.create_key("proj_1")
        self.assertEqual(k1["version"], k2["version"])  # same default key
        k3 = self.store.rotate("proj_1", k1["keyId"])
        self.assertEqual(k3["version"], 2)

    def test_delete(self) -> None:
        key = self.store.create_key("proj_1")
        self.assertTrue(self.store.delete_key(key["keyId"]))
        self.assertIsNone(self.store.get_key(key["keyId"]))


class TestKmsHttp(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.TemporaryDirectory()
        cls.db = KmsStore(Path(cls._tmp.name) / "kms.db")
        KmsHandler.db = cls.db
        KmsHandler.service_role = "test-role"
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), KmsHandler)
        cls.port = cls.server.server_address[1]
        cls._thread = Thread(target=cls.server.serve_forever, daemon=True)
        cls._thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.db.close()
        cls._tmp.cleanup()

    def _req(self, method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
        req = Request(
            f"http://127.0.0.1:{self.port}{path}",
            data=json.dumps(body).encode() if body is not None else None,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer test-role",
            },
            method=method,
        )
        try:
            with urlopen(req) as r:
                return r.status, json.loads(r.read() or b"{}")
        except Exception as e:  # noqa: BLE001
            if hasattr(e, "code"):
                return e.code, json.loads(e.read() or b"{}")
            raise

    def test_health_and_unauthorized(self) -> None:
        with urlopen(f"http://127.0.0.1:{self.port}/health") as r:
            self.assertEqual(r.status, 200)
        req = Request(f"http://127.0.0.1:{self.port}/v1/projects/p/keys")
        try:
            urlopen(req)
            self.fail("expected 401")
        except Exception as e:  # noqa: BLE001
            self.assertEqual(e.code, 401)

    def test_full_lifecycle(self) -> None:
        st, key = self._req("POST", "/v1/projects/proj_x/keys")
        self.assertEqual(st, 201, key)
        kid = key["keyId"]

        st, enc = self._req("POST", f"/v1/projects/proj_x/keys/{kid}/encrypt", {"data": _b64e(b"hello")})
        self.assertEqual(st, 200)
        st, dec = self._req("POST", f"/v1/projects/proj_x/keys/{kid}/decrypt", {"ciphertext": enc["ciphertext"]})
        self.assertEqual(st, 200)
        self.assertEqual(crypto.b64d(dec["data"]), b"hello")

        st, sig = self._req("POST", f"/v1/projects/proj_x/keys/{kid}/sign", {"data": _b64e(b"msg")})
        self.assertEqual(st, 200)
        st, ver = self._req("POST", f"/v1/projects/proj_x/keys/{kid}/verify", {"data": _b64e(b"msg"), "signature": sig["signature"]})
        self.assertEqual(ver["valid"], True)

        st, rotated = self._req("POST", f"/v1/projects/proj_x/keys/{kid}/rotate")
        self.assertEqual(st, 200)
        self.assertEqual(rotated["version"], 2)

        st, _ = self._req("DELETE", f"/v1/projects/proj_x/keys/{kid}")
        self.assertEqual(st, 200)

    def test_internal_seal_unseal(self) -> None:
        st, sealed = self._req("POST", "/v1/internal/seal", {"project_id": "p", "plaintext": "client-secret"})
        self.assertEqual(st, 200, sealed)
        st, out = self._req("POST", "/v1/internal/unseal", {"key_id": sealed["keyId"], "ciphertext": sealed["ciphertext"]})
        self.assertEqual(st, 200)
        self.assertEqual(out["plaintext"], "client-secret")


if __name__ == "__main__":
    unittest.main()
