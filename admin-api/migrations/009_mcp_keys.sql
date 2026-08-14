-- Per-org MCP keys (AI/assistant tool access). Plaintext is shown once; only
-- the sha256 hash is stored. One active key per org (rotating revokes prior).
CREATE TABLE IF NOT EXISTS mcp_keys (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  key_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  revoked_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_mcp_keys_org ON mcp_keys(org_id);
