-- Rented-VM provisioning (Hetzner substrate)
-- Adds the real-server identity + base image + agent bootstrap token.
-- `status` already exists on hosts; allowed values become:
-- stopped | provisioning | running | error
ALTER TABLE hosts ADD COLUMN server_id TEXT;
ALTER TABLE hosts ADD COLUMN ip TEXT;
ALTER TABLE hosts ADD COLUMN image_id TEXT;
ALTER TABLE hosts ADD COLUMN agent_token TEXT;
