-- Hosts (rented VMs) — multi-instance placement + resource budget
CREATE TABLE IF NOT EXISTS hosts (
  id TEXT PRIMARY KEY,
  org_id TEXT NOT NULL,
  name TEXT NOT NULL,
  provider TEXT NOT NULL,
  region TEXT NOT NULL,
  mem_mb INTEGER NOT NULL,
  mem_used_mb INTEGER NOT NULL DEFAULT 0,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

ALTER TABLE instances ADD COLUMN host_id TEXT;
ALTER TABLE instances ADD COLUMN mem_limit_mb INTEGER;
