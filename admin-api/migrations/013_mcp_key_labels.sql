-- Optional label on MCP keys so an org can keep Cursor / Claude / CI keys.
ALTER TABLE mcp_keys ADD COLUMN label TEXT;
