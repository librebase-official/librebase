"""Admin API business logic for Email Pack routes (LIB-139)."""
from __future__ import annotations

import json
from typing import Any, Callable, Mapping

from mail_pack import (
    MAIL_OAUTH_SCOPES,
    MailSendError,
    draft_approval_payload,
    draft_content_hash,
    get_adapter,
    parse_draft_body,
    row_mail_account,
    row_mail_account_admin,
    row_mail_draft,
    row_mail_oauth_client,
    row_mail_oauth_client_admin,
    row_mail_provider_default,
    row_mail_send,
)

NewIdFn = Callable[[str], str]
UtcNowFn = Callable[[], str]
HashFn = Callable[[Mapping[str, Any]], str]
KmsSealFn = Callable[[str, str], tuple[str, str]]
KmsUnsealFn = Callable[[str, str], str]


def _draft_row_from_parsed(
    parsed: dict[str, Any], account_id: str | None, from_address: str | None
) -> dict[str, Any]:
    attachments_json = json.dumps(parsed.get("attachments") or [], separators=(",", ":"))
    return {
        "account_id": account_id,
        "to_json": json.dumps(parsed["to"], separators=(",", ":")),
        "cc_json": json.dumps(parsed["cc"], separators=(",", ":")),
        "bcc_json": json.dumps(parsed["bcc"], separators=(",", ":")),
        "subject": parsed["subject"],
        "body_text": parsed["body_text"],
        "body_html": parsed["body_html"],
        "provider": parsed["provider"],
        "from_address": from_address,
        "attachments_json": attachments_json,
    }


def _approval_fields(
    draft_fields: Mapping[str, Any],
) -> dict[str, Any]:
    return dict(draft_fields)


def _sync_approval(
    db: Any,
    approval_id: str,
    approval: Mapping[str, Any] | None,
    payload: dict[str, Any],
    approval_payload_hash: HashFn,
) -> None:
    phash = approval_payload_hash(payload)
    if approval and phash == approval["payload_hash"]:
        return
    payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    if approval and approval["state"] == "approved":
        db.execute(
            "UPDATE approvals SET state = ?, payload_json = ?, payload_hash = ?, "
            "resolved_at = NULL, resolved_by = NULL WHERE id = ?",
            ("pending", payload_json, phash, approval_id),
        )
    elif approval:
        db.execute(
            "UPDATE approvals SET payload_json = ?, payload_hash = ? WHERE id = ?",
            (payload_json, phash, approval_id),
        )


def upsert_mail_oauth_client(
    db: Any,
    org_id: str,
    body: dict[str, Any],
    utc_now: UtcNowFn,
    new_id: NewIdFn,
    kms_configured: Callable[[], bool],
    kms_seal: KmsSealFn,
) -> tuple[int, dict[str, Any]]:
    provider = str(body.get("provider", "")).strip().lower()
    if provider not in ("gmail_oauth", "msgraph"):
        return 400, {"error": "provider must be gmail_oauth or msgraph"}
    client_id = str(body.get("clientId", body.get("client_id", ""))).strip()
    client_secret = str(body.get("clientSecret", body.get("client_secret", "")))
    if not client_id or not client_secret:
        return 400, {"error": "clientId and clientSecret required"}
    scopes = body.get("scopes")
    if scopes is None:
        scopes = MAIL_OAUTH_SCOPES.get(provider, [])
    if not isinstance(scopes, list) or not scopes:
        return 400, {"error": "scopes must be a non-empty array"}
    if not kms_configured():
        return 503, {"error": "KMS not configured (set LIBREBASE_KMS_URL)"}
    try:
        ciphertext, key_id = kms_seal(org_id, client_secret)
    except RuntimeError as exc:
        return 502, {"error": str(exc)}
    now = utc_now()
    existing = db.fetchone(
        "SELECT id FROM mail_oauth_clients WHERE org_id = ? AND provider = ?",
        (org_id, provider),
    )
    scopes_json = json.dumps([str(s) for s in scopes], separators=(",", ":"))
    if existing:
        db.execute(
            "UPDATE mail_oauth_clients SET client_id = ?, client_secret_enc = ?, kms_key_id = ?, "
            "scopes_json = ?, updated_at = ? WHERE org_id = ? AND provider = ?",
            (client_id, ciphertext, key_id, scopes_json, now, org_id, provider),
        )
    else:
        client_row_id = new_id("moc")
        db.execute(
            "INSERT INTO mail_oauth_clients "
            "(id, org_id, provider, client_id, client_secret_enc, kms_key_id, scopes_json, "
            "created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                client_row_id,
                org_id,
                provider,
                client_id,
                ciphertext,
                key_id,
                scopes_json,
                now,
                now,
            ),
        )
    row = db.fetchone(
        "SELECT * FROM mail_oauth_clients WHERE org_id = ? AND provider = ?",
        (org_id, provider),
    )
    return 200, row_mail_oauth_client(row)


def list_mail_oauth_clients(db: Any, org_id: str) -> list[dict[str, Any]]:
    rows = db.fetchall(
        "SELECT * FROM mail_oauth_clients WHERE org_id = ? ORDER BY provider",
        (org_id,),
    )
    return [row_mail_oauth_client(r) for r in rows]


def get_mail_oauth_client_admin(
    db: Any, org_id: str, provider: str
) -> tuple[int, dict[str, Any]]:
    row = db.fetchone(
        "SELECT * FROM mail_oauth_clients WHERE org_id = ? AND provider = ?",
        (org_id, provider),
    )
    if not row:
        return 404, {"error": "mail oauth client not found"}
    return 200, row_mail_oauth_client_admin(row)


def list_mail_provider_defaults(db: Any, org_id: str) -> list[dict[str, Any]]:
    rows = db.fetchall(
        "SELECT * FROM mail_provider_defaults WHERE org_id = ? ORDER BY provider",
        (org_id,),
    )
    return [row_mail_provider_default(r) for r in rows]


def set_mail_provider_default(
    db: Any,
    org_id: str,
    provider: str,
    body: dict[str, Any],
    utc_now: UtcNowFn,
) -> tuple[int, dict[str, Any]]:
    if provider not in ("gmail_oauth", "msgraph", "klaut"):
        return 400, {"error": "invalid provider"}
    account_id = str(body.get("accountId", body.get("account_id", ""))).strip()
    if not account_id:
        return 400, {"error": "accountId required"}
    acct = db.fetchone(
        "SELECT * FROM mail_accounts WHERE org_id = ? AND id = ?",
        (org_id, account_id),
    )
    if not acct:
        return 404, {"error": "mail account not found"}
    if acct["provider"] != provider:
        return 400, {"error": "account provider does not match"}
    now = utc_now()
    db.execute(
        "INSERT INTO mail_provider_defaults (org_id, provider, account_id, updated_at) "
        "VALUES (?, ?, ?, ?) "
        "ON CONFLICT(org_id, provider) DO UPDATE SET account_id = excluded.account_id, "
        "updated_at = excluded.updated_at",
        (org_id, provider, account_id, now),
    )
    row = db.fetchone(
        "SELECT * FROM mail_provider_defaults WHERE org_id = ? AND provider = ?",
        (org_id, provider),
    )
    return 200, row_mail_provider_default(row)


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
    provider = parsed["provider"]
    if provider == "klaut":
        return 200, None, None, None
    account_id = parsed.get("account_id")
    rows = db.fetchall(
        "SELECT * FROM mail_accounts WHERE org_id = ? AND provider = ? AND enabled = 1 "
        "ORDER BY created_at",
        (org_id, provider),
    )
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
    if not rows:
        return 400, None, None, "mail account required for provider (create mail account first)"
    if len(rows) == 1:
        row = rows[0]
        return 200, row["id"], row, None
    default = db.fetchone(
        "SELECT account_id FROM mail_provider_defaults WHERE org_id = ? AND provider = ?",
        (org_id, provider),
    )
    if default:
        row = db.fetchone(
            "SELECT * FROM mail_accounts WHERE org_id = ? AND id = ? AND enabled = 1",
            (org_id, default["account_id"]),
        )
        if row and row["provider"] == provider:
            return 200, row["id"], row, None
    return (
        400,
        None,
        None,
        "multiple mail accounts for this provider; specify accountId or set an org default",
    )


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
    draft_fields = _draft_row_from_parsed(parsed, account_id, from_address)
    payload = draft_approval_payload(_approval_fields(draft_fields))
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
        "subject, body_text, body_html, attachments_json, content_hash, approval_id, status, "
        "created_at, updated_at, created_by) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
            draft_fields["attachments_json"],
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
        "attachments": json.loads(row["attachments_json"] if "attachments_json" in row.keys() and row["attachments_json"] else "[]"),
    }
    for key in (
        "to",
        "cc",
        "bcc",
        "subject",
        "bodyText",
        "bodyHtml",
        "body_text",
        "body_html",
        "accountId",
        "account_id",
        "attachments",
    ):
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
    draft_fields = _draft_row_from_parsed(parsed, account_id, from_address)
    payload = draft_approval_payload(_approval_fields(draft_fields))
    content_hash = draft_content_hash(payload)
    now = utc_now()
    approval = db.fetchone("SELECT * FROM approvals WHERE id = ?", (row["approval_id"],))
    _sync_approval(db, row["approval_id"], approval, payload, approval_payload_hash)
    db.execute(
        "UPDATE mail_drafts SET account_id = ?, to_json = ?, cc_json = ?, bcc_json = ?, "
        "subject = ?, body_text = ?, body_html = ?, attachments_json = ?, content_hash = ?, "
        "updated_at = ? WHERE id = ?",
        (
            account_id,
            draft_fields["to_json"],
            draft_fields["cc_json"],
            draft_fields["bcc_json"],
            draft_fields["subject"],
            draft_fields["body_text"],
            draft_fields["body_html"],
            draft_fields["attachments_json"],
            content_hash,
            now,
            draft_id,
        ),
    )
    updated = db.fetchone("SELECT * FROM mail_drafts WHERE id = ?", (draft_id,))
    approval = db.fetchone("SELECT * FROM approvals WHERE id = ?", (updated["approval_id"],))
    return 200, row_mail_draft(updated, approval)


def _oauth_tokens_for_send(
    db: Any,
    org_id: str,
    provider: str,
    account_row: Mapping[str, Any],
    kms_unseal: KmsUnsealFn,
) -> tuple[str | None, str | None]:
    oauth_plain = None
    if account_row.get("oauth_tokens_enc") and account_row.get("kms_key_id"):
        try:
            oauth_plain = kms_unseal(account_row["kms_key_id"], account_row["oauth_tokens_enc"])
        except RuntimeError as exc:
            raise MailSendError(str(exc), status=502) from exc
    client_row = db.fetchone(
        "SELECT * FROM mail_oauth_clients WHERE org_id = ? AND provider = ?",
        (org_id, provider),
    )
    client_plain = None
    if client_row:
        try:
            secret = kms_unseal(client_row["kms_key_id"], client_row["client_secret_enc"])
        except RuntimeError as exc:
            raise MailSendError(str(exc), status=502) from exc
        client_plain = json.dumps(
            {"client_id": client_row["client_id"], "client_secret": secret},
            separators=(",", ":"),
        )
    return oauth_plain, client_plain


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
    account_row = None
    if row["account_id"]:
        account_row = db.fetchone(
            "SELECT * FROM mail_accounts WHERE org_id = ? AND id = ?",
            (org_id, row["account_id"]),
        )
    draft_fields = {
        "account_id": row["account_id"],
        "from_address": account_row["from_address"] if account_row else None,
        "to_json": row["to_json"],
        "cc_json": row["cc_json"],
        "bcc_json": row["bcc_json"],
        "subject": row["subject"],
        "body_text": row["body_text"],
        "body_html": row["body_html"],
        "attachments_json": row["attachments_json"] if "attachments_json" in row.keys() else "[]",
    }
    payload = draft_approval_payload(draft_fields)
    phash = approval_payload_hash(payload)
    if phash != approval["payload_hash"] or draft_content_hash(payload) != row["content_hash"]:
        return 409, {"error": "draft content changed since approval; re-approve required"}
    oauth_plain = None
    oauth_client_plain = None
    if account_row and row["provider"] != "klaut":
        try:
            oauth_plain, oauth_client_plain = _oauth_tokens_for_send(
                db, org_id, row["provider"], account_row, kms_unseal
            )
        except MailSendError as exc:
            return exc.status, {"error": str(exc)}
        if oauth_plain and oauth_client_plain:
            merged = {**json.loads(oauth_plain), **json.loads(oauth_client_plain)}
            oauth_plain = json.dumps(merged)
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
