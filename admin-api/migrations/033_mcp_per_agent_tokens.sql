-- LIB-162: per-agent / per-device MCP tokens (org-wide lb_mcp_* keys remain valid).
-- key_kind: org | agent | device (NULL legacy rows treated as org in application code).

ALTER TABLE mcp_keys ADD COLUMN bot_id TEXT;
ALTER TABLE mcp_keys ADD COLUMN label TEXT;
ALTER TABLE mcp_keys ADD COLUMN key_kind TEXT;
ALTER TABLE mcp_keys ADD COLUMN last_used_at TEXT;
ALTER TABLE mcp_keys ADD COLUMN expires_at TEXT;

CREATE INDEX IF NOT EXISTS idx_mcp_keys_bot ON mcp_keys(org_id, bot_id);
CREATE INDEX IF NOT EXISTS idx_mcp_keys_hash ON mcp_keys(key_hash);

-- RFC 8628-style device authorization (persisted for self-host; no SaaS-only deps).
CREATE TABLE IF NOT EXISTS mcp_device_sessions (
  id TEXT PRIMARY KEY,
  device_code_hash TEXT NOT NULL UNIQUE,
  user_code TEXT NOT NULL UNIQUE,
  client_name TEXT NOT NULL DEFAULT '',
  bot_id TEXT,
  org_id TEXT,
  scope TEXT,
  project_id TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  approved_by TEXT,
  mcp_key_id TEXT,
  access_token TEXT,
  expires_at TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_mcp_device_user_code ON mcp_device_sessions(user_code);
CREATE INDEX IF NOT EXISTS idx_mcp_device_status ON mcp_device_sessions(status);
