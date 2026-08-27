-- Backfill: self-host edition orgs created before the plan column was added
-- should have plan='self-host' (unlimited), not the default 'suspended' (0 limit).
UPDATE organizations
SET plan = 'self-host'
WHERE edition = 'self-host' AND plan = 'suspended';
