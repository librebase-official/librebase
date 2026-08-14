-- TOTP MFA + recovery codes (console auth)
ALTER TABLE users ADD COLUMN mfa_secret TEXT;
ALTER TABLE users ADD COLUMN mfa_enabled INTEGER NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS recovery_codes (
  user_id TEXT NOT NULL,
  code_hash TEXT PRIMARY KEY,
  created_at TEXT NOT NULL
);
