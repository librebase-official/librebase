-- MCP usage log — tracks every tool call through the hosted MCP endpoint.
-- Used for analytics dashboards, billing, and abuse detection.
CREATE TABLE IF NOT EXISTS mcp_usage_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  org_id TEXT NOT NULL,
  mcp_key_id TEXT,
  tool_name TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'ok',        -- 'ok' | 'error' | 'rate_limited' | 'auth_error'
  latency_ms INTEGER,
  ip_address TEXT,
  user_agent TEXT,
  error_message TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_mcp_usage_org ON mcp_usage_log(org_id);
CREATE INDEX IF NOT EXISTS idx_mcp_usage_tool ON mcp_usage_log(tool_name);
CREATE INDEX IF NOT EXISTS idx_mcp_usage_created ON mcp_usage_log(created_at);
