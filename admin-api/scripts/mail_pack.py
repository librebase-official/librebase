"""Email Pack adapters — draft → approval → send (LIB-139).

Providers: gmail_oauth, msgraph (stub), klaut (stub). HTTP is injectable for tests.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
from email.message import EmailMessage
from typing import Any, Callable, Mapping, Protocol

MAIL_PROVIDERS = frozenset({"gmail_oauth", "msgraph", "klaut"})

MAIL_OAUTH_SCOPES: dict[str, list[str]] = {
    "gmail_oauth": ["https://www.googleapis.com/auth/gmail.send"],
    "msgraph": ["Mail.Send"],
}

HttpJsonFn = Callable[[str, str, dict[str, str], bytes | None], dict[str, Any]]
HttpJson = HttpJsonFn | None


class MailSendError(Exception):
    def __init__(self, message: str, status: int = 400) -> None:
        super().__init__(message)
        self.status = status


def _default_http_json(
    method: str, url: str, headers: dict[str, str], body: bytes | None
) -> dict[str, Any]:
    import urllib.error
    import urllib.request

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            if not raw:
                return {}
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {"data": parsed}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8")[:500]
        raise MailSendError(f"HTTP {e.code} from {url}: {detail}", status=502) from e


_http_json: HttpJsonFn = _default_http_json


def set_http_json(fn: HttpJsonFn | None) -> None:
    """Test hook — replace Gmail/Graph HTTP calls."""
    global _http_json
    _http_json = fn or _default_http_json


def attachment_content_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def normalize_attachments(raw: Any) -> list[dict[str, str]]:
    """Return stored attachment records with filename, contentHash, contentBase64."""
    if raw is None:
        return []
    items = raw
    if isinstance(raw, str):
        try:
            items = json.loads(raw)
        except json.JSONDecodeError:
            raise MailSendError("attachments must be a JSON array", status=400)
    if not isinstance(items, list):
        raise MailSendError("attachments must be an array", status=400)
    out: list[dict[str, str]] = []
    for item in items:
        if not isinstance(item, dict):
            raise MailSendError("each attachment must be an object", status=400)
        filename = str(item.get("filename", "")).strip()
        if not filename:
            raise MailSendError("attachment filename required", status=400)
        content_b64 = item.get("contentBase64") or item.get("content_base64")
        if content_b64 is None:
            raise MailSendError(f"attachment {filename!r} requires contentBase64", status=400)
        try:
            content = base64.b64decode(str(content_b64), validate=True)
        except (ValueError, TypeError):
            raise MailSendError(f"attachment {filename!r} has invalid base64", status=400)
        provided_hash = item.get("contentHash") or item.get("content_hash")
        chash = str(provided_hash).strip() if provided_hash else attachment_content_hash(content)
        if chash != attachment_content_hash(content):
            raise MailSendError(f"attachment {filename!r} contentHash mismatch", status=400)
        out.append(
            {
                "filename": filename,
                "contentHash": chash,
                "contentBase64": base64.b64encode(content).decode("ascii"),
            }
        )
    out.sort(key=lambda a: a["filename"])
    return out


def attachments_for_approval(stored: Any) -> list[dict[str, str]]:
    if stored is None or stored == "" or stored == "[]":
        return []
    parsed: Any = stored
    if isinstance(stored, str):
        try:
            parsed = json.loads(stored)
        except json.JSONDecodeError:
            return []
    if not isinstance(parsed, list):
        return []
    out: list[dict[str, str]] = []
    for item in parsed:
        if not isinstance(item, dict):
            continue
        filename = item.get("filename")
        chash = item.get("contentHash") or item.get("content_hash")
        if filename and chash:
            out.append({"filename": str(filename), "contentHash": str(chash)})
    out.sort(key=lambda a: a["filename"])
    return out


def draft_approval_payload(draft: Mapping[str, Any]) -> dict[str, Any]:
    """Canonical payload whose hash is stored on the linked approval row."""
    raw_att = draft.get("attachments_json")
    if raw_att is None and "attachments" in draft:
        raw_att = draft.get("attachments")
    return {
        "accountId": draft.get("account_id"),
        "fromAddress": draft.get("from_address"),
        "to": _json_list(draft, "to_json"),
        "cc": _json_list(draft, "cc_json"),
        "bcc": _json_list(draft, "bcc_json"),
        "subject": draft.get("subject") or "",
        "bodyText": draft.get("body_text") or "",
        "bodyHtml": draft.get("body_html"),
        "attachments": attachments_for_approval(raw_att if raw_att is not None else "[]"),
    }


def draft_content_hash(payload: Mapping[str, Any]) -> str:
    import hashlib

    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def _attachments_api_view(row: Mapping[str, Any]) -> list[dict[str, str]]:
    raw = row.get("attachments_json") if "attachments_json" in row.keys() else "[]"
    if not raw:
        return []
    try:
        parsed = json.loads(str(raw))
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [
        {"filename": a.get("filename", ""), "contentHash": a.get("contentHash", "")}
        for a in parsed
        if isinstance(a, dict)
    ]


def _json_list(row: Mapping[str, Any], col: str) -> list[str]:
    raw = row.get(col) if col in row else row.get(col.replace("_json", ""))
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw]
    try:
        parsed = json.loads(str(raw))
        if isinstance(parsed, list):
            return [str(x) for x in parsed]
    except json.JSONDecodeError:
        pass
    return []


def row_mail_account(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "orgId": row["org_id"],
        "provider": row["provider"],
        "label": row["label"] if "label" in row.keys() else None,
        "fromAddress": row["from_address"] if "from_address" in row.keys() else None,
        "enabled": bool(row["enabled"]) if "enabled" in row.keys() else True,
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def row_mail_account_admin(row: Mapping[str, Any]) -> dict[str, Any]:
    out = row_mail_account(row)
    out["oauthTokensEnc"] = row["oauth_tokens_enc"] if "oauth_tokens_enc" in row.keys() else None
    out["kmsKeyId"] = row["kms_key_id"] if "kms_key_id" in row.keys() else None
    return out


def row_mail_oauth_client(row: Mapping[str, Any]) -> dict[str, Any]:
    scopes: list[str] = []
    raw = row["scopes_json"] if "scopes_json" in row.keys() else "[]"
    if raw:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                scopes = [str(s) for s in parsed]
        except json.JSONDecodeError:
            pass
    return {
        "id": row["id"],
        "orgId": row["org_id"],
        "provider": row["provider"],
        "clientId": row["client_id"],
        "scopes": scopes,
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def row_mail_oauth_client_admin(row: Mapping[str, Any]) -> dict[str, Any]:
    out = row_mail_oauth_client(row)
    out["clientSecretEnc"] = row["client_secret_enc"]
    out["kmsKeyId"] = row["kms_key_id"]
    return out


def row_mail_provider_default(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "orgId": row["org_id"],
        "provider": row["provider"],
        "accountId": row["account_id"],
        "updatedAt": row["updated_at"],
    }


def row_mail_draft(row: Mapping[str, Any], approval: Mapping[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "id": row["id"],
        "orgId": row["org_id"],
        "botId": row["bot_id"],
        "accountId": row["account_id"] if "account_id" in row.keys() else None,
        "provider": row["provider"],
        "to": _json_list(row, "to_json"),
        "cc": _json_list(row, "cc_json"),
        "bcc": _json_list(row, "bcc_json"),
        "subject": row["subject"],
        "bodyText": row["body_text"],
        "bodyHtml": row["body_html"] if "body_html" in row.keys() else None,
        "attachments": _attachments_api_view(row),
        "contentHash": row["content_hash"],
        "approvalId": row["approval_id"],
        "status": row["status"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
        "createdBy": row["created_by"] if "created_by" in row.keys() else None,
    }
    if approval is not None:
        payload["approvalState"] = approval["state"]
    return payload


def row_mail_send(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "orgId": row["org_id"],
        "draftId": row["draft_id"],
        "provider": row["provider"],
        "providerMessageId": row["provider_message_id"]
        if "provider_message_id" in row.keys()
        else None,
        "sentAt": row["sent_at"],
        "sentBy": row["sent_by"] if "sent_by" in row.keys() else None,
    }


class MailAdapter(Protocol):
    provider: str

    def send(
        self,
        draft: Mapping[str, Any],
        account: Mapping[str, Any] | None,
        oauth_plain: str | None,
    ) -> str:
        """Return provider message id."""
        ...


class KlautAdapter:
    provider = "klaut"

    def send(
        self,
        draft: Mapping[str, Any],
        account: Mapping[str, Any] | None,
        oauth_plain: str | None,
    ) -> str:
        return f"klaut-{draft['id']}"


class MsGraphAdapter:
    provider = "msgraph"

    def send(
        self,
        draft: Mapping[str, Any],
        account: Mapping[str, Any] | None,
        oauth_plain: str | None,
    ) -> str:
        if not oauth_plain:
            raise MailSendError("msgraph adapter requires OAuth tokens", status=503)
        tokens = json.loads(oauth_plain)
        access = tokens.get("access_token") or tokens.get("accessToken")
        if not access:
            raise MailSendError("msgraph access token missing", status=503)
        to_addrs = _json_list(draft, "to_json")
        body = {
            "message": {
                "subject": draft.get("subject") or "",
                "body": {"contentType": "Text", "content": draft.get("body_text") or ""},
                "toRecipients": [{"emailAddress": {"address": a}} for a in to_addrs],
            },
            "saveToSentItems": True,
        }
        resp = _http_json(
            "POST",
            "https://graph.microsoft.com/v1.0/me/sendMail",
            {
                "Authorization": f"Bearer {access}",
                "Content-Type": "application/json",
            },
            json.dumps(body).encode(),
        )
        return str(resp.get("id") or f"msgraph-{draft['id']}")


class GmailAdapter:
    provider = "gmail_oauth"

    def send(
        self,
        draft: Mapping[str, Any],
        account: Mapping[str, Any] | None,
        oauth_plain: str | None,
    ) -> str:
        if not oauth_plain:
            raise MailSendError("gmail adapter requires OAuth tokens", status=503)
        tokens = json.loads(oauth_plain)
        access = _gmail_access_token(tokens)
        msg = EmailMessage()
        from_addr = None
        if account and account.get("from_address"):
            from_addr = account["from_address"]
        if from_addr:
            msg["From"] = from_addr
        to_addrs = _json_list(draft, "to_json")
        if not to_addrs:
            raise MailSendError("at least one recipient required", status=400)
        msg["To"] = ", ".join(to_addrs)
        cc = _json_list(draft, "cc_json")
        if cc:
            msg["Cc"] = ", ".join(cc)
        msg["Subject"] = draft.get("subject") or ""
        body_text = draft.get("body_text") or ""
        body_html = draft.get("body_html")
        if body_html:
            msg.set_content(body_text)
            msg.add_alternative(body_html, subtype="html")
        else:
            msg.set_content(body_text)
        att_raw = draft.get("attachments_json") if "attachments_json" in draft.keys() else "[]"
        for att in normalize_attachments(att_raw or "[]"):
            msg.add_attachment(
                base64.b64decode(att["contentBase64"]),
                maintype="application",
                subtype="octet-stream",
                filename=att["filename"],
            )
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii").rstrip("=")
        resp = _http_json(
            "POST",
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            {
                "Authorization": f"Bearer {access}",
                "Content-Type": "application/json",
            },
            json.dumps({"raw": raw}).encode(),
        )
        mid = resp.get("id")
        if not mid:
            raise MailSendError("gmail send returned no message id", status=502)
        return str(mid)


def _gmail_access_token(tokens: dict[str, Any]) -> str:
    access = tokens.get("access_token") or tokens.get("accessToken")
    if access:
        return str(access)
    refresh = tokens.get("refresh_token") or tokens.get("refreshToken")
    client_id = tokens.get("client_id") or tokens.get("clientId")
    client_secret = tokens.get("client_secret") or tokens.get("clientSecret")
    if not refresh or not client_id or not client_secret:
        raise MailSendError("gmail tokens incomplete (need refresh + client credentials)", status=503)
    resp = _http_json(
        "POST",
        "https://oauth2.googleapis.com/token",
        {"Content-Type": "application/x-www-form-urlencoded"},
        urlencode_form(
            {
                "grant_type": "refresh_token",
                "refresh_token": refresh,
                "client_id": client_id,
                "client_secret": client_secret,
            }
        ).encode(),
    )
    new_access = resp.get("access_token")
    if not new_access:
        raise MailSendError("gmail token refresh failed", status=502)
    return str(new_access)


def urlencode_form(data: dict[str, str]) -> str:
    from urllib.parse import urlencode

    return urlencode(data)


_ADAPTERS: dict[str, MailAdapter] = {
    "klaut": KlautAdapter(),
    "gmail_oauth": GmailAdapter(),
    "msgraph": MsGraphAdapter(),
}


def get_adapter(provider: str) -> MailAdapter:
    adapter = _ADAPTERS.get(provider)
    if not adapter:
        raise MailSendError(f"unsupported mail provider={provider}", status=400)
    return adapter


def validate_recipients(addrs: list[Any]) -> list[str]:
    out: list[str] = []
    pat = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    for a in addrs:
        s = str(a).strip()
        if not s or not pat.match(s):
            raise MailSendError(f"invalid email address: {a!r}", status=400)
        out.append(s)
    return out


def parse_draft_body(body: dict[str, Any]) -> dict[str, Any]:
    provider = str(body.get("provider", "klaut")).strip().lower()
    if provider not in MAIL_PROVIDERS:
        raise MailSendError(f"provider must be one of {sorted(MAIL_PROVIDERS)}", status=400)
    to_list = validate_recipients(body.get("to") or [])
    cc_list = validate_recipients(body.get("cc") or [])
    bcc_list = validate_recipients(body.get("bcc") or [])
    subject = str(body.get("subject", "")).strip()
    body_text = str(body.get("bodyText", body.get("body_text", "")))
    body_html = body.get("bodyHtml", body.get("body_html"))
    if body_html is not None:
        body_html = str(body_html)
    account_id = body.get("accountId") or body.get("account_id")
    if account_id:
        account_id = str(account_id).strip()
    attachments = normalize_attachments(body.get("attachments"))
    return {
        "provider": provider,
        "to": to_list,
        "cc": cc_list,
        "bcc": bcc_list,
        "subject": subject,
        "body_text": body_text,
        "body_html": body_html,
        "account_id": account_id,
        "attachments": attachments,
    }
