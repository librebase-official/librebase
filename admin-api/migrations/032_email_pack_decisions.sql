-- LIB-139 PM decisions: attachments, provider defaults, dedicated mail OAuth clients

ALTER TABLE mail_drafts ADD COLUMN attachments_json TEXT NOT NULL DEFAULT '[]';

CREATE TABLE IF NOT EXISTS mail_provider_defaults (
  org_id TEXT NOT NULL,
  provider TEXT NOT NULL,
  account_id TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (org_id, provider)
);

CREATE TABLE IF NOT EXISTS mail_oauth_clients (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  provider TEXT NOT NULL,
  client_id TEXT NOT NULL,
  client_secret_enc TEXT NOT NULL,
  kms_key_id TEXT NOT NULL,
  scopes_json TEXT NOT NULL DEFAULT '[]',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(org_id, provider)
);

CREATE INDEX IF NOT EXISTS idx_mail_oauth_clients_org ON mail_oauth_clients(org_id);
