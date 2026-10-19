-- Optional operator-facing detail when a host VM fails provisioning sync.
ALTER TABLE hosts ADD COLUMN last_error TEXT;
