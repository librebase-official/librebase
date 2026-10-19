-- Optional operator-facing detail when a host VM fails provisioning sync.
-- Idempotent: migrate() ignores duplicate-column errors (SQLite + Postgres).
ALTER TABLE hosts ADD COLUMN last_error TEXT;
