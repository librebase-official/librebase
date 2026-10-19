-- LIB-139 WP-03: Email Pack (draft → approval → send)

CREATE TABLE IF NOT EXISTS mail_accounts (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  provider TEXT NOT NULL,
  label TEXT,
  from_address TEXT,
  oauth_tokens_enc TEXT,
  kms_key_id TEXT,
  enabled INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_mail_accounts_org ON mail_accounts(org_id);

CREATE TABLE IF NOT EXISTS mail_drafts (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  bot_id TEXT NOT NULL,
  account_id TEXT,
  provider TEXT NOT NULL,
  to_json TEXT NOT NULL DEFAULT '[]',
  cc_json TEXT NOT NULL DEFAULT '[]',
  bcc_json TEXT NOT NULL DEFAULT '[]',
  subject TEXT NOT NULL DEFAULT '',
  body_text TEXT NOT NULL DEFAULT '',
  body_html TEXT,
  content_hash TEXT NOT NULL,
  approval_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'draft',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  created_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_mail_drafts_bot ON mail_drafts(org_id, bot_id);

CREATE TABLE IF NOT EXISTS mail_sends (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  draft_id TEXT NOT NULL UNIQUE,
  provider TEXT NOT NULL,
  provider_message_id TEXT,
  sent_at TEXT NOT NULL,
  sent_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_mail_sends_org ON mail_sends(org_id);
