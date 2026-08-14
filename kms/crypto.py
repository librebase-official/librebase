"""KMS crypto core — envelope encryption (AES-256-GCM) + Ed25519 sign/verify.

Interim Python implementation (mirrors the admin-api "interim until li-httpd/
lic/lidb land" pattern); the pure-Li port will swap in once li-crypto exposes
high-level seal/open + sign/verify.

Envelope model:
  KEK (root master key, 32B) wraps per-project DEKs (32B).
  Data is sealed with the DEK via AES-256-GCM (nonce + ct + tag).
  Each project key also carries an Ed25519 keypair (sign/verify); the private
  key is wrapped by the KEK at rest.
"""

from __future__ import annotations

import base64
import secrets

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

KEK_BYTES = 32
DEK_BYTES = 32
NONCE_BYTES = 12

ED25519_SK_BYTES = 32
ED25519_PK_BYTES = 32


def b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def generate_kek() -> bytes:
    return secrets.token_bytes(KEK_BYTES)


def generate_dek() -> bytes:
    return secrets.token_bytes(DEK_BYTES)


def wrap(kek: bytes, data: bytes) -> str:
    """Envelope-wrap `data` with the KEK (AES-256-GCM)."""
    nonce = secrets.token_bytes(NONCE_BYTES)
    ct = AESGCM(kek).encrypt(nonce, data, None)
    return b64e(nonce + ct)


def unwrap(kek: bytes, blob: str) -> bytes:
    raw = b64d(blob)
    return AESGCM(kek).decrypt(raw[:NONCE_BYTES], raw[NONCE_BYTES:], None)


def seal(dek: bytes, plaintext: bytes) -> str:
    nonce = secrets.token_bytes(NONCE_BYTES)
    ct = AESGCM(dek).encrypt(nonce, plaintext, None)
    return b64e(nonce + ct)


def open_seal(dek: bytes, blob: str) -> bytes:
    raw = b64d(blob)
    return AESGCM(dek).decrypt(raw[:NONCE_BYTES], raw[NONCE_BYTES:], None)


def generate_ed25519() -> tuple[bytes, bytes]:
    sk = Ed25519PrivateKey.generate()
    return sk.private_bytes_raw(), sk.public_key().public_bytes_raw()


def ed25519_sign(sk_raw: bytes, message: bytes) -> bytes:
    return Ed25519PrivateKey.from_private_bytes(sk_raw).sign(message)


def ed25519_verify(pk_raw: bytes, message: bytes, signature: bytes) -> bool:
    try:
        Ed25519PublicKey.from_public_bytes(pk_raw).verify(signature, message)
        return True
    except InvalidSignature:
        return False
