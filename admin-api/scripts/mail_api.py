"""Admin API business logic for Email Pack routes (LIB-139)."""
from __future__ import annotations

import json
from typing import Any, Callable, Mapping

from mail_pack import (
    MailSendError,
    draft_approval_payload,
    draft_content_hash,
    get_adapter,
    parse_draft_body,
    row_mail_account,
    row_mail_account_admin,
    row_mail_draft,
    row_mail_send,
)

NewIdFn = Callable[[str], str]
UtcNowFn = Callable[[], str]
HashFn = Callable[[Mapping[str, Any]], str]
KmsSealFn = Callable[[str, str], tuple[str, str]]
KmsUnsealFn = Callable[[str, str], str]


def _draft_row_from_parsed(parsed: dict[str, Any], from_address: str | None = None) -> dict[str, Any]:
    return {
        "to_json": json.dumps(parsed["to"], separators=(",", ":")),
        "cc_json": json.dumps(parsed["cc"], separators=(",", ":")),
        "bcc_json": json.dumps(parsed["bcc"], separators=(",", ":")),
        "subject": parsed["subject"],
        "body_text": parsed["body_text"],
        "body_html": parsed["body_html"],
        "provider": parsed["provider"],
        "from_address": from_address,
    }


def create_mail_account(
    db: Any,
    org_id: str,
    body: dict[str, Any],
    utc_now: UtcNowFn,
    new_id: NewIdFn,
    kms_configured: Callable[[], bool],
    kms_seal: KmsSealFn,
) -> tuple[int, dict[str, Any]]:
    provider = str(body.get("provider", "")).strip().lower()
    if provider not in ("gmail_oauth", "msgraph", "klaut"):
        return 400, {"error": "provider must be gmail_oauth, msgraph, or klaut"}
    label = body.get("label")
    from_address = body.get("fromAddress") or body.get("from_address")
    oauth_tokens = body.get("oauthTokens") or body.get("oauth_tokens")
    ciphertext = None
    key_id = None
    if oauth_tokens is not None:
        if not kms_configured():
            return 503, {"error": "KMS not configured (set LIBREBASE_KMS_URL)"}
        try:
            plaintext = json.dumps(oauth_tokens, sort_keys=True, separators=(",", ":"))
            ciphertext, key_id = kms_seal(org_id, plaintext)
        except RuntimeError as exc:
            return 502, {"error": str(exc)}
    now = utc_now()
    account_id = new_id("mac")
    db.execute(
        "INSERT INTO mail_accounts "
        "(id, org_id, provider, label, from_address, oauth_tokens_enc, kms_key_id, "
        "enabled, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            account_id,
            org_id,
            provider,
            label,
            from_address,
            ciphertext,
            key_id,
            1,
            now,
            now,
        ),
    )
    row = db.fetchone("SELECT * FROM mail_accounts WHERE id = ?", (account_id,))
    return 201, row_mail_account(row)


def list_mail_accounts(db: Any, org_id: str) -> list[dict[str, Any]]:
    rows = db.fetchall(
        "SELECT * FROM mail_accounts WHERE org_id = ? ORDER BY created_at",
        (org_id,),
    )
    return [row_mail_account(r) for r in rows]


def get_mail_account_admin(db: Any, org_id: str, account_id: str) -> tuple[int, dict[str, Any]]:
    row = db.fetchone(
        "SELECT * FROM mail_accounts WHERE org_id = ? AND id = ?",
        (org_id, account_id),
    )
    if not row:
        return 404, {"error": "mail account not found"}
    return 200, row_mail_account_admin(row)


def _resolve_account(
    db: Any, org_id: str, parsed: dict[str, Any]
) -> tuple[int, str | None, Mapping[str, Any] | None, str | None]:
    account_id = parsed.get("account_id")
    provider = parsed["provider"]
    if account_id:
        row = db.fetchone(
            "SELECT * FROM mail_accounts WHERE org_id = ? AND id = ?",
            (org_id, account_id),
        )
        if not row:
            return 400, None, None, "mail account not found"
        if row["provider"] != provider:
            return 400, None, None, "mail account provider mismatch"
        return 200, account_id, row, None
    if provider == "klaut":
        return 200, None, None, None
    row = db.fetchone(
        "SELECT * FROM mail_accounts WHERE org_id = ? AND provider = ? AND enabled = 1 "
        "ORDER BY created_at LIMIT 1",
        (org_id, provider),
    )
    if not row:
        return 400, None, None, "mail account required for provider (create mail account first)"
    return 200, row["id"], row, None


def create_mail_draft(
    db: Any,
    org_id: str,
    bot_id: str,
    body: dict[str, Any],
    created_by: str,
    utc_now: UtcNowFn,
    new_id: NewIdFn,
    approval_payload_hash: HashFn,
) -> tuple[int, dict[str, Any]]:
    try:
        parsed = parse_draft_body(body)
    except MailSendError as exc:
        return exc.status, {"error": str(exc)}
    st, account_id, account_row, err = _resolve_account(db, org_id, parsed)
    if st != 200:
        return 400, {"error": err or "mail account required"}
    from_address = account_row["from_address"] if account_row else None
    draft_fields = _draft_row_from_parsed(parsed, from_address)
    payload = draft_approval_payload(draft_fields)
    content_hash = draft_content_hash(payload)
    now = utc_now()
    draft_id = new_id("mdr")
    approval_id = new_id("apr")
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    phash = approval_payload_hash(payload)
    db.execute(
        "INSERT INTO approvals "
        "(id, org_id, bot_id, tool_name, payload_json, payload_hash, state, "
        "created_at, resolved_at, resolved_by, requested_by) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?)",
        (
            approval_id,
            org_id,
            bot_id,
            "mail.send",
            payload_json,
            phash,
            "pending",
            now,
            created_by,
        ),
    )
    db.execute(
        "INSERT INTO mail_drafts "
        "(id, org_id, bot_id, account_id, provider, to_json, cc_json, bcc_json, "
        "subject, body_text, body_html, content_hash, approval_id, status, "
        "created_at, updated_at, created_by) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            draft_id,
            org_id,
            bot_id,
            account_id,
            parsed["provider"],
            draft_fields["to_json"],
            draft_fields["cc_json"],
            draft_fields["bcc_json"],
            draft_fields["subject"],
            draft_fields["body_text"],
            draft_fields["body_html"],
            content_hash,
            approval_id,
            "draft",
            now,
            now,
            created_by,
        ),
    )
    row = db.fetchone("SELECT * FROM mail_drafts WHERE id = ?", (draft_id,))
    approval = db.fetchone("SELECT * FROM approvals WHERE id = ?", (approval_id,))
    return 201, row_mail_draft(row, approval)


def get_mail_draft(db: Any, org_id: str, bot_id: str, draft_id: str) -> tuple[int, dict[str, Any]]:
    row = db.fetchone(
        "SELECT * FROM mail_drafts WHERE org_id = ? AND bot_id = ? AND id = ?",
        (org_id, bot_id, draft_id),
    )
    if not row:
        return 404, {"error": "draft not found"}
    approval = db.fetchone("SELECT * FROM approvals WHERE id = ?", (row["approval_id"],))
    return 200, row_mail_draft(row, approval)


def list_mail_drafts(db: Any, org_id: str, bot_id: str) -> list[dict[str, Any]]:
    rows = db.fetchall(
        "SELECT * FROM mail_drafts WHERE org_id = ? AND bot_id = ? ORDER BY created_at",
        (org_id, bot_id),
    )
    out: list[dict[str, Any]] = []
    for row in rows:
        approval = db.fetchone("SELECT * FROM approvals WHERE id = ?", (row["approval_id"],))
        out.append(row_mail_draft(row, approval))
    return out


def patch_mail_draft(
    db: Any,
    org_id: str,
    bot_id: str,
    draft_id: str,
    body: dict[str, Any],
    utc_now: UtcNowFn,
    approval_payload_hash: HashFn,
) -> tuple[int, dict[str, Any]]:
    row = db.fetchone(
        "SELECT * FROM mail_drafts WHERE org_id = ? AND bot_id = ? AND id = ?",
        (org_id, bot_id, draft_id),
    )
    if not row:
        return 404, {"error": "draft not found"}
    if row["status"] == "sent":
        return 409, {"error": "draft already sent"}
    merged = {
        "provider": row["provider"],
        "to": json.loads(row["to_json"]),
        "cc": json.loads(row["cc_json"]),
        "bcc": json.loads(row["bcc_json"]),
        "subject": row["subject"],
        "bodyText": row["body_text"],
        "bodyHtml": row["body_html"],
        "accountId": row["account_id"],
    }
    for key in ("to", "cc", "bcc", "subject", "bodyText", "bodyHtml", "body_text", "body_html"):
        if key in body:
            merged[key] = body[key]
    try:
        parsed = parse_draft_body(merged)
    except MailSendError as exc:
        return exc.status, {"error": str(exc)}
    st, account_id, account_row, err = _resolve_account(db, org_id, parsed)
    if st != 200:
        return 400, {"error": err or "mail account required"}
    from_address = account_row["from_address"] if account_row else None
    draft_fields = _draft_row_from_parsed(parsed, from_address)
    payload = draft_approval_payload(draft_fields)
    content_hash = draft_content_hash(payload)
    now = utc_now()
    approval = db.fetchone("SELECT * FROM approvals WHERE id = ?", (row["approval_id"],))
    if approval and approval["state"] == "approved" and content_hash != approval["payload_hash"]:
        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        phash = approval_payload_hash(payload)
        db.execute(
            "UPDATE approvals SET state = ?, payload_json = ?, payload_hash = ?, "
            "resolved_at = NULL, resolved_by = NULL WHERE id = ?",
            ("pending", payload_json, phash, row["approval_id"]),
        )
    elif approval and approval["state"] == "pending":
        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        phash = approval_payload_hash(payload)
        db.execute(
            "UPDATE approvals SET payload_json = ?, payload_hash = ? WHERE id = ?",
            (payload_json, phash, row["approval_id"]),
        )
    db.execute(
        "UPDATE mail_drafts SET account_id = ?, to_json = ?, cc_json = ?, bcc_json = ?, "
        "subject = ?, body_text = ?, body_html = ?, content_hash = ?, updated_at = ? "
        "WHERE id = ?",
        (
            account_id,
            draft_fields["to_json"],
            draft_fields["cc_json"],
            draft_fields["bcc_json"],
            draft_fields["subject"],
            draft_fields["body_text"],
            draft_fields["body_html"],
            content_hash,
            now,
            draft_id,
        ),
    )
    updated = db.fetchone("SELECT * FROM mail_drafts WHERE id = ?", (draft_id,))
    approval = db.fetchone("SELECT * FROM approvals WHERE id = ?", (updated["approval_id"],))
    return 200, row_mail_draft(updated, approval)


def send_mail_draft(
    db: Any,
    org_id: str,
    bot_id: str,
    draft_id: str,
    sent_by: str,
    utc_now: UtcNowFn,
    new_id: NewIdFn,
    approval_payload_hash: HashFn,
    kms_unseal: KmsUnsealFn,
) -> tuple[int, dict[str, Any]]:
    existing = db.fetchone(
        "SELECT * FROM mail_sends WHERE draft_id = ?",
        (draft_id,),
    )
    if existing:
        out = row_mail_send(existing)
        out["idempotent"] = True
        return 200, out
    row = db.fetchone(
        "SELECT * FROM mail_drafts WHERE org_id = ? AND bot_id = ? AND id = ?",
        (org_id, bot_id, draft_id),
    )
    if not row:
        return 404, {"error": "draft not found"}
    if row["status"] == "sent":
        existing = db.fetchone("SELECT * FROM mail_sends WHERE draft_id = ?", (draft_id,))
        if existing:
            out = row_mail_send(existing)
            out["idempotent"] = True
            return 200, out
        return 409, {"error": "draft already sent"}
    approval = db.fetchone("SELECT * FROM approvals WHERE id = ?", (row["approval_id"],))
    if not approval:
        return 409, {"error": "approval missing"}
    if approval["state"] != "approved":
        return 403, {"error": "draft not approved", "state": approval["state"]}
    payload = draft_approval_payload(row)
    phash = approval_payload_hash(payload)
    if phash != approval["payload_hash"] or draft_content_hash(payload) != row["content_hash"]:
        return 409, {"error": "draft content changed since approval; re-approve required"}
    account_row = None
    oauth_plain = None
    if row["account_id"]:
        account_row = db.fetchone(
            "SELECT * FROM mail_accounts WHERE org_id = ? AND id = ?",
            (org_id, row["account_id"]),
        )
        if account_row and account_row["oauth_tokens_enc"] and account_row["kms_key_id"]:
            try:
                oauth_plain = kms_unseal(account_row["kms_key_id"], account_row["oauth_tokens_enc"])
            except RuntimeError as exc:
                return 502, {"error": str(exc)}
    try:
        adapter = get_adapter(row["provider"])
        message_id = adapter.send(row, account_row, oauth_plain)
    except MailSendError as exc:
        return exc.status, {"error": str(exc)}
    now = utc_now()
    send_id = new_id("msd")
    db.execute(
        "INSERT INTO mail_sends "
        "(id, org_id, draft_id, provider, provider_message_id, sent_at, sent_by) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (send_id, org_id, draft_id, row["provider"], message_id, now, sent_by),
    )
    db.execute(
        "UPDATE mail_drafts SET status = ?, updated_at = ? WHERE id = ?",
        ("sent", now, draft_id),
    )
    send_row = db.fetchone("SELECT * FROM mail_sends WHERE id = ?", (send_id,))
    out = row_mail_send(send_row)
    out["idempotent"] = False
    return 200, out
