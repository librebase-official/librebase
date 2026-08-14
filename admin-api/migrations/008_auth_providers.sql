-- Per-project OAuth provider configuration (client_secret is KMS-sealed).
CREATE TABLE IF NOT EXISTS auth_providers (
  project_id TEXT NOT NULL,
  provider TEXT NOT NULL,
  client_id TEXT NOT NULL,
  client_secret_enc TEXT NOT NULL,
  kms_key_id TEXT NOT NULL,
  redirect_uris TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (project_id, provider)
);
