-- Align OSS MCP token schema with librebase-saas PR #134 (LIB-162).
-- Tokens may bind to bot_id and/or device_code_id; device flow rows use mcp_device_codes.

ALTER TABLE mcp_keys ADD COLUMN device_code_id TEXT;

CREATE INDEX IF NOT EXISTS idx_mcp_keys_device_code ON mcp_keys(device_code_id);

ALTER TABLE mcp_device_sessions RENAME TO mcp_device_codes;
