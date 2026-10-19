"""MCP bearer token issuance and resolution (LIB-162).

Kept in a dedicated module so the storage model and rotation rules can evolve
when SaaS design (#134 / #135) is finalized without rewriting the HTTP handler.
"""
from __future__ import annotations

import re
import secrets
from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

PREFIX_ORG = "lb_mcp_"
PREFIX_AGENT = "lb_agt_"

KIND_ORG = "org"
KIND_AGENT = "agent"
KIND_DEVICE = "device"

DEVICE_TTL_SECONDS = 30 * 60
DEVICE_POLL_INTERVAL = 5
USER_CODE_RE = re.compile(r"^[A-Z0-9]{4}-?[A-Z0-9]{4}$")


class McpAuthCause(str, Enum):
    OK = "ok"
    UNKNOWN = "unknown_token"
    REVOKED = "revoked"
    EXPIRED = "expired"
    MALFORMED = "malformed_token"


@dataclass(frozen=True)
class McpAuthContext:
    org_id: str
    key_id: str
    key_kind: str
    bot_id: str | None
    role: str = "admin"


def _normalize_user_code(user_code: str) -> str:
    compact = re.sub(r"[^A-Za-z0-9]", "", user_code).upper()
    if len(compact) != 8:
        return user_code.strip().upper()
    return f"{compact[:4]}-{compact[4:]}"


def _new_plaintext(prefix: str) -> str:
    return prefix + secrets.token_urlsafe(32)


def _row_kind(row: Mapping[str, Any]) -> str:
    kind = row["key_kind"] if "key_kind" in row.keys() else None
    if kind:
        return str(kind)
    return KIND_ORG


def row_mcp_key(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "orgId": row["org_id"],
        "botId": row["bot_id"] if "bot_id" in row.keys() else None,
        "label": row["label"] if "label" in row.keys() else None,
        "keyKind": _row_kind(row),
        "createdAt": row["created_at"],
        "revoked": bool(row["revoked_at"]),
        "lastUsedAt": row["last_used_at"] if "last_used_at" in row.keys() else None,
        "expiresAt": row["expires_at"] if "expires_at" in row.keys() else None,
    }


def resolve_bearer(
    db: Any,
    token: str,
    *,
    hash_token: Any,
    utc_now: Any,
    touch_last_used: bool = True,
) -> tuple[McpAuthContext | None, McpAuthCause]:
    if not token:
        return None, McpAuthCause.MALFORMED
    if token.startswith(PREFIX_ORG):
        pass
    elif token.startswith(PREFIX_AGENT):
        pass
    else:
        return None, McpAuthCause.MALFORMED

    row = db.fetchone(
        "SELECT * FROM mcp_keys WHERE key_hash = ?",
        (hash_token(token),),
    )
    if not row:
        return None, McpAuthCause.UNKNOWN
    if row["revoked_at"]:
        return None, McpAuthCause.REVOKED
    expires = row["expires_at"] if "expires_at" in row.keys() else None
    if expires and expires <= utc_now():
        return None, McpAuthCause.EXPIRED

    if touch_last_used:
        db.execute(
            "UPDATE mcp_keys SET last_used_at = ? WHERE id = ?",
            (utc_now(), row["id"]),
        )

    bot_id = row["bot_id"] if "bot_id" in row.keys() else None
    return (
        McpAuthContext(
            org_id=row["org_id"],
            key_id=row["id"],
            key_kind=_row_kind(row),
            bot_id=bot_id,
        ),
        McpAuthCause.OK,
    )


def mcp_claims_from_context(ctx: McpAuthContext) -> dict[str, Any]:
    claims: dict[str, Any] = {
        "sub": "mcp",
        "org_id": ctx.org_id,
        "role": ctx.role,
        "via": "mcp",
        "mcpKeyId": ctx.key_id,
        "mcpKeyKind": ctx.key_kind,
    }
    if ctx.bot_id:
        claims["bot_id"] = ctx.bot_id
    return claims


def issue_org_mcp_key(
    db: Any,
    org_id: str,
    *,
    new_id: Any,
    hash_token: Any,
    utc_now: Any,
) -> str:
    """Issue a console org key; revokes only prior active *org* keys (not agent/device)."""
    key = _new_plaintext(PREFIX_ORG)
    now = utc_now()
    db.execute(
        "UPDATE mcp_keys SET revoked_at = ? WHERE org_id = ? AND revoked_at IS NULL "
        "AND bot_id IS NULL AND (key_kind IS NULL OR key_kind = ?)",
        (now, org_id, KIND_ORG),
    )
    db.execute(
        "INSERT INTO mcp_keys (id, org_id, key_hash, created_at, key_kind, label) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (new_id("mcpk"), org_id, hash_token(key), now, KIND_ORG, "org console"),
    )
    return key


def issue_agent_mcp_token(
    db: Any,
    org_id: str,
    bot_id: str,
    *,
    new_id: Any,
    hash_token: Any,
    utc_now: Any,
    label: str | None = None,
) -> str:
    """Rotate agent token: revoke only the active token for this bot_id."""
    bot = db.fetchone(
        "SELECT id FROM bots WHERE org_id = ? AND id = ?",
        (org_id, bot_id),
    )
    if not bot:
        raise ValueError("bot not found")
    key = _new_plaintext(PREFIX_AGENT)
    now = utc_now()
    db.execute(
        "UPDATE mcp_keys SET revoked_at = ? WHERE org_id = ? AND bot_id = ? "
        "AND revoked_at IS NULL AND key_kind IN (?, ?)",
        (now, org_id, bot_id, KIND_AGENT, KIND_DEVICE),
    )
    db.execute(
        "INSERT INTO mcp_keys (id, org_id, bot_id, key_hash, created_at, key_kind, label) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            new_id("mcpk"),
            org_id,
            bot_id,
            hash_token(key),
            now,
            KIND_AGENT,
            label or f"agent:{bot_id}",
        ),
    )
    return key


def revoke_mcp_key_id(
    db: Any,
    org_id: str,
    key_id: str,
    *,
    utc_now: Any,
) -> bool:
    row = db.fetchone(
        "SELECT id FROM mcp_keys WHERE id = ? AND org_id = ? AND revoked_at IS NULL",
        (key_id, org_id),
    )
    if not row:
        return False
    db.execute(
        "UPDATE mcp_keys SET revoked_at = ? WHERE id = ?",
        (utc_now(), key_id),
    )
    return True


def revoke_all_org_mcp_keys(db: Any, org_id: str, *, utc_now: Any) -> int:
    rows = db.fetchall(
        "SELECT id FROM mcp_keys WHERE org_id = ? AND revoked_at IS NULL",
        (org_id,),
    )
    now = utc_now()
    for row in rows:
        db.execute("UPDATE mcp_keys SET revoked_at = ? WHERE id = ?", (now, row["id"]))
    return len(rows)


def list_agent_mcp_tokens(db: Any, org_id: str, bot_id: str) -> list[dict[str, Any]]:
    rows = db.fetchall(
        "SELECT * FROM mcp_keys WHERE org_id = ? AND bot_id = ? "
        "ORDER BY created_at DESC",
        (org_id, bot_id),
    )
    return [row_mcp_key(r) for r in rows]


def device_start(
    db: Any,
    *,
    client_name: str,
    bot_id: str | None,
    new_id: Any,
    hash_token: Any,
    utc_now: Any,
    utc_now_offset: Any,
    site_base: str,
) -> dict[str, Any]:
    device_code = secrets.token_urlsafe(32)
    user_code = _normalize_user_code(secrets.token_hex(4).upper()[:8])
    now = utc_now()
    expires = utc_now_offset(DEVICE_TTL_SECONDS)
    session_id = new_id("mcps")
    db.execute(
        "INSERT INTO mcp_device_sessions "
        "(id, device_code_hash, user_code, client_name, bot_id, status, expires_at, created_at) "
        "VALUES (?, ?, ?, ?, ?, 'pending', ?, ?)",
        (
            session_id,
            hash_token(device_code),
            user_code,
            client_name or "MCP Agent",
            bot_id,
            expires,
            now,
        ),
    )
    verification_uri = f"{site_base.rstrip('/')}/mcp/authorize"
    return {
        "deviceCode": device_code,
        "userCode": user_code,
        "verificationUri": verification_uri,
        "verificationUriComplete": f"{verification_uri}?user_code={user_code}",
        "expiresIn": DEVICE_TTL_SECONDS,
        "interval": DEVICE_POLL_INTERVAL,
    }


def device_view(
    db: Any,
    user_code: str,
    *,
    utc_now: Any,
    memberships: list[dict[str, Any]],
    active_org_id: str | None,
) -> dict[str, Any] | None:
    code = _normalize_user_code(user_code)
    row = db.fetchone(
        "SELECT * FROM mcp_device_sessions WHERE user_code = ?",
        (code,),
    )
    if not row:
        return None
    status = row["status"]
    if status == "pending" and row["expires_at"] <= utc_now():
        status = "expired"
    return {
        "userCode": row["user_code"],
        "clientName": row["client_name"],
        "expiresAt": row["expires_at"],
        "status": status,
        "botId": row["bot_id"],
        "memberships": memberships,
        "activeOrgId": active_org_id,
    }


def device_approve(
    db: Any,
    user_code: str,
    org_id: str,
    approver_user_id: str,
    *,
    bot_id: str | None,
    scope: str | None,
    project_id: str | None,
    new_id: Any,
    hash_token: Any,
    utc_now: Any,
) -> dict[str, Any]:
    code = _normalize_user_code(user_code)
    row = db.fetchone(
        "SELECT * FROM mcp_device_sessions WHERE user_code = ?",
        (code,),
    )
    if not row:
        raise ValueError("unknown device code")
    if row["status"] != "pending":
        raise ValueError("device session not pending")
    if row["expires_at"] <= utc_now():
        raise ValueError("device code expired")
    bound_bot = bot_id or row["bot_id"]
    access = _new_plaintext(PREFIX_AGENT)
    now = utc_now()
    key_id = new_id("mcpk")
    db.execute(
        "INSERT INTO mcp_keys (id, org_id, bot_id, key_hash, created_at, key_kind, label) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            key_id,
            org_id,
            bound_bot,
            hash_token(access),
            now,
            KIND_DEVICE,
            row["client_name"] or "device flow",
        ),
    )
    db.execute(
        "UPDATE mcp_device_sessions SET status = 'approved', org_id = ?, bot_id = ?, "
        "scope = ?, project_id = ?, approved_by = ?, mcp_key_id = ?, access_token = ? "
        "WHERE id = ?",
        (org_id, bound_bot, scope, project_id, approver_user_id, key_id, access, row["id"]),
    )
    return {"ok": True, "status": "approved", "orgId": org_id}


def device_deny(db: Any, user_code: str, *, utc_now: Any) -> dict[str, Any]:
    code = _normalize_user_code(user_code)
    row = db.fetchone(
        "SELECT * FROM mcp_device_sessions WHERE user_code = ?",
        (code,),
    )
    if not row:
        raise ValueError("unknown device code")
    db.execute(
        "UPDATE mcp_device_sessions SET status = 'denied' WHERE id = ?",
        (row["id"],),
    )
    return {"ok": True, "status": "denied"}


def device_poll_token(
    db: Any,
    device_code: str,
    *,
    hash_token: Any,
    utc_now: Any,
) -> dict[str, Any]:
    row = db.fetchone(
        "SELECT * FROM mcp_device_sessions WHERE device_code_hash = ?",
        (hash_token(device_code),),
    )
    if not row:
        return {"error": "invalid_grant"}
    if row["expires_at"] <= utc_now():
        return {"error": "expired_token"}
    if row["status"] == "denied":
        return {"error": "access_denied"}
    if row["status"] == "pending":
        return {"error": "authorization_pending", "interval": DEVICE_POLL_INTERVAL}
    if row["status"] != "approved":
        return {"error": "invalid_grant"}
    access = row["access_token"] if "access_token" in row.keys() else None
    if not access:
        key_row = db.fetchone("SELECT * FROM mcp_keys WHERE id = ?", (row["mcp_key_id"],))
        if not key_row or key_row["revoked_at"]:
            return {"error": "revoked"}
        return {"error": "invalid_grant"}
    key_row = db.fetchone("SELECT * FROM mcp_keys WHERE id = ?", (row["mcp_key_id"],))
    if not key_row or key_row["revoked_at"]:
        return {"error": "revoked"}
    db.execute(
        "UPDATE mcp_device_sessions SET access_token = NULL WHERE id = ?",
        (row["id"],),
    )
    return {
        "accessToken": access,
        "tokenType": "Bearer",
        "orgId": row["org_id"],
        "role": "admin",
    }
