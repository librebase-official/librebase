#!/usr/bin/env python3
"""Librebase Admin HTTP server — SQLite backend for Librebase Studio (self-host).

Cloud deployments use the same SQL schema via lidb embed through src/seam.li; this Python
shim is the interim self-host runtime until li-httpd + lic seam + lidb land together.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
import struct
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, urlencode, urlparse

ROOT = Path(__file__).resolve().parent.parent
MIGRATIONS = ROOT / "migrations"

DEFAULT_DB = Path.home() / ".local" / "share" / "librebase" / "org.db"
JWT_TTL_SECONDS = 60 * 60 * 24 * 7  # legacy; replaced by ACCESS_TTL for console sessions
ACCESS_TTL_SECONDS = 15 * 60  # access JWT lifetime (short-lived)
REFRESH_TTL_SECONDS = 60 * 60 * 24 * 30  # refresh token lifetime (rotated)

try:  # Argon2id when available; stdlib scrypt fallback otherwise
    from argon2 import PasswordHasher as _Argon2Hasher
    from argon2.exceptions import InvalidHashError as _Argon2InvalidHash
    from argon2.exceptions import VerifyMismatchError as _Argon2Mismatch

    _ARGON2_HASHER = _Argon2Hasher(time_cost=3, memory_cost=64 * 1024, parallelism=2)
    _ARGON2 = True
except Exception:  # pragma: no cover - fallback path
    _ARGON2_HASHER = None
    _ARGON2 = False

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1

RESET_TTL_SECONDS = 60 * 60  # password reset link lifetime (1h)
VERIFY_TTL_SECONDS = 60 * 60 * 24 * 7  # email verification link lifetime (7d)

MAX_LOGIN_ATTEMPTS = 5  # failed attempts before account lockout
LOCKOUT_SECONDS = 15 * 60  # lockout duration (15 min)
IP_WINDOW_SECONDS = 60  # per-IP login rate-limit window
IP_MAX_ATTEMPTS = 20  # max login POSTs per IP per window


def admin_dev_mode() -> bool:
    return os.environ.get("LIBREBASE_ADMIN_DEV", "").strip().lower() in ("1", "true", "yes")


def login_locked(db: "LiorgDb", email: str) -> bool:
    row = db.fetchone("SELECT * FROM login_attempts WHERE email = ?", (email,))
    if not row or not row["locked_until"]:
        return False
    return row["locked_until"] > utc_now()


def record_login_failure(db: "LiorgDb", email: str) -> None:
    now = utc_now()
    row = db.fetchone("SELECT * FROM login_attempts WHERE email = ?", (email,))
    if row:
        count = row["failed_count"] + 1
        locked_until = None
        if count >= MAX_LOGIN_ATTEMPTS:
            locked_until = utc_now_offset(LOCKOUT_SECONDS)
            count = 0  # reset so post-expiry gets a fresh budget
        db.execute(
            "UPDATE login_attempts SET failed_count = ?, last_failed_at = ?, locked_until = ? "
            "WHERE email = ?",
            (count, now, locked_until, email),
        )
    else:
        db.execute(
            "INSERT INTO login_attempts (email, failed_count, last_failed_at, locked_until) "
            "VALUES (?, ?, ?, NULL)",
            (email, 1, now),
        )


def clear_login_failures(db: "LiorgDb", email: str) -> None:
    db.execute("DELETE FROM login_attempts WHERE email = ?", (email,))


# --- TOTP (RFC 6238 / HOTP RFC 4226, stdlib-only) + recovery codes ---
RECOVERY_CODES_COUNT = 8
TOTP_STEP = 30
TOTP_DIGITS = 6
TOTP_ISSUER = "Librebase"


def _b32decode(secret: str) -> bytes:
    return base64.b32decode(secret + "=" * (-len(secret) % 8))


def totp_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")


def totp_code(secret: str, counter: int, digits: int = TOTP_DIGITS) -> str:
    key = _b32decode(secret)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = (struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF) % (10**digits)
    return str(value).zfill(digits)


def totp_now(secret: str, step: int = TOTP_STEP, digits: int = TOTP_DIGITS) -> str:
    return totp_code(secret, int(time.time()) // step, digits)


def totp_verify(secret: str, code: str, step: int = TOTP_STEP, window: int = 1) -> bool:
    if not secret:
        return False
    code = code.strip()
    counter = int(time.time()) // step
    for w in range(-window, window + 1):
        if hmac.compare_digest(totp_code(secret, counter + w), code):
            return True
    return False


def totp_uri(secret: str, email: str, issuer: str = TOTP_ISSUER) -> str:
    label = quote(f"{issuer}:{email}")
    return (
        f"otpauth://totp/{label}?secret={secret}&issuer={quote(issuer)}"
        f"&algorithm=SHA1&digits={TOTP_DIGITS}&period={TOTP_STEP}"
    )


def generate_recovery_codes(
    db: "LiorgDb", user_id: str, count: int = RECOVERY_CODES_COUNT
) -> list[str]:
    db.execute("DELETE FROM recovery_codes WHERE user_id = ?", (user_id,))
    codes: list[str] = []
    now = utc_now()
    for _ in range(count):
        code = secrets.token_urlsafe(9)
        codes.append(code)
        db.execute(
            "INSERT INTO recovery_codes (user_id, code_hash, created_at) VALUES (?, ?, ?)",
            (user_id, hash_token(code), now),
        )
    return codes


def verify_recovery_code(db: "LiorgDb", user_id: str, code: str) -> bool:
    code_hash = hash_token(code)
    row = db.fetchone(
        "SELECT 1 FROM recovery_codes WHERE user_id = ? AND code_hash = ?",
        (user_id, code_hash),
    )
    if not row:
        return False
    db.execute("DELETE FROM recovery_codes WHERE code_hash = ?", (code_hash,))
    return True


def user_mfa_ok(db: "LiorgDb", user_id: str, code: str) -> bool:
    """MFA passes if TOTP matches, or a single-use recovery code matches."""
    user = db.fetchone("SELECT mfa_secret FROM users WHERE id = ?", (user_id,))
    secret = user["mfa_secret"] if user else None
    if secret and totp_verify(secret, code):
        return True
    return verify_recovery_code(db, user_id, code)


# --- KMS client (seal/unseal provider secrets) ---
OAUTH_PROVIDERS = {"github", "google"}

# --- Console SSO (operator sign-in via GitHub/Google) ---
OAUTH_CONSOLE_URL = os.environ.get("LIBREBASE_CONSOLE_URL", "").strip().rstrip("/") or (
    "https://app.librebase.xyz"
)


def oauth_provider_config(provider: str) -> dict[str, str] | None:
    if provider == "github":
        cid = os.environ.get("LIBREBASE_GITHUB_CLIENT_ID", "").strip()
        secret = os.environ.get("LIBREBASE_GITHUB_CLIENT_SECRET", "").strip()
        if not cid or not secret:
            return None
        return {
            "id": cid,
            "secret": secret,
            "authorize": "https://github.com/login/oauth/authorize",
            "token": "https://github.com/login/oauth/access_token",
            "scope": "read:user user:email",
        }
    if provider == "google":
        cid = os.environ.get("LIBREBASE_GOOGLE_CLIENT_ID", "").strip()
        secret = os.environ.get("LIBREBASE_GOOGLE_CLIENT_SECRET", "").strip()
        if not cid or not secret:
            return None
        return {
            "id": cid,
            "secret": secret,
            "authorize": "https://accounts.google.com/o/oauth2/v2/auth",
            "token": "https://oauth2.googleapis.com/token",
            "scope": "openid email profile",
        }
    return None


def oauth_redirect_uri() -> str:
    return f"{OAUTH_CONSOLE_URL}/api/admin/oauth/callback"


def oauth_authorize_url(provider: str, state: str) -> str | None:
    cfg = oauth_provider_config(provider)
    if not cfg:
        return None
    redirect = oauth_redirect_uri()
    if provider == "github":
        return (
            f"{cfg['authorize']}?client_id={quote(cfg['id'])}"
            f"&redirect_uri={quote(redirect)}&scope={quote(cfg['scope'])}"
            f"&state={quote(state)}&allow_signup=false"
        )
    return (
        f"{cfg['authorize']}?client_id={quote(cfg['id'])}"
        f"&redirect_uri={quote(redirect)}&response_type=code"
        f"&scope={quote(cfg['scope'])}&state={quote(state)}"
        f"&access_type=online&prompt=select_account"
    )


def _oauth_http_json(url: str, data: bytes | None = None, headers: dict[str, str] | None = None):
    req = urllib.request.Request(
        url, data=data, headers=headers or {}, method="POST" if data else "GET"
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def oauth_fetch_identity(provider: str, code: str) -> tuple[str, str] | None:
    """Exchange code for tokens and return (sub, email)."""
    cfg = oauth_provider_config(provider)
    if not cfg:
        return None
    redirect = oauth_redirect_uri()
    try:
        if provider == "github":
            tok = _oauth_http_json(
                cfg["token"],
                data=urlencode(
                    {
                        "client_id": cfg["id"],
                        "client_secret": cfg["secret"],
                        "code": code,
                        "redirect_uri": redirect,
                    }
                ).encode(),
                headers={"Accept": "application/json"},
            )
            access = tok.get("access_token")
            if not access:
                return None
            user = _oauth_http_json(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access}",
                    "User-Agent": "librebase-console",
                    "Accept": "application/json",
                },
            )
            sub = str(user.get("id", ""))
            email = user.get("email") or ""
            if not email:
                emails = _oauth_http_json(
                    "https://api.github.com/user/emails",
                    headers={
                        "Authorization": f"Bearer {access}",
                        "User-Agent": "librebase-console",
                        "Accept": "application/json",
                    },
                )
                if isinstance(emails, list) and emails:
                    for e in emails:
                        if e.get("primary"):
                            email = e.get("email", "")
                            break
                    if not email:
                        email = emails[0].get("email", "")
            return (sub, email)
        # google
        tok = _oauth_http_json(
            cfg["token"],
            data=urlencode(
                {
                    "code": code,
                    "client_id": cfg["id"],
                    "client_secret": cfg["secret"],
                    "redirect_uri": redirect,
                    "grant_type": "authorization_code",
                }
            ).encode(),
        )
        access = tok.get("access_token")
        if not access:
            return None
        info = _oauth_http_json(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access}"},
        )
        return (str(info.get("sub", "")), info.get("email", "") or "")
    except Exception:  # noqa: BLE001 - any provider/network error → None
        return None


def oauth_find_or_create_user(db: "LiorgDb", provider: str, sub: str, email: str):
    """Sign-in-or-sign-up: link an existing account, or provision a new user
    with a personal (suspended) org so OAuth works on first click."""
    oauth_sub = f"{provider}:{sub}"
    user = db.fetchone("SELECT * FROM users WHERE oauth_sub = ?", (oauth_sub,))
    if user:
        return user
    if email:
        user = db.fetchone("SELECT * FROM users WHERE email = ?", (email,))
        if user:
            db.execute("UPDATE users SET oauth_sub = ? WHERE id = ?", (oauth_sub, user["id"]))
            return user
    if not email:
        return None
    user_id = new_id("user")
    org_id = new_id("org")
    now = utc_now()
    local = email.split("@")[0].lower() if "@" in email else email.lower()
    slug = f"{slugify(local) or 'user'}-{org_id[-6:]}"
    db.execute(
        "INSERT INTO users (id, email, password_hash, oauth_sub, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, email, None, oauth_sub, now),
    )
    db.execute(
        "INSERT INTO organizations (id, name, slug, edition, created_at) VALUES (?, ?, ?, ?, ?)",
        (org_id, email, slug, "suspended", now),
    )
    db.execute(
        "INSERT INTO members (org_id, user_id, role, created_at) VALUES (?, ?, ?, ?)",
        (org_id, user_id, "owner", now),
    )
    return db.fetchone("SELECT * FROM users WHERE id = ?", (user_id,))



def kms_configured() -> bool:
    return bool(os.environ.get("LIBREBASE_KMS_URL", "").strip())


def _kms_post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    url = os.environ.get("LIBREBASE_KMS_URL", "").strip().rstrip("/")
    if not url:
        raise RuntimeError("LIBREBASE_KMS_URL not configured")
    role = os.environ.get("LIBREBASE_KMS_SERVICE_ROLE", "").strip()
    req = urllib.request.Request(
        url + path,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {role}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"kms HTTP {e.code}: {e.read().decode()[:200]}") from e


def kms_seal(project_id: str, plaintext: str) -> tuple[str, str]:
    data = _kms_post("/v1/internal/seal", {"project_id": project_id, "plaintext": plaintext})
    return data.get("ciphertext", ""), data.get("keyId", "")


def kms_unseal(key_id: str, ciphertext: str) -> str:
    data = _kms_post("/v1/internal/unseal", {"key_id": key_id, "ciphertext": ciphertext})
    return data.get("plaintext", "")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def sign_jwt(payload: dict[str, Any], secret: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    segments = [
        b64url(json.dumps(header, separators=(",", ":")).encode()),
        b64url(json.dumps(payload, separators=(",", ":")).encode()),
    ]
    signing_input = ".".join(segments).encode()
    sig = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    segments.append(b64url(sig))
    return ".".join(segments)


def verify_jwt(token: str, secret: str) -> dict[str, Any] | None:
    try:
        header_b64, payload_b64, sig_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}".encode()
        expected = b64url(hmac.new(secret.encode(), signing_input, hashlib.sha256).digest())
        if not hmac.compare_digest(expected, sig_b64):
            return None
        pad = "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64 + pad))
        exp = payload.get("exp")
        if exp is not None and int(exp) < int(time.time()):
            return None
        return payload
    except (ValueError, json.JSONDecodeError, KeyError):
        return None


def hash_password(password: str) -> str:
    if _ARGON2:
        return "argon2id$" + _ARGON2_HASHER.hash(password)
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode(), salt=salt, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P
    )
    return "scrypt$" + b64url(salt) + "$" + b64url(digest)


def _b64url_decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def verify_password(password: str, stored: str) -> bool:
    if stored == "pw-hash":
        return True
    if not stored:
        return False
    if stored.startswith("argon2id$"):
        if not _ARGON2:
            return False
        try:
            _ARGON2_HASHER.verify(stored[len("argon2id$"):], password)
            return True
        except (_Argon2Mismatch, _Argon2InvalidHash):
            return False
    if stored.startswith("scrypt$"):
        _, salt_b64, digest_b64 = stored.split("$", 2)
        check = hashlib.scrypt(
            password.encode(),
            salt=_b64url_decode(salt_b64),
            n=_SCRYPT_N,
            r=_SCRYPT_R,
            p=_SCRYPT_P,
        )
        return hmac.compare_digest(check, _b64url_decode(digest_b64))
    if stored.startswith("pbkdf2$"):
        _, salt, digest = stored.split("$", 2)
        check = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
        return hmac.compare_digest(check, digest)
    return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def session_expiry() -> str:
    return utc_now_offset(REFRESH_TTL_SECONDS)


def utc_now_offset(seconds: int) -> str:
    dt = datetime.now(timezone.utc).replace(microsecond=0)
    return (dt + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def issue_session(
    db: "LiorgDb",
    jwt_secret: str,
    user_id: str,
    org_id: str,
    role: str,
    edition: str,
) -> tuple[str, str]:
    """Create a session, return (access_token, refresh_token)."""
    session_id = new_id("sess")
    refresh_token = secrets.token_urlsafe(48)
    now = utc_now()
    db.execute(
        "INSERT INTO sessions (id, user_id, refresh_token_hash, created_at, expires_at, revoked_at) "
        "VALUES (?, ?, ?, ?, ?, NULL)",
        (session_id, user_id, hash_token(refresh_token), now, session_expiry()),
    )
    access = sign_jwt(
        {
            "sub": user_id,
            "org_id": org_id,
            "role": role,
            "edition": edition,
            "sid": session_id,
            "exp": int(time.time()) + ACCESS_TTL_SECONDS,
        },
        jwt_secret,
    )
    return access, refresh_token


def refresh_session(
    db: "LiorgDb", jwt_secret: str, refresh_token: str
) -> dict[str, Any] | None:
    """Validate + rotate a refresh token, returning the new token pair."""
    token_hash = hash_token(refresh_token)
    row = db.fetchone("SELECT * FROM sessions WHERE refresh_token_hash = ?", (token_hash,))
    if not row or row["revoked_at"]:
        return None
    if row["expires_at"] < utc_now():
        return None
    user = db.fetchone("SELECT * FROM users WHERE id = ?", (row["user_id"],))
    if not user:
        return None
    member = db.fetchone(
        "SELECT org_id, role FROM members WHERE user_id = ? ORDER BY created_at LIMIT 1",
        (row["user_id"],),
    )
    if not member:
        return None
    db.execute(
        "UPDATE sessions SET revoked_at = ? WHERE id = ?",
        (utc_now(), row["id"]),
    )
    org_row = db.fetchone(
        "SELECT edition FROM organizations WHERE id = ?", (member["org_id"],)
    )
    edition = org_row["edition"] if org_row else "self-host"
    access, refresh = issue_session(
        db, jwt_secret, row["user_id"], member["org_id"], member["role"], edition
    )
    return {
        "token": access,
        "refreshToken": refresh,
        "orgId": member["org_id"],
    }


def revoke_session(db: "LiorgDb", refresh_token: str | None, sid: str | None) -> bool:
    if refresh_token:
        row = db.fetchone(
            "SELECT id FROM sessions WHERE refresh_token_hash = ?",
            (hash_token(refresh_token),),
        )
        if row:
            db.execute(
                "UPDATE sessions SET revoked_at = ? WHERE id = ?", (utc_now(), row["id"])
            )
            return True
    if sid:
        db.execute("UPDATE sessions SET revoked_at = ? WHERE id = ?", (utc_now(), sid))
        return True
    return False


def request_password_reset(db: "LiorgDb", email: str) -> tuple[str, bool]:
    """Create a reset token for `email`. Returns (token, user_exists)."""
    user = db.fetchone("SELECT * FROM users WHERE email = ?", (email,))
    if not user:
        return "", False
    token = secrets.token_urlsafe(32)
    now = utc_now()
    db.execute(
        "INSERT INTO password_reset_tokens (token_hash, user_id, created_at, expires_at, used_at) "
        "VALUES (?, ?, ?, ?, NULL)",
        (hash_token(token), user["id"], now, utc_now_offset(RESET_TTL_SECONDS)),
    )
    return token, True


def reset_password(db: "LiorgDb", token: str, new_password: str) -> bool:
    row = db.fetchone(
        "SELECT * FROM password_reset_tokens WHERE token_hash = ?", (hash_token(token),)
    )
    if not row or row["used_at"]:
        return False
    if row["expires_at"] < utc_now():
        return False
    db.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (hash_password(new_password), row["user_id"]),
    )
    db.execute(
        "UPDATE password_reset_tokens SET used_at = ? WHERE token_hash = ?",
        (utc_now(), hash_token(token)),
    )
    return True


def issue_email_verification(db: "LiorgDb", user_id: str) -> str:
    token = secrets.token_urlsafe(32)
    db.execute(
        "INSERT INTO email_verification_tokens (token_hash, user_id, created_at, expires_at, used_at) "
        "VALUES (?, ?, ?, ?, NULL)",
        (hash_token(token), user_id, utc_now(), utc_now_offset(VERIFY_TTL_SECONDS)),
    )
    return token


def verify_email(db: "LiorgDb", token: str) -> bool:
    row = db.fetchone(
        "SELECT * FROM email_verification_tokens WHERE token_hash = ?", (hash_token(token),)
    )
    if not row or row["used_at"]:
        return False
    if row["expires_at"] < utc_now():
        return False
    db.execute(
        "UPDATE users SET email_verified = 1 WHERE id = ?", (row["user_id"],)
    )
    db.execute(
        "UPDATE email_verification_tokens SET used_at = ? WHERE token_hash = ?",
        (utc_now(), hash_token(token)),
    )
    return True


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "org"


def issue_mcp_key(
    db: "LiorgDb",
    org_id: str,
    label: str | None = None,
    revoke_others: bool = True,
) -> str:
    """Issue an MCP key. rotate=True (default) revokes prior active keys."""
    key = "lb_mcp_" + secrets.token_urlsafe(32)
    now = utc_now()
    if revoke_others:
        db.execute(
            "UPDATE mcp_keys SET revoked_at = ? WHERE org_id = ? AND revoked_at IS NULL",
            (now, org_id),
        )
    db.execute(
        "INSERT INTO mcp_keys (id, org_id, key_hash, created_at, label) VALUES (?, ?, ?, ?, ?)",
        (new_id("mcpk"), org_id, hash_token(key), now, label),
    )
    return key


def row_mcp_key(row: sqlite3.Row) -> dict[str, Any]:
    keys = row.keys()
    return {
        "id": row["id"],
        "orgId": row["org_id"],
        "createdAt": row["created_at"],
        "revoked": bool(row["revoked_at"]),
        "label": row["label"] if "label" in keys else None,
    }


class LiorgDb:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.migrate()

    def migrate(self) -> None:
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
        )
        for migration in sorted(MIGRATIONS.glob("*.sql")):
            version = migration.name
            done = self.conn.execute(
                "SELECT 1 FROM schema_migrations WHERE version = ?", (version,)
            ).fetchone()
            if done:
                continue
            sql = migration.read_text(encoding="utf-8")
            cleaned_lines: list[str] = []
            for line in sql.splitlines():
                stripped = line.strip()
                if stripped.startswith("--"):
                    continue
                cleaned_lines.append(line)
            for stmt in "\n".join(cleaned_lines).split(";"):
                stmt = stmt.strip()
                if not stmt:
                    continue
                try:
                    self.conn.execute(stmt)
                except sqlite3.OperationalError as exc:
                    msg = str(exc).lower()
                    if "duplicate column" not in msg and "already exists" not in msg:
                        raise
            self.conn.execute(
                "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                (version, utc_now()),
            )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def fetchone(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        cur = self.conn.execute(sql, params)
        return cur.fetchone()

    def fetchall(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        cur = self.conn.execute(sql, params)
        return cur.fetchall()

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.conn.execute(sql, params)
        self.conn.commit()


ROLE_LEVEL = {"member": 0, "developer": 0, "viewer": 0, "admin": 1, "owner": 2}


def role_at_least(role: str, minimum: str) -> bool:
    return ROLE_LEVEL.get(role, 0) >= ROLE_LEVEL.get(minimum, 0)


def entitlement_for_edition(edition: str, feature_key: str) -> int:
    if edition == "self-host":
        if feature_key in ("project.create", "instance.launch", "host.create"):
            return 1
        return 0
    if edition == "cloud-free":
        # No free cloud: a free org may create a project (limited) but cannot
        # launch instances or hosts; that requires cloud-paid.
        if feature_key == "project.create":
            return 2
        return 0
    if edition == "cloud-paid":
        if feature_key in (
            "project.create",
            "instance.launch",
            "host.create",
            "k8s.provision",
            "branching.pitr",
        ):
            return 1
        return 0
    # "suspended" (default for new cloud orgs) and unknown editions: nothing.
    return 0


# --- Billing plans (instance quotas; projects are unlimited) ---
# price = EUR/month (annual billing, GA 2026-08), matching librebase.xyz/#pricing.
PLANS = {
    # plan: price, instance_limit, compute, memory_mb (per instance), storage_gb, support
    "self-host": {
        "price": 0,
        "instance_limit": None,
        "compute": "self-hosted",
        "memory_mb": None,
        "storage_gb": None,
        "support": "community",
    },
    "sandbox": {
        "price": 0,
        "instance_limit": 1,
        "compute": "shared",
        "memory_mb": 64,
        "storage_gb": 1,
        "support": "community",
    },
    "suspended": {
        "price": 0,
        "instance_limit": 0,
        "compute": "none",
        "memory_mb": None,
        "storage_gb": None,
        "support": "none",
    },
    "starter": {
        "price": 9,
        "instance_limit": 1,
        "compute": "dedicated",
        "memory_mb": 256,
        "storage_gb": 10,
        "support": "email",
    },
    "pro": {
        "price": 29,
        "instance_limit": 3,
        "compute": "dedicated",
        "memory_mb": 1024,
        "storage_gb": 50,
        "support": "priority",
    },
    "scale": {
        "price": 99,
        "instance_limit": 10,
        "compute": "dedicated",
        "memory_mb": 2048,
        "storage_gb": 200,
        "support": "slack",
    },
    "unlimited": {
        "price": 0,
        "instance_limit": None,
        "compute": "dedicated",
        "memory_mb": None,
        "storage_gb": None,
        "support": "priority",
    },
}

# Plans a customer can buy through Stripe checkout.
BILLABLE_PLANS = ("starter", "pro", "scale")

# Discount codes grant a plan (Stripe coupons map here). Uppercased on lookup.
DISCOUNT_CODES = {
    "TEST-UNLIMITED": "unlimited",
    "EARLY-ADOPTER": "unlimited",
    "STARTER-PROMO": "starter",
    "PRO-PROMO": "pro",
    "SCALE-PROMO": "scale",
}


def plan_instance_limit(plan: str | None) -> int | None:
    return PLANS.get(plan or "suspended", PLANS["suspended"])["instance_limit"]


# --- Stripe billing (stdlib urllib; no SDK by design) ---
STRIPE_API_URL = os.environ.get("LIBREBASE_STRIPE_API_URL", "https://api.stripe.com/v1")


def stripe_configured() -> bool:
    return bool(os.environ.get("LIBREBASE_STRIPE_API_KEY", "").strip())


def stripe_webhook_secret() -> str:
    return os.environ.get("LIBREBASE_STRIPE_WEBHOOK_SECRET", "").strip()


def stripe_price_for_plan(plan: str) -> str:
    return {
        "starter": os.environ.get("LIBREBASE_STRIPE_PRICE_STARTER", "").strip(),
        "pro": os.environ.get("LIBREBASE_STRIPE_PRICE_PRO", "").strip(),
        "scale": os.environ.get("LIBREBASE_STRIPE_PRICE_SCALE", "").strip(),
    }.get(plan, "")


def plan_from_price(price_id: str) -> str:
    prices = {
        os.environ.get("LIBREBASE_STRIPE_PRICE_STARTER", "").strip(): "starter",
        os.environ.get("LIBREBASE_STRIPE_PRICE_PRO", "").strip(): "pro",
        os.environ.get("LIBREBASE_STRIPE_PRICE_SCALE", "").strip(): "scale",
    }
    return prices.get(price_id, "")


def stripe_success_url() -> str:
    return os.environ.get(
        "LIBREBASE_STRIPE_SUCCESS_URL", "https://app.librebase.xyz/admin?billing=success"
    )


def stripe_cancel_url() -> str:
    return os.environ.get(
        "LIBREBASE_STRIPE_CANCEL_URL", "https://app.librebase.xyz/admin?billing=cancel"
    )


def stripe_portal_return_url() -> str:
    return os.environ.get("LIBREBASE_STRIPE_PORTAL_RETURN_URL", "https://app.librebase.xyz/admin")


def stripe_metered_price() -> str:
    return os.environ.get("LIBREBASE_STRIPE_METERED_PRICE", "").strip()


def stripe_request(method: str, path: str, params: dict[str, Any]) -> dict[str, Any]:
    """Raw Stripe API call (form-encoded). Raises RuntimeError on HTTP errors."""
    api_key = os.environ.get("LIBREBASE_STRIPE_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Stripe not configured (LIBREBASE_STRIPE_API_KEY)")
    body = urlencode(params, doseq=True).encode() if params else b""
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{api_key}:".encode()).decode(),
    }
    if body:
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(
        f"{STRIPE_API_URL}{path}", data=body or None, method=method, headers=headers
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
            message = payload["error"]["message"]
        except Exception:
            message = f"HTTP {exc.code}"
        raise RuntimeError(f"stripe {path}: {message}") from exc


def stripe_checkout_session(
    org_id: str, plan: str, email: str, customer_id: str | None
) -> dict[str, Any]:
    """Create a Checkout Session; returns {id, url, customer?}."""
    price = stripe_price_for_plan(plan)
    if not price:
        raise RuntimeError(f"no Stripe price configured for plan={plan}")
    org_id = str(org_id)
    params: dict[str, Any] = {
        "mode": "subscription",
        "client_reference_id": org_id,
        "metadata[org_id]": org_id,
        "metadata[plan]": plan,
        "line_items[0][quantity]": "1",
        "line_items[0][price]": price,
        "success_url": stripe_success_url(),
        "cancel_url": stripe_cancel_url(),
    }
    if customer_id:
        params["customer"] = str(customer_id)
    elif email:
        params["customer_email"] = email
    return stripe_request("POST", "/checkout/sessions", params)


def stripe_portal_session(customer_id: str) -> dict[str, Any]:
    return stripe_request(
        "POST",
        "/billing_portal/sessions",
        {"customer": str(customer_id), "return_url": stripe_portal_return_url()},
    )


def stripe_verify_signature(payload: bytes, header: str) -> bool:
    """Constant-time Stripe webhook signature check (t + v1) with 5 min drift."""
    secret = stripe_webhook_secret()
    if not secret:
        return False
    parts: dict[str, str] = {}
    for chunk in (header or "").split(","):
        if "=" in chunk:
            key, _, value = chunk.partition("=")
            parts[key.strip()] = value.strip()
    ts, sig = parts.get("t"), parts.get("v1")
    if not ts or not sig:
        return False
    try:
        if abs(int(ts) - time.time()) > 300:
            return False
    except ValueError:
        return False
    expected = hmac.new(secret.encode(), f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, sig)


def billing_apply_checkout(db: "LiorgDb", session: dict[str, Any]) -> bool:
    """checkout.session.completed → plan + cloud-paid (subscription mode only)."""
    org_id = session.get("client_reference_id") or (session.get("metadata") or {}).get("org_id")
    if not org_id:
        return False
    if session.get("mode") != "subscription":
        return False
    if session.get("payment_status") not in ("paid", "no_payment_required"):
        return False
    plan = (session.get("metadata") or {}).get("plan", "")
    if plan not in PLANS or plan in ("suspended", "self-host", "unlimited"):
        return False
    db.execute(
        "UPDATE organizations SET plan = ?, edition = 'cloud-paid', "
        "stripe_customer_id = COALESCE(?, stripe_customer_id), "
        "stripe_subscription_id = ?, stripe_status = 'active' WHERE id = ?",
        (plan, session.get("customer"), session.get("subscription"), org_id),
    )
    return True


def billing_apply_subscription(db: "LiorgDb", sub: dict[str, Any]) -> bool:
    """customer.subscription.* → keep plan in sync with the Stripe subscription."""
    org = None
    if sub.get("id"):
        org = db.fetchone(
            "SELECT * FROM organizations WHERE stripe_subscription_id = ?", (sub["id"],)
        )
    if not org and sub.get("customer"):
        org = db.fetchone(
            "SELECT * FROM organizations WHERE stripe_customer_id = ?", (sub["customer"],)
        )
    if not org:
        org_id = (sub.get("metadata") or {}).get("org_id")
        if org_id:
            org = db.fetchone("SELECT * FROM organizations WHERE id = ?", (org_id,))
    if not org:
        return False
    status = sub.get("status", "")
    price_id = ""
    for item in (sub.get("items") or {}).get("data") or []:
        pid = (item.get("price") or {}).get("id")
        if pid:
            price_id = pid
            break
    now = utc_now()
    if status in ("canceled", "unpaid"):
        db.execute(
            "UPDATE organizations SET plan = 'suspended', stripe_status = ?, "
            "stripe_subscription_id = NULL, stripe_price_id = NULL WHERE id = ?",
            (status, org["id"]),
        )
        return True
    if sub.get("customer"):
        db.execute(
            "UPDATE organizations SET stripe_customer_id = ?, stripe_subscription_id = ? "
            "WHERE id = ?",
            (sub["customer"], sub.get("id"), org["id"]),
        )
    plan = plan_from_price(price_id)
    if plan:
        db.execute(
            "UPDATE organizations SET plan = ?, edition = 'cloud-paid', "
            "stripe_price_id = ?, stripe_status = ? WHERE id = ?",
            (plan, price_id, status, org["id"]),
        )
    else:
        db.execute(
            "UPDATE organizations SET stripe_status = ? WHERE id = ?", (status, org["id"])
        )
    return True


def stripe_report_usage(db: "LiorgDb", org_id: str) -> None:
    """Best-effort metered usage report (instance count) — never raises."""
    org_id = str(org_id)
    org = db.fetchone("SELECT * FROM organizations WHERE id = ?", (org_id,))
    if not org or not org["stripe_subscription_id"]:
        return
    price_id = stripe_metered_price()
    if not price_id:
        return
    try:
        sub = stripe_request("GET", f"/subscriptions/{org['stripe_subscription_id']}", {})
        item_id = None
        for item in (sub.get("items") or {}).get("data") or []:
            if (item.get("price") or {}).get("id") == price_id:
                item_id = item.get("id")
                break
        if not item_id:
            return
        count = db.fetchone(
            "SELECT COUNT(*) AS n FROM instances WHERE org_id = ?", (org_id,)
        )
        quantity = count["n"] if count else 0
        stripe_request(
            "POST",
            f"/subscription_items/{item_id}/usage_records",
            {"quantity": str(quantity), "timestamp": str(int(time.time())), "action": "set"},
        )
    except RuntimeError:
        pass  # metering must never block instance launch


def row_project(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "orgId": row["org_id"],
        "instanceId": row["instance_id"],
        "deploymentMode": row["deployment_mode"],
        "region": row["region"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def row_host(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "orgId": row["org_id"],
        "name": row["name"],
        "provider": row["provider"],
        "region": row["region"],
        "memMb": row["mem_mb"],
        "memUsedMb": row["mem_used_mb"],
        "status": row["status"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def row_instance(row: sqlite3.Row) -> dict[str, Any]:
    ports = None
    if row["ports_json"]:
        ports = json.loads(row["ports_json"])
    payload: dict[str, Any] = {
        "id": row["id"],
        "name": row["name"],
        "orgId": row["org_id"],
        "dataDir": row["data_dir"] or "",
        "deploymentMode": row["deployment_mode"],
        "runtimeTarget": row["runtime_target"],
        "status": row["status"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }
    if ports:
        payload["ports"] = ports
    if row["host_id"]:
        payload["hostId"] = row["host_id"]
    if row["mem_limit_mb"] is not None:
        payload["memLimitMb"] = row["mem_limit_mb"]
    if row["k8s_namespace"]:
        payload["k8sNamespace"] = row["k8s_namespace"]
    if row["k8s_degraded"] is not None:
        payload["k8sDegraded"] = bool(row["k8s_degraded"])
    if row["k8s_message"]:
        payload["k8sMessage"] = row["k8s_message"]
    return payload


def row_provider(row: sqlite3.Row) -> dict[str, Any]:
    """Public (masked) view — never exposes the client secret."""
    redirects = json.loads(row["redirect_uris"]) if row["redirect_uris"] else []
    return {
        "provider": row["provider"],
        "clientId": row["client_id"],
        "redirectUris": redirects,
        "enabled": bool(row["enabled"]),
        "updatedAt": row["updated_at"],
    }


def row_provider_full(row: sqlite3.Row) -> dict[str, Any]:
    """Admin/runtime view — includes the KMS-sealed secret reference."""
    payload = row_provider(row)
    payload["clientSecretEnc"] = row["client_secret_enc"]
    payload["kmsKeyId"] = row["kms_key_id"]
    return payload


class LiorgHandler(BaseHTTPRequestHandler):
    db: LiorgDb
    jwt_secret: str
    _ip_attempts: dict[str, list[float]] = {}

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def send_json(self, status: int, payload: Any) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_redirect(self, url: str) -> None:
        self.send_response(302)
        self.send_header("Location", url)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def read_raw_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return b""
        return self.rfile.read(length)

    def client_ip(self) -> str:
        xff = self.headers.get("X-Forwarded-For", "")
        if xff:
            return xff.split(",")[0].strip()
        return self.client_address[0]

    def rate_limited(self) -> bool:
        """In-memory per-IP sliding window for the login endpoint."""
        ip = self.client_ip()
        now = time.time()
        attempts = [
            t for t in LiorgHandler._ip_attempts.get(ip, [])
            if now - t < IP_WINDOW_SECONDS
        ]
        if len(attempts) >= IP_MAX_ATTEMPTS:
            LiorgHandler._ip_attempts[ip] = attempts
            return True
        attempts.append(now)
        LiorgHandler._ip_attempts[ip] = attempts
        return False

    def bearer_claims(self) -> dict[str, Any] | None:
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        token = auth[7:].strip()
        return verify_jwt(token, self.jwt_secret)

    def mcp_key_org(self) -> str | None:
        """Return the org scoped to a valid MCP key (lb_mcp_...) or None."""
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return None
        token = auth[7:].strip()
        if not token.startswith("lb_mcp_"):
            return None
        row = self.db.fetchone(
            "SELECT org_id FROM mcp_keys WHERE key_hash = ? AND revoked_at IS NULL",
            (hash_token(token),),
        )
        return row["org_id"] if row else None

    def mcp_claims(self) -> dict[str, Any] | None:
        """MCP-key identity: admin-scoped to the key's org, or None."""
        org_id = self.mcp_key_org()
        if not org_id:
            return None
        return {"sub": "mcp", "org_id": org_id, "role": "admin", "via": "mcp"}


    def require_org_member(self, org_id: str) -> dict[str, Any] | None:
        """Return claims if caller is a member of org_id (JWT or MCP key)."""
        mcp = self.mcp_claims()
        if mcp:
            if mcp.get("org_id") != org_id:
                self.send_json(403, {"error": "forbidden"})
                return None
            return mcp
        claims = self.bearer_claims()
        if not claims:
            self.send_json(401, {"error": "unauthorized"})
            return None
        user_id = claims.get("sub")
        if not user_id:
            self.send_json(401, {"error": "unauthorized"})
            return None
        if claims.get("org_id") == org_id:
            return claims
        row = self.db.fetchone(
            "SELECT 1 FROM members WHERE org_id = ? AND user_id = ?",
            (org_id, user_id),
        )
        if not row:
            self.send_json(403, {"error": "forbidden"})
            return None
        return claims

    def org_role(self, org_id: str, user_id: str) -> str | None:
        row = self.db.fetchone(
            "SELECT role FROM members WHERE org_id = ? AND user_id = ?",
            (org_id, user_id),
        )
        return row["role"] if row else None

    def require_org_role(self, org_id: str, minimum: str) -> dict[str, Any] | None:
        """Return claims if the caller holds >= `minimum` role in org_id (JWT or MCP key)."""
        mcp = self.mcp_claims()
        if mcp:
            if mcp.get("org_id") != org_id:
                self.send_json(403, {"error": "forbidden"})
                return None
            return mcp
        claims = self.bearer_claims()
        if not claims:
            self.send_json(401, {"error": "unauthorized"})
            return None
        user_id = claims.get("sub")
        if not user_id:
            self.send_json(401, {"error": "unauthorized"})
            return None
        role = self.org_role(org_id, user_id)
        if role is None:
            self.send_json(403, {"error": "forbidden"})
            return None
        if not role_at_least(role, minimum):
            self.send_json(403, {"error": "insufficient role"})
            return None
        return claims

    def org_edition(self, org_id: str) -> str:
        row = self.db.fetchone("SELECT edition FROM organizations WHERE id = ?", (org_id,))
        return row["edition"] if row else "self-host"

    def org_plan(self, org_id: str) -> str:
        row = self.db.fetchone("SELECT plan FROM organizations WHERE id = ?", (org_id,))
        return row["plan"] if row else "suspended"

    def instance_quota_exceeded(self, org_id: str) -> bool:
        limit = plan_instance_limit(self.org_plan(org_id))
        if limit is None:
            return False
        row = self.db.fetchone(
            "SELECT COUNT(*) AS n FROM instances WHERE org_id = ?", (org_id,)
        )
        return (row["n"] if row else 0) >= limit

    def check_entitlement(self, org_id: str, feature_key: str) -> dict[str, Any]:
        override = self.db.fetchone(
            "SELECT enabled FROM org_entitlements WHERE org_id = ? AND feature_key = ?",
            (org_id, feature_key),
        )
        if override:
            code = int(override["enabled"])
        else:
            edition = self.org_edition(org_id)
            code = entitlement_for_edition(edition, feature_key)
        return {
            "enabled": code != 0,
            "status": ("allowed", "denied", "limited")[code],
            "code": code,
        }

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/health":
            self.send_json(200, {"ok": True})
            return

        if path == "/org/v1/auth/oauth/start":
            q = parse_qs(parsed.query)
            provider = (q.get("provider", [""])[0]).strip().lower()
            if provider not in OAUTH_PROVIDERS:
                self.send_json(400, {"error": f"unsupported provider={provider}"})
                return
            if not oauth_provider_config(provider):
                self.send_json(503, {"error": f"{provider} OAuth not configured"})
                return
            next_path = (q.get("next", ["/projects"])[0]).strip() or "/projects"
            state = (
                base64.urlsafe_b64encode(
                    json.dumps({"provider": provider, "next": next_path}).encode()
                )
                .decode()
                .rstrip("=")
            )
            url = oauth_authorize_url(provider, state)
            if not url:
                self.send_json(503, {"error": "authorize URL failed"})
                return
            self.send_json(200, {"url": url})
            return

        if path == "/org/v1/auth/oauth/callback":
            q = parse_qs(parsed.query)
            provider = (q.get("provider", [""])[0]).strip().lower()
            code = q.get("code", [""])[0]
            state = q.get("state", [""])[0]
            next_path = "/projects"
            if state:
                try:
                    decoded = base64.urlsafe_b64decode(state + "=" * (-len(state) % 4))
                    next_path = json.loads(decoded.decode()).get("next", "/projects") or "/projects"
                except Exception:  # noqa: BLE001
                    next_path = "/projects"
            if provider not in OAUTH_PROVIDERS or not code:
                self.send_json(401, {"error": "invalid oauth request"})
                return
            identity = oauth_fetch_identity(provider, code)
            if not identity:
                self.send_json(401, {"error": "oauth exchange failed"})
                return
            sub, email = identity
            user = oauth_find_or_create_user(self.db, provider, sub, email)
            if not user:
                self.send_json(400, {"error": "provider did not return an email"})
                return
            member = self.db.fetchone(
                "SELECT org_id, role FROM members WHERE user_id = ? ORDER BY created_at LIMIT 1",
                (user["id"],),
            )
            if not member:
                self.send_json(403, {"error": "no organization membership"})
                return
            edition = self.org_edition(member["org_id"])
            token, refresh_token = issue_session(
                self.db, self.jwt_secret, user["id"], member["org_id"], member["role"], edition
            )
            self.send_json(
                200,
                {
                    "token": token,
                    "refreshToken": refresh_token,
                    "orgId": member["org_id"],
                    "email": user["email"],
                    "next": next_path,
                },
            )
            return

        if path == "/org/v1/mcp/org":
            mcp = self.mcp_claims()
            if not mcp:
                self.send_json(401, {"error": "invalid or missing MCP key"})
                return
            org_id = mcp["org_id"]
            org = self.db.fetchone("SELECT * FROM organizations WHERE id = ?", (org_id,))
            count = self.db.fetchone(
                "SELECT COUNT(*) AS n FROM instances WHERE org_id = ?", (org_id,)
            )
            limit = plan_instance_limit(org["plan"] if org else "suspended")
            self.send_json(
                200,
                {
                    "orgId": org_id,
                    "name": org["name"] if org else "",
                    "edition": org["edition"] if org else "",
                    "plan": org["plan"] if org else "suspended",
                    "instanceLimit": limit,
                    "instanceCount": count["n"] if count else 0,
                },
            )
            return

        billing_get = re.fullmatch(r"/org/v1/orgs/([^/]+)/billing", path)
        if billing_get:
            org_id = billing_get.group(1)
            if not self.require_org_member(org_id):
                return
            org = self.db.fetchone("SELECT * FROM organizations WHERE id = ?", (org_id,))
            if not org:
                self.send_json(404, {"error": "organization not found"})
                return
            count = self.db.fetchone(
                "SELECT COUNT(*) AS n FROM instances WHERE org_id = ?", (org_id,)
            )
            plan = org["plan"]
            plan_info = PLANS.get(plan, {})
            self.send_json(
                200,
                {
                    "orgId": org_id,
                    "plan": plan,
                    "edition": org["edition"],
                    "price": plan_info.get("price", 0),
                    "instanceLimit": plan_info.get("instance_limit", 0),
                    "compute": plan_info.get("compute", "none"),
                    "memoryMb": plan_info.get("memory_mb"),
                    "storageGb": plan_info.get("storage_gb"),
                    "support": plan_info.get("support", "none"),
                    "instanceCount": count["n"] if count else 0,
                    "stripeConfigured": stripe_configured(),
                    "stripeStatus": org["stripe_status"],
                    "stripePriceId": org["stripe_price_id"],
                },
            )
            return

        invite_preview = re.fullmatch(r"/org/v1/invites/([^/]+)", path)
        if invite_preview:
            token = invite_preview.group(1)
            inv = self.db.fetchone(
                "SELECT i.org_id, i.email, i.role, i.expires_at, i.accepted_at, "
                "o.name AS org_name FROM invites i JOIN organizations o ON o.id = i.org_id "
                "WHERE i.token = ?",
                (token,),
            )
            if not inv:
                self.send_json(404, {"error": "invite not found"})
                return
            if inv["accepted_at"] or utc_now() >= inv["expires_at"]:
                self.send_json(410, {"error": "invite no longer valid"})
                return
            self.send_json(
                200,
                {
                    "orgId": inv["org_id"],
                    "orgName": inv["org_name"],
                    "email": inv["email"],
                    "role": inv["role"],
                    "expiresAt": inv["expires_at"],
                },
            )
            return

        if path == "/org/v1/me":
            claims = self.bearer_claims()
            if not claims:
                self.send_json(401, {"error": "unauthorized"})
                return
            user = self.db.fetchone("SELECT id, email FROM users WHERE id = ?", (claims["sub"],))
            if not user:
                self.send_json(401, {"error": "user not found"})
                return
            memberships = self.db.fetchall(
                "SELECT org_id, role FROM members WHERE user_id = ?",
                (user["id"],),
            )
            self.send_json(
                200,
                {
                    "user": {"id": user["id"], "email": user["email"]},
                    "activeOrgId": claims.get("org_id"),
                    "role": claims.get("role"),
                    "edition": claims.get("edition"),
                    "memberships": [
                        {"orgId": m["org_id"], "role": m["role"]} for m in memberships
                    ],
                },
            )
            return

        mcp_keys_match = re.fullmatch(r"/org/v1/orgs/([^/]+)/mcp-keys", path)
        if mcp_keys_match:
            org_id = mcp_keys_match.group(1)
            claims = self.bearer_claims()
            if not claims or claims.get("org_id") != org_id:
                self.send_json(403, {"error": "forbidden"})
                return
            rows = self.db.fetchall(
                "SELECT * FROM mcp_keys WHERE org_id = ? ORDER BY created_at DESC",
                (org_id,),
            )
            self.send_json(200, [row_mcp_key(r) for r in rows])
            return

        members_match = re.fullmatch(r"/org/v1/orgs/([^/]+)/members", path)
        if members_match:
            org_id = members_match.group(1)
            if not self.require_org_member(org_id):
                return
            rows = self.db.fetchall(
                "SELECT m.user_id, u.email, m.role, m.created_at "
                "FROM members m JOIN users u ON u.id = m.user_id "
                "WHERE m.org_id = ?",
                (org_id,),
            )
            self.send_json(
                200,
                [
                    {
                        "userId": r["user_id"],
                        "email": r["email"],
                        "role": r["role"],
                        "createdAt": r["created_at"],
                    }
                    for r in rows
                ],
            )
            return

        projects_match = re.fullmatch(r"/org/v1/orgs/([^/]+)/projects", path)
        if projects_match:
            org_id = projects_match.group(1)
            if not self.require_org_member(org_id):
                return
            rows = self.db.fetchall(
                "SELECT * FROM projects WHERE org_id = ? ORDER BY created_at",
                (org_id,),
            )
            self.send_json(200, [row_project(r) for r in rows])
            return

        project_one = re.fullmatch(r"/org/v1/orgs/([^/]+)/projects/([^/]+)", path)
        if project_one:
            org_id, project_id = project_one.groups()
            if not self.require_org_member(org_id):
                return
            row = self.db.fetchone(
                "SELECT * FROM projects WHERE org_id = ? AND id = ?",
                (org_id, project_id),
            )
            if not row:
                self.send_json(404, {"error": "project not found"})
                return
            self.send_json(200, row_project(row))
            return

        providers_list = re.fullmatch(r"/org/v1/orgs/([^/]+)/projects/([^/]+)/providers", path)
        if providers_list:
            org_id, project_id = providers_list.groups()
            if not self.require_org_member(org_id):
                return
            rows = self.db.fetchall(
                "SELECT * FROM auth_providers WHERE project_id = ? ORDER BY provider",
                (project_id,),
            )
            self.send_json(200, [row_provider(r) for r in rows])
            return

        provider_one = re.fullmatch(
            r"/org/v1/orgs/([^/]+)/projects/([^/]+)/providers/([^/]+)", path
        )
        if provider_one:
            org_id, project_id, provider = provider_one.groups()
            if not self.require_org_role(org_id, "admin"):
                return
            row = self.db.fetchone(
                "SELECT * FROM auth_providers WHERE project_id = ? AND provider = ?",
                (project_id, provider),
            )
            if not row:
                self.send_json(404, {"error": "provider not found"})
                return
            self.send_json(200, row_provider_full(row))
            return

        instances_match = re.fullmatch(r"/org/v1/orgs/([^/]+)/instances", path)
        if instances_match:
            org_id = instances_match.group(1)
            if not self.require_org_member(org_id):
                return
            rows = self.db.fetchall(
                "SELECT * FROM instances WHERE org_id = ? ORDER BY created_at",
                (org_id,),
            )
            self.send_json(200, [row_instance(r) for r in rows])
            return

        instance_one = re.fullmatch(r"/org/v1/orgs/([^/]+)/instances/([^/]+)", path)
        if instance_one:
            org_id, inst_id = instance_one.groups()
            if not self.require_org_member(org_id):
                return
            row = self.db.fetchone(
                "SELECT * FROM instances WHERE org_id = ? AND id = ?",
                (org_id, inst_id),
            )
            if not row:
                self.send_json(404, {"error": "instance not found"})
                return
            self.send_json(200, row_instance(row))
            return

        ent_match = re.fullmatch(r"/org/v1/orgs/([^/]+)/entitlements/([^/]+)", path)
        if ent_match:
            org_id, feature_key = ent_match.groups()
            if not self.require_org_member(org_id):
                return
            self.send_json(200, self.check_entitlement(org_id, feature_key))
            return

        hosts_match = re.fullmatch(r"/org/v1/orgs/([^/]+)/hosts", path)
        if hosts_match:
            org_id = hosts_match.group(1)
            if not self.require_org_member(org_id):
                return
            rows = self.db.fetchall(
                "SELECT * FROM hosts WHERE org_id = ? ORDER BY created_at",
                (org_id,),
            )
            self.send_json(200, [row_host(r) for r in rows])
            return

        host_one = re.fullmatch(r"/org/v1/orgs/([^/]+)/hosts/([^/]+)", path)
        if host_one:
            org_id, host_id = host_one.groups()
            if not self.require_org_member(org_id):
                return
            row = self.db.fetchone(
                "SELECT * FROM hosts WHERE org_id = ? AND id = ?",
                (org_id, host_id),
            )
            if not row:
                self.send_json(404, {"error": "host not found"})
                return
            self.send_json(200, row_host(row))
            return

        self.send_json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/org/v1/billing/webhook":
            # Stripe verifies the raw bytes of the body, so handle this route
            # before read_json() consumes the stream.
            payload = self.read_raw_body()
            if not stripe_verify_signature(payload, self.headers.get("Stripe-Signature", "")):
                self.send_json(401, {"error": "invalid stripe signature"})
                return
            try:
                event = json.loads(payload.decode("utf-8"))
            except ValueError:
                self.send_json(400, {"error": "invalid JSON payload"})
                return
            obj = (event.get("data") or {}).get("object") or {}
            ev_type = event.get("type", "")
            if ev_type == "checkout.session.completed":
                billing_apply_checkout(self.db, obj)
            elif ev_type in (
                "customer.subscription.created",
                "customer.subscription.updated",
                "customer.subscription.deleted",
            ):
                billing_apply_subscription(self.db, obj)
            self.send_json(200, {"received": True})
            return

        body = self.read_json()

        if path == "/org/v1/setup":
            if self.db.fetchone("SELECT id FROM organizations LIMIT 1"):
                self.send_json(409, {"error": "already configured"})
                return
            name = str(body.get("name", "")).strip()
            owner_email = str(body.get("ownerEmail", body.get("owner_email", ""))).strip()
            password = str(body.get("password", ""))
            slug = str(body.get("slug", slugify(name))).strip()
            if not name or not owner_email or not password:
                self.send_json(400, {"error": "name, ownerEmail, password required"})
                return
            org_id = new_id("org")
            user_id = new_id("user")
            now = utc_now()
            self.db.execute(
                "INSERT INTO organizations (id, name, slug, edition, created_at) VALUES (?, ?, ?, ?, ?)",
                (org_id, name, slug, "self-host", now),
            )
            self.db.execute(
                "INSERT INTO users (id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (user_id, owner_email, hash_password(password), now),
            )
            self.db.execute(
                "INSERT INTO members (org_id, user_id, role, created_at) VALUES (?, ?, ?, ?)",
                (org_id, user_id, "owner", now),
            )
            token, refresh_token = issue_session(
                self.db, self.jwt_secret, user_id, org_id, "owner", "self-host"
            )
            mcp_key = issue_mcp_key(self.db, org_id)
            self.send_json(
                201,
                {
                    "orgId": org_id,
                    "token": token,
                    "refreshToken": refresh_token,
                    "mcpKey": mcp_key,
                    "expiresIn": ACCESS_TTL_SECONDS,
                },
            )
            return

        mcp_keys_post = re.fullmatch(r"/org/v1/orgs/([^/]+)/mcp-keys", path)
        if mcp_keys_post:
            org_id = mcp_keys_post.group(1)
            if not self.require_org_role(org_id, "admin"):
                return
            label_raw = str(body.get("label") or "").strip()
            label = label_raw or None
            rotate = bool(body.get("rotate", False))
            mcp_key = issue_mcp_key(
                self.db, org_id, label=label, revoke_others=rotate
            )
            self.send_json(200, {"mcpKey": mcp_key, "label": label})
            return

        mcp_rotate = re.fullmatch(r"/org/v1/orgs/([^/]+)/mcp-keys/rotate", path)
        if mcp_rotate:
            org_id = mcp_rotate.group(1)
            if not self.require_org_role(org_id, "admin"):
                return
            label_raw = str(body.get("label") or "").strip()
            mcp_key = issue_mcp_key(
                self.db, org_id, label=label_raw or None, revoke_others=True
            )
            self.send_json(200, {"mcpKey": mcp_key})
            return

        if path == "/org/v1/me/password":
            claims = self.bearer_claims()
            if not claims:
                self.send_json(401, {"error": "unauthorized"})
                return
            user = self.db.fetchone("SELECT * FROM users WHERE id = ?", (claims["sub"],))
            if not user:
                self.send_json(401, {"error": "user not found"})
                return
            current = str(body.get("currentPassword", body.get("current_password", "")))
            new_password = str(body.get("newPassword", body.get("new_password", "")))
            if len(new_password) < 6:
                self.send_json(400, {"error": "new password must be at least 6 characters"})
                return
            if user["password_hash"] and not verify_password(current, user["password_hash"]):
                self.send_json(401, {"error": "current password is incorrect"})
                return
            self.db.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (hash_password(new_password), user["id"]),
            )
            self.send_json(200, {"ok": True})
            return

        discount_redeem = re.fullmatch(r"/org/v1/orgs/([^/]+)/discounts/redeem", path)
        if discount_redeem:
            org_id = discount_redeem.group(1)
            if not self.require_org_role(org_id, "admin"):
                return
            code = str(body.get("code", "")).strip().upper()
            plan = DISCOUNT_CODES.get(code)
            if not plan:
                self.send_json(400, {"error": "unknown discount code"})
                return
            self.db.execute("UPDATE organizations SET plan = ? WHERE id = ?", (plan, org_id))
            self.send_json(200, {"plan": plan, "instanceLimit": plan_instance_limit(plan)})
            return

        billing_session = re.fullmatch(r"/org/v1/orgs/([^/]+)/billing/session", path)
        if billing_session:
            org_id = billing_session.group(1)
            if not self.require_org_role(org_id, "admin"):
                return
            if not stripe_configured():
                self.send_json(503, {"error": "Stripe not configured"})
                return
            plan = str(body.get("plan", "")).strip().lower()
            if plan not in BILLABLE_PLANS:
                self.send_json(400, {"error": "plan must be starter, pro, or scale"})
                return
            org = self.db.fetchone("SELECT * FROM organizations WHERE id = ?", (org_id,))
            if not org:
                self.send_json(404, {"error": "organization not found"})
                return
            owner = self.db.fetchone(
                "SELECT u.email FROM members m JOIN users u ON u.id = m.user_id "
                "WHERE m.org_id = ? AND m.role = 'owner' ORDER BY m.created_at LIMIT 1",
                (org_id,),
            )
            email = owner["email"] if owner else ""
            try:
                session = stripe_checkout_session(
                    org_id, plan, email, org["stripe_customer_id"]
                )
            except RuntimeError as exc:
                self.send_json(502, {"error": str(exc)})
                return
            customer_id = session.get("customer")
            if customer_id and not org["stripe_customer_id"]:
                self.db.execute(
                    "UPDATE organizations SET stripe_customer_id = ? WHERE id = ?",
                    (customer_id, org_id),
                )
            self.send_json(200, {"url": session["url"], "plan": plan})
            return

        billing_portal = re.fullmatch(r"/org/v1/orgs/([^/]+)/billing/portal", path)
        if billing_portal:
            org_id = billing_portal.group(1)
            if not self.require_org_role(org_id, "admin"):
                return
            if not stripe_configured():
                self.send_json(503, {"error": "Stripe not configured"})
                return
            org = self.db.fetchone("SELECT * FROM organizations WHERE id = ?", (org_id,))
            if not org:
                self.send_json(404, {"error": "organization not found"})
                return
            if not org["stripe_customer_id"]:
                self.send_json(
                    409, {"error": "no Stripe customer yet; subscribe via billing/session"}
                )
                return
            try:
                portal = stripe_portal_session(org["stripe_customer_id"])
            except RuntimeError as exc:
                self.send_json(502, {"error": str(exc)})
                return
            self.send_json(200, {"url": portal["url"]})
            return

        if path == "/org/v1/auth/login":
            email = str(body.get("email", "")).strip()
            password = str(body.get("password", ""))
            if self.rate_limited():
                self.send_json(429, {"error": "too many attempts; try again shortly"})
                return
            if login_locked(self.db, email):
                self.send_json(
                    429,
                    {"error": "account temporarily locked; try again later"},
                )
                return
            user = self.db.fetchone("SELECT * FROM users WHERE email = ?", (email,))
            if not user or not verify_password(password, user["password_hash"] or ""):
                record_login_failure(self.db, email)
                self.send_json(401, {"error": "invalid credentials"})
                return
            clear_login_failures(self.db, email)
            if user["mfa_enabled"]:
                code = str(body.get("code", "")).strip()
                if not code or not user_mfa_ok(self.db, user["id"], code):
                    self.send_json(401, {"error": "mfa_required"})
                    return
            member = self.db.fetchone(
                "SELECT org_id, role FROM members WHERE user_id = ? ORDER BY created_at LIMIT 1",
                (user["id"],),
            )
            if not member:
                self.send_json(403, {"error": "no organization membership"})
                return
            edition = self.org_edition(member["org_id"])
            token, refresh_token = issue_session(
                self.db, self.jwt_secret, user["id"], member["org_id"], member["role"], edition
            )
            self.send_json(
                200,
                {
                    "token": token,
                    "refreshToken": refresh_token,
                    "orgId": member["org_id"],
                    "expiresIn": ACCESS_TTL_SECONDS,
                },
            )
            return

        if path == "/org/v1/auth/refresh":
            refresh_token = str(body.get("refreshToken", body.get("refresh_token", ""))).strip()
            if not refresh_token:
                self.send_json(400, {"error": "refreshToken required"})
                return
            result = refresh_session(self.db, self.jwt_secret, refresh_token)
            if not result:
                self.send_json(401, {"error": "invalid or expired refresh token"})
                return
            result["expiresIn"] = ACCESS_TTL_SECONDS
            self.send_json(200, result)
            return

        if path == "/org/v1/auth/switch-org":
            target = str(body.get("orgId", "")).strip()
            claims = self.bearer_claims()
            if not claims or not claims.get("sub"):
                self.send_json(401, {"error": "unauthorized"})
                return
            user = self.db.fetchone("SELECT id, email FROM users WHERE id = ?", (claims["sub"],))
            if not user:
                self.send_json(401, {"error": "user not found"})
                return
            member = self.db.fetchone(
                "SELECT org_id, role FROM members WHERE org_id = ? AND user_id = ?",
                (target, user["id"]),
            )
            if not member:
                self.send_json(403, {"error": "not a member of target organization"})
                return
            edition = self.org_edition(member["org_id"])
            token, refresh_token = issue_session(
                self.db, self.jwt_secret, user["id"], member["org_id"], member["role"], edition
            )
            self.send_json(
                200,
                {
                    "token": token,
                    "refreshToken": refresh_token,
                    "orgId": member["org_id"],
                    "role": member["role"],
                    "edition": edition,
                    "expiresIn": ACCESS_TTL_SECONDS,
                },
            )
            return

        if path == "/org/v1/auth/logout":
            refresh_token = str(body.get("refreshToken", body.get("refresh_token", ""))).strip()
            sid = None
            claims = self.bearer_claims()
            if claims:
                sid = claims.get("sid")
            revoked = revoke_session(self.db, refresh_token or None, sid)
            self.send_json(200, {"ok": True, "revoked": revoked})
            return

        if path == "/org/v1/auth/forgot-password":
            email = str(body.get("email", "")).strip()
            if not email:
                self.send_json(400, {"error": "email required"})
                return
            token, exists = request_password_reset(self.db, email)
            # Always 200 to avoid user enumeration. In dev the reset token is
            # returned directly; production sends it via email (SMTP, TODO).
            payload: dict[str, Any] = {"ok": True}
            if exists and admin_dev_mode():
                payload["resetToken"] = token
            self.send_json(200, payload)
            return

        if path == "/org/v1/auth/reset-password":
            token = str(body.get("token", "")).strip()
            password = str(body.get("password", ""))
            if not token or not password:
                self.send_json(400, {"error": "token and password required"})
                return
            if not reset_password(self.db, token, password):
                self.send_json(400, {"error": "invalid or expired token"})
                return
            self.send_json(200, {"ok": True})
            return

        if path == "/org/v1/auth/verify-email":
            token = str(body.get("token", "")).strip()
            if not token:
                self.send_json(400, {"error": "token required"})
                return
            if not verify_email(self.db, token):
                self.send_json(400, {"error": "invalid or expired token"})
                return
            self.send_json(200, {"ok": True})
            return

        if path == "/org/v1/auth/mfa/setup":
            claims = self.bearer_claims()
            if not claims:
                self.send_json(401, {"error": "unauthorized"})
                return
            user = self.db.fetchone("SELECT * FROM users WHERE id = ?", (claims.get("sub"),))
            if not user:
                self.send_json(401, {"error": "unauthorized"})
                return
            secret = totp_secret()
            self.db.execute(
                "UPDATE users SET mfa_secret = ? WHERE id = ?", (secret, user["id"])
            )
            self.send_json(200, {"secret": secret, "uri": totp_uri(secret, user["email"])})
            return

        if path == "/org/v1/auth/mfa/enable":
            claims = self.bearer_claims()
            if not claims:
                self.send_json(401, {"error": "unauthorized"})
                return
            user_id = claims.get("sub")
            code = str(body.get("code", "")).strip()
            user = self.db.fetchone("SELECT * FROM users WHERE id = ?", (user_id,))
            if not user or not user["mfa_secret"] or not totp_verify(user["mfa_secret"], code):
                self.send_json(400, {"error": "invalid code"})
                return
            self.db.execute("UPDATE users SET mfa_enabled = 1 WHERE id = ?", (user_id,))
            codes = generate_recovery_codes(self.db, user_id)
            self.send_json(200, {"ok": True, "recoveryCodes": codes})
            return

        if path == "/org/v1/auth/mfa/disable":
            claims = self.bearer_claims()
            if not claims:
                self.send_json(401, {"error": "unauthorized"})
                return
            user_id = claims.get("sub")
            code = str(body.get("code", "")).strip()
            user = self.db.fetchone("SELECT * FROM users WHERE id = ?", (user_id,))
            if not user or not user["mfa_secret"] or not totp_verify(user["mfa_secret"], code):
                self.send_json(400, {"error": "invalid code"})
                return
            self.db.execute(
                "UPDATE users SET mfa_enabled = 0, mfa_secret = NULL WHERE id = ?",
                (user_id,),
            )
            self.db.execute("DELETE FROM recovery_codes WHERE user_id = ?", (user_id,))
            self.send_json(200, {"ok": True})
            return

        if path == "/org/v1/orgs":
            claims = self.bearer_claims()
            if not claims:
                self.send_json(401, {"error": "unauthorized"})
                return
            name = str(body.get("name", "")).strip()
            # Default-closed: new cloud orgs are "suspended" (no compute).
            # cloud-paid is granted only via billing (Stripe) later; never
            # trust a client-supplied edition.
            edition = "suspended"
            slug = str(body.get("slug", slugify(name))).strip()
            if not name:
                self.send_json(400, {"error": "name required"})
                return
            org_id = new_id("org")
            now = utc_now()
            self.db.execute(
                "INSERT INTO organizations (id, name, slug, edition, created_at) VALUES (?, ?, ?, ?, ?)",
                (org_id, name, slug, edition, now),
            )
            self.db.execute(
                "INSERT INTO members (org_id, user_id, role, created_at) VALUES (?, ?, ?, ?)",
                (org_id, claims["sub"], "owner", now),
            )
            self.send_json(201, {"id": org_id, "name": name, "slug": slug, "edition": edition})
            return

        org_projects = re.fullmatch(r"/org/v1/orgs/([^/]+)/projects", path)
        if org_projects:
            org_id = org_projects.group(1)
            if not self.require_org_member(org_id):
                return
            gate = self.check_entitlement(org_id, "project.create")
            if gate["code"] == 0:
                self.send_json(403, {"error": "entitlement denied", "entitlement": gate})
                return
            name = str(body.get("name", "")).strip()
            instance_id = str(body.get("instanceId", body.get("instance_id", ""))).strip()
            deployment_mode = str(
                body.get("deploymentMode", body.get("deployment_mode", "dedicated"))
            ).strip()
            region = str(body.get("region", "local")).strip()
            if not name or not instance_id:
                self.send_json(400, {"error": "name and instanceId required"})
                return
            now = utc_now()
            project_id = new_id("proj")
            self.db.execute(
                "INSERT INTO projects "
                "(id, org_id, name, instance_id, deployment_mode, region, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (project_id, org_id, name, instance_id, deployment_mode, region, now, now),
            )
            row = self.db.fetchone("SELECT * FROM projects WHERE id = ?", (project_id,))
            self.send_json(201, row_project(row))
            return

        providers_upsert = re.fullmatch(
            r"/org/v1/orgs/([^/]+)/projects/([^/]+)/providers", path
        )
        if providers_upsert:
            org_id, project_id = providers_upsert.groups()
            if not self.require_org_role(org_id, "admin"):
                return
            provider = str(body.get("provider", "")).strip().lower()
            client_id = str(body.get("clientId", body.get("client_id", ""))).strip()
            client_secret = str(body.get("clientSecret", body.get("client_secret", "")))
            redirect_uris = body.get("redirectUris", body.get("redirect_uris", []))
            enabled = bool(body.get("enabled", True))
            if provider not in OAUTH_PROVIDERS:
                self.send_json(400, {"error": f"unsupported provider={provider}"})
                return
            if not client_id or not client_secret:
                self.send_json(400, {"error": "clientId and clientSecret required"})
                return
            if not isinstance(redirect_uris, list) or not redirect_uris:
                self.send_json(400, {"error": "redirectUris (non-empty list) required"})
                return
            if not kms_configured():
                self.send_json(503, {"error": "KMS not configured (set LIBREBASE_KMS_URL)"})
                return
            try:
                ciphertext, key_id = kms_seal(project_id, client_secret)
            except RuntimeError as exc:
                self.send_json(502, {"error": str(exc)})
                return
            now = utc_now()
            self.db.execute(
                "INSERT INTO auth_providers "
                "(project_id, provider, client_id, client_secret_enc, kms_key_id, redirect_uris, enabled, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(project_id, provider) DO UPDATE SET "
                "client_id = excluded.client_id, client_secret_enc = excluded.client_secret_enc, "
                "kms_key_id = excluded.kms_key_id, redirect_uris = excluded.redirect_uris, "
                "enabled = excluded.enabled, updated_at = excluded.updated_at",
                (
                    project_id,
                    provider,
                    client_id,
                    ciphertext,
                    key_id,
                    json.dumps(redirect_uris),
                    1 if enabled else 0,
                    now,
                    now,
                ),
            )
            row = self.db.fetchone(
                "SELECT * FROM auth_providers WHERE project_id = ? AND provider = ?",
                (project_id, provider),
            )
            self.send_json(200, row_provider(row))
            return

        org_hosts = re.fullmatch(r"/org/v1/orgs/([^/]+)/hosts", path)
        if org_hosts:
            org_id = org_hosts.group(1)
            if not self.require_org_role(org_id, "admin"):
                return
            gate = self.check_entitlement(org_id, "host.create")
            if gate["code"] == 0:
                self.send_json(403, {"error": "entitlement denied", "entitlement": gate})
                return
            name = str(body.get("name", "")).strip()
            if not name:
                self.send_json(400, {"error": "name required"})
                return
            now = utc_now()
            host_id = new_id("host")
            mem_mb = int(body.get("memMb", body.get("mem_mb", 512)))
            provider = str(body.get("provider", "linative-cloud")).strip()
            region = str(body.get("region", "local")).strip()
            status = str(body.get("status", "stopped")).strip()
            self.db.execute(
                "INSERT INTO hosts "
                "(id, org_id, name, provider, region, mem_mb, mem_used_mb, status, "
                "created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, 0, ?, ?, ?)",
                (host_id, org_id, name, provider, region, mem_mb, status, now, now),
            )
            row = self.db.fetchone("SELECT * FROM hosts WHERE id = ?", (host_id,))
            self.send_json(201, row_host(row))
            return

        org_instances = re.fullmatch(r"/org/v1/orgs/([^/]+)/instances", path)
        if org_instances:
            org_id = org_instances.group(1)
            if not self.require_org_role(org_id, "admin"):
                return
            gate = self.check_entitlement(org_id, "instance.launch")
            if gate["code"] == 0:
                self.send_json(403, {"error": "entitlement denied", "entitlement": gate})
                return
            if self.instance_quota_exceeded(org_id):
                limit = plan_instance_limit(self.org_plan(org_id))
                self.send_json(
                    403,
                    {
                        "error": "instance limit reached",
                        "plan": self.org_plan(org_id),
                        "limit": limit,
                    },
                )
                return
            name = str(body.get("name", "")).strip()
            if not name:
                self.send_json(400, {"error": "name required"})
                return
            now = utc_now()
            inst_id = new_id("inst")
            data_dir = str(body.get("dataDir", body.get("data_dir", ""))).strip()
            deployment_mode = str(
                body.get("deploymentMode", body.get("deployment_mode", "dedicated"))
            ).strip()
            runtime_target = str(
                body.get("runtimeTarget", body.get("runtime_target", "local"))
            ).strip()
            region = str(body.get("region", "local")).strip()
            status = str(body.get("status", "stopped")).strip()
            ports = body.get("ports")
            ports_json = json.dumps(ports) if ports else None
            k8s_namespace = body.get("k8sNamespace") or body.get("k8s_namespace")
            k8s_degraded = body.get("k8sDegraded")
            k8s_message = body.get("k8sMessage") or body.get("k8s_message")
            host_id = body.get("hostId") or body.get("host_id")
            mem_limit_mb = body.get("memLimitMb", body.get("mem_limit_mb"))
            if host_id:
                host_row = self.db.fetchone(
                    "SELECT * FROM hosts WHERE org_id = ? AND id = ?",
                    (org_id, host_id),
                )
                if not host_row:
                    self.send_json(404, {"error": "host not found"})
                    return
                mem = int(mem_limit_mb) if mem_limit_mb is not None else 0
                if mem and host_row["mem_used_mb"] + mem > host_row["mem_mb"]:
                    self.send_json(
                        409,
                        {
                            "error": "host memory budget exceeded",
                            "memMb": host_row["mem_mb"],
                            "memUsedMb": host_row["mem_used_mb"],
                            "requestedMb": mem,
                        },
                    )
                    return
            self.db.execute(
                "INSERT INTO instances "
                "(id, org_id, name, data_dir, deployment_mode, runtime_target, region, status, "
                "created_at, updated_at, ports_json, k8s_namespace, k8s_degraded, k8s_message, "
                "host_id, mem_limit_mb) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    inst_id,
                    org_id,
                    name,
                    data_dir,
                    deployment_mode,
                    runtime_target,
                    region,
                    status,
                    now,
                    now,
                    ports_json,
                    k8s_namespace,
                    int(k8s_degraded) if k8s_degraded is not None else None,
                    k8s_message,
                    host_id,
                    int(mem_limit_mb) if mem_limit_mb is not None else None,
                ),
            )
            if host_id and mem_limit_mb:
                self.db.execute(
                    "UPDATE hosts SET mem_used_mb = mem_used_mb + ?, updated_at = ? "
                    "WHERE id = ?",
                    (int(mem_limit_mb), now, host_id),
                )
            if stripe_configured() and stripe_metered_price():
                stripe_report_usage(self.db, org_id)
            row = self.db.fetchone("SELECT * FROM instances WHERE id = ?", (inst_id,))
            self.send_json(201, row_instance(row))
            return

        org_invites = re.fullmatch(r"/org/v1/orgs/([^/]+)/invites", path)
        if org_invites:
            org_id = org_invites.group(1)
            if not self.require_org_role(org_id, "owner"):
                return
            email = str(body.get("email", "")).strip()
            role = str(body.get("role", "developer")).strip()
            if not email:
                self.send_json(400, {"error": "email required"})
                return
            token = secrets.token_urlsafe(24)
            self.db.execute(
                "INSERT INTO invites (org_id, email, role, token, expires_at) VALUES (?, ?, ?, ?, ?)",
                (org_id, email, role, token, "2099-01-01T00:00:00Z"),
            )
            self.send_json(201, {"token": token, "email": email, "role": role})
            return

        invite_accept = re.fullmatch(r"/org/v1/invites/([^/]+)/accept", path)
        if invite_accept:
            token = invite_accept.group(1)
            claims = self.bearer_claims()
            if not claims:
                self.send_json(401, {"error": "unauthorized"})
                return
            inv = self.db.fetchone(
                "SELECT org_id, email, role, expires_at, accepted_at FROM invites WHERE token = ?",
                (token,),
            )
            if not inv:
                self.send_json(404, {"error": "invite not found"})
                return
            if inv["accepted_at"] or utc_now() >= inv["expires_at"]:
                self.send_json(410, {"error": "invite no longer valid"})
                return
            user = self.db.fetchone("SELECT id, email FROM users WHERE id = ?", (claims["sub"],))
            if not user:
                self.send_json(401, {"error": "user not found"})
                return
            if user["email"].lower() != (inv["email"] or "").lower():
                self.send_json(403, {"error": "invite is for another email address"})
                return
            role = inv["role"]
            if role not in ROLE_LEVEL:
                role = "developer"
            existing = self.db.fetchone(
                "SELECT role FROM members WHERE org_id = ? AND user_id = ?",
                (inv["org_id"], user["id"]),
            )
            now = utc_now()
            if not existing:
                self.db.execute(
                    "INSERT INTO members (org_id, user_id, role, created_at) VALUES (?, ?, ?, ?)",
                    (inv["org_id"], user["id"], role, now),
                )
            else:
                # Bump to the invite's role if the inviter specified higher access.
                if ROLE_LEVEL.get(role, 0) > ROLE_LEVEL.get(existing["role"], 0):
                    self.db.execute(
                        "UPDATE members SET role = ? WHERE org_id = ? AND user_id = ?",
                        (role, inv["org_id"], user["id"]),
                    )
            self.db.execute(
                "UPDATE invites SET accepted_at = ? WHERE token = ?", (now, token)
            )
            org = self.db.fetchone("SELECT name FROM organizations WHERE id = ?", (inv["org_id"],))
            self.send_json(
                200,
                {
                    "orgId": inv["org_id"],
                    "orgName": org["name"] if org else "",
                    "role": role,
                    "email": inv["email"],
                },
            )
            return

        self.send_json(404, {"error": "not found"})

    def do_DELETE(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        provider_del = re.fullmatch(
            r"/org/v1/orgs/([^/]+)/projects/([^/]+)/providers/([^/]+)", path
        )
        if provider_del:
            org_id, project_id, provider = provider_del.groups()
            if not self.require_org_role(org_id, "admin"):
                return
            self.db.execute(
                "DELETE FROM auth_providers WHERE project_id = ? AND provider = ?",
                (project_id, provider),
            )
            self.send_json(200, {"ok": True})
            return

        self.send_json(404, {"error": "not found"})

    def do_PATCH(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        body = self.read_json()

        member_match = re.fullmatch(r"/org/v1/members/([^/]+)", path)
        if member_match:
            member_key = member_match.group(1)
            role = str(body.get("role", "")).strip()
            if not role:
                self.send_json(400, {"error": "role required"})
                return
            # member_key is user_id in this MVP
            row = self.db.fetchone(
                "SELECT org_id, user_id FROM members WHERE user_id = ? LIMIT 1",
                (member_key,),
            )
            if not row:
                self.send_json(404, {"error": "member not found"})
                return
            if not self.require_org_role(row["org_id"], "owner"):
                return
            self.db.execute(
                "UPDATE members SET role = ? WHERE org_id = ? AND user_id = ?",
                (role, row["org_id"], row["user_id"]),
            )
            self.send_json(200, {"userId": row["user_id"], "role": role})
            return

        inst_match = re.fullmatch(r"/org/v1/orgs/([^/]+)/instances/([^/]+)", path)
        if inst_match:
            org_id, inst_id = inst_match.groups()
            if not self.require_org_member(org_id):
                return
            fields: list[str] = []
            values: list[Any] = []
            mapping = {
                "status": "status",
                "dataDir": "data_dir",
                "data_dir": "data_dir",
                "k8sNamespace": "k8s_namespace",
                "k8s_namespace": "k8s_namespace",
                "k8sMessage": "k8s_message",
                "k8s_message": "k8s_message",
                "hostId": "host_id",
                "host_id": "host_id",
                "memLimitMb": "mem_limit_mb",
                "mem_limit_mb": "mem_limit_mb",
            }
            for key, col in mapping.items():
                if key in body:
                    fields.append(f"{col} = ?")
                    values.append(body[key])
            if "k8sDegraded" in body or "k8s_degraded" in body:
                fields.append("k8s_degraded = ?")
                val = body.get("k8sDegraded", body.get("k8s_degraded"))
                values.append(int(val) if val is not None else None)
            if "ports" in body:
                fields.append("ports_json = ?")
                values.append(json.dumps(body["ports"]))
            if not fields:
                self.send_json(400, {"error": "no patch fields"})
                return
            fields.append("updated_at = ?")
            values.append(utc_now())
            values.extend([org_id, inst_id])
            self.db.execute(
                f"UPDATE instances SET {', '.join(fields)} WHERE org_id = ? AND id = ?",
                tuple(values),
            )
            row = self.db.fetchone(
                "SELECT * FROM instances WHERE org_id = ? AND id = ?",
                (org_id, inst_id),
            )
            if not row:
                self.send_json(404, {"error": "instance not found"})
                return
            self.send_json(200, row_instance(row))
            return

        self.send_json(404, {"error": "not found"})


def main() -> None:
    host = os.environ.get(
        "LIBREBASE_ADMIN_BIND",
        os.environ.get("LIORG_BIND", "0.0.0.0"),
    )
    port = int(
        os.environ.get(
            "LIBREBASE_ADMIN_PORT",
            os.environ.get("LIORG_PORT", "54330"),
        )
    )
    db_path = Path(
        os.environ.get(
            "LIBREBASE_ADMIN_DB_PATH",
            os.environ.get("LIORG_DB_PATH", str(DEFAULT_DB)),
        )
    )
    secret = os.environ.get(
        "LIBREBASE_ADMIN_JWT_SECRET",
        os.environ.get("LIORG_SESSION_JWT_SECRET", "dev-librebase-admin-secret"),
    )

    db = LiorgDb(db_path)
    LiorgHandler.db = db
    LiorgHandler.jwt_secret = secret

    server = ThreadingHTTPServer((host, port), LiorgHandler)
    sys.stderr.write(f"librebase-admin listening on http://{host}:{port} db={db_path}\n")
    try:
        server.serve_forever()
    finally:
        db.close()


if __name__ == "__main__":
    main()
