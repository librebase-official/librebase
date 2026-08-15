-- Billing plan: self-host (unlimited) | suspended (0) | starter (1 instance) | pro (3 instances).
ALTER TABLE organizations ADD COLUMN plan TEXT NOT NULL DEFAULT 'suspended';
