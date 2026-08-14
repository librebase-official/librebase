"""Librebase KMS — HTTP service (interim Python, stdlib server).

Customer-facing key management: per-project keys with encrypt/decrypt,
sign/verify, rotation, and key lifecycle. Service-role bearer gated.

Env:
  LIBREBASE_KMS_BIND      (default 0.0.0.0)
  LIBREBASE_KMS_PORT      (default 54340)
  LIBREBASE_KMS_DB_PATH   (default ~/.local/share/librebase/kms.db)
  LIBREBASE_KMS_SERVICE_ROLE  (bearer token; required)
"""

from __future__ import annotations

import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from . import crypto
from .store import DEFAULT_DB, KmsStore


def _json(status: int, payload: Any) -> tuple[int, dict[str, str], bytes]:
    body = json.dumps(payload).encode()
    return status, {"Content-Type": "application/json", "Content-Length": str(len(body))}, body


class KmsHandler(BaseHTTPRequestHandler):
    db: KmsStore
    service_role: str

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, status: int, payload: Any) -> None:
        status, headers, body = _json(status, payload)
        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _authed(self) -> bool:
        auth = self.headers.get("Authorization", "")
        expected = f"Bearer {self.service_role}"
        if self.service_role and auth == expected:
            return True
        self._send(401, {"error": "unauthorized"})
        return False

    def _body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path == "/health":
            self._send(200, {"ok": True})
            return
        if not self._authed():
            return
        m = re.fullmatch(r"/v1/projects/([^/]+)/keys", path)
        if m:
            self._send(200, {"keys": self.db.list_keys(m.group(1))})
            return
        m = re.fullmatch(r"/v1/projects/([^/]+)/keys/([^/]+)/public", path)
        if m:
            key = self.db.get_key_public(m.group(2))
            if not key or key["project_id"] != m.group(1):
                self._send(404, {"error": "key not found"})
                return
            self._send(200, {"keyId": key["keyId"], "publicKey": key["publicKey"], "version": key["version"]})
            return
        self._send(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path.rstrip("/") or "/"
        if not self._authed():
            return
        body = self._body()

        m = re.fullmatch(r"/v1/projects/([^/]+)/keys", path)
        if m:
            self._send(201, self.db.create_key(m.group(1)))
            return

        m = re.fullmatch(r"/v1/projects/([^/]+)/keys/([^/]+)/encrypt", path)
        if m:
            key = self.db.get_key(m.group(2))
            if not key or key["project_id"] != m.group(1):
                self._send(404, {"error": "key not found"})
                return
            data = crypto.b64d(str(body.get("data", "")))
            self._send(200, {"ciphertext": self.db.encrypt(key, data), "keyId": key["key_id"], "version": key["version"]})
            return

        m = re.fullmatch(r"/v1/projects/([^/]+)/keys/([^/]+)/decrypt", path)
        if m:
            key = self.db.get_key(m.group(2))
            if not key or key["project_id"] != m.group(1):
                self._send(404, {"error": "key not found"})
                return
            try:
                plain = self.db.decrypt(key, str(body.get("ciphertext", "")))
            except Exception:  # noqa: BLE001
                self._send(400, {"error": "decryption failed"})
                return
            self._send(200, {"data": crypto.b64e(plain)})
            return

        m = re.fullmatch(r"/v1/projects/([^/]+)/keys/([^/]+)/sign", path)
        if m:
            key = self.db.get_key(m.group(2))
            if not key or key["project_id"] != m.group(1):
                self._send(404, {"error": "key not found"})
                return
            data = crypto.b64d(str(body.get("data", "")))
            self._send(200, {"signature": self.db.sign(key, data)})
            return

        m = re.fullmatch(r"/v1/projects/([^/]+)/keys/([^/]+)/verify", path)
        if m:
            key = self.db.get_key(m.group(2))
            if not key or key["project_id"] != m.group(1):
                self._send(404, {"error": "key not found"})
                return
            data = crypto.b64d(str(body.get("data", "")))
            valid = self.db.verify(key, data, str(body.get("signature", "")))
            self._send(200, {"valid": valid})
            return

        m = re.fullmatch(r"/v1/projects/([^/]+)/keys/([^/]+)/rotate", path)
        if m:
            rotated = self.db.rotate(m.group(1), m.group(2))
            self._send(200, rotated)
            return

        # Internal: envelope-seal a project secret (used by admin-api for
        # provider client_secret storage).
        if path == "/v1/internal/seal":
            project = str(body.get("project_id", "")).strip()
            plaintext = str(body.get("plaintext", "")).encode("utf-8")
            if not project:
                self._send(400, {"error": "project_id required"})
                return
            pub = self.db.create_key(project)
            row = self.db.get_key(pub["keyId"])
            self._send(200, {"ciphertext": self.db.encrypt(row, plaintext), "keyId": pub["keyId"]})
            return

        if path == "/v1/internal/unseal":
            key_id = str(body.get("key_id", "")).strip()
            ciphertext = str(body.get("ciphertext", ""))
            key = self.db.get_key(key_id)
            if not key:
                self._send(404, {"error": "key not found"})
                return
            try:
                plain = self.db.decrypt(key, ciphertext)
            except Exception:  # noqa: BLE001
                self._send(400, {"error": "decryption failed"})
                return
            self._send(200, {"plaintext": plain.decode("utf-8", errors="replace")})
            return

        self._send(404, {"error": "not found"})

    def do_DELETE(self) -> None:  # noqa: N802
        path = urlparse(self.path).path.rstrip("/") or "/"
        if not self._authed():
            return
        m = re.fullmatch(r"/v1/projects/([^/]+)/keys/([^/]+)", path)
        if m:
            key = self.db.get_key(m.group(2))
            if not key or key["project_id"] != m.group(1):
                self._send(404, {"error": "key not found"})
                return
            self.db.delete_key(m.group(2))
            self._send(200, {"ok": True})
            return
        self._send(404, {"error": "not found"})


def main() -> None:
    host = os.environ.get("LIBREBASE_KMS_BIND", "0.0.0.0")
    port = int(os.environ.get("LIBREBASE_KMS_PORT", "54340"))
    db_path = Path(os.environ.get("LIBREBASE_KMS_DB_PATH", str(DEFAULT_DB)))
    service_role = os.environ.get("LIBREBASE_KMS_SERVICE_ROLE", "")

    if not service_role:
        sys.stderr.write("warning: LIBREBASE_KMS_SERVICE_ROLE not set; auth accepts any bearer\n")

    db = KmsStore(db_path)
    KmsHandler.db = db
    KmsHandler.service_role = service_role

    server = ThreadingHTTPServer((host, port), KmsHandler)
    sys.stderr.write(f"librebase-kms listening on http://{host}:{port} db={db_path}\n")
    try:
        server.serve_forever()
    finally:
        db.close()


if __name__ == "__main__":
    main()
