-- Optional operator-facing detail when a host VM fails provisioning sync.
ALTER TABLE hosts ADD COLUMN IF NOT EXISTS last_error TEXT;
