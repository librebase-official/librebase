-- Librebase Agents: office bots, workspaces, approvals (Dots/Grok/Hermes UX control plane)
-- See planning repo docs/superpowers/specs/2026-10-18-enterprise-agent-harness-design.md

CREATE TABLE IF NOT EXISTS bots (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  name TEXT NOT NULL,
  instructions TEXT NOT NULL DEFAULT '',
  profile TEXT NOT NULL DEFAULT 'office',
  harness TEXT NOT NULL DEFAULT 'pi',
  host_id TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  avatar TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_bots_org ON bots(org_id);

CREATE TABLE IF NOT EXISTS bot_workspaces (
  id TEXT PRIMARY KEY,
  bot_id TEXT NOT NULL UNIQUE,
  org_id TEXT NOT NULL,
  host_id TEXT,
  container_id TEXT,
  volume_path TEXT,
  status TEXT NOT NULL DEFAULT 'stopped',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS approvals (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  bot_id TEXT NOT NULL,
  tool_name TEXT NOT NULL,
  payload_json TEXT NOT NULL DEFAULT '{}',
  payload_hash TEXT,
  state TEXT NOT NULL DEFAULT 'pending',
  requested_by TEXT,
  created_at TEXT NOT NULL,
  resolved_at TEXT,
  resolved_by TEXT
);

CREATE INDEX IF NOT EXISTS idx_approvals_bot_state ON approvals(bot_id, state);
