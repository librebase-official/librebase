-- Stripe billing: checkouts set plan + cloud-paid; webhook keeps the
-- subscription state in sync. Customer/subscription ids are Stripe's own.
ALTER TABLE organizations ADD COLUMN stripe_customer_id TEXT;
ALTER TABLE organizations ADD COLUMN stripe_subscription_id TEXT;
ALTER TABLE organizations ADD COLUMN stripe_price_id TEXT;
ALTER TABLE organizations ADD COLUMN stripe_status TEXT;
