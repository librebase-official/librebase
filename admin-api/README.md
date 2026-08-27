# Librebase Admin API

Self-host operator metadata HTTP (orgs, members, projects, instances, entitlements).

Interim Python `ThreadingHTTPServer` + SQLite until li-httpd + lic seam + lidb land.

## Run

```bash
python admin-api/scripts/admin_server.py
# env: LIBREBASE_ADMIN_BIND, LIBREBASE_ADMIN_PORT (54330), LIBREBASE_ADMIN_DB_PATH, LIBREBASE_ADMIN_JWT_SECRET
```

## Smoke

```bash
python admin-api/scripts/smoke_admin.py
```

Exercises: health → setup → unauthenticated 401 → create instance/project → list with Bearer. Migrations are idempotent (`schema_migrations` + safe re-ALTER).

## Auth

Org resource routes (`/org/v1/orgs/{id}/projects|instances|entitlements|…`) require `Authorization: Bearer <jwt>` from setup/login. Public: `/health`, `/org/v1/setup`, `/org/v1/auth/login`.

## Billing (Stripe)

Plans (GA, EUR, `PLANS` in `scripts/admin_server.py`): `sandbox` €0 / `starter` €12 / `pro` €20 / `scale` €99 / `self-host` free / `unlimited` (discount code).

Env vars (VPS admin compose):

```
LIBREBASE_STRIPE_API_KEY=sk_live_…
LIBREBASE_STRIPE_WEBHOOK_SECRET=whsec_…
LIBREBASE_STRIPE_PRICE_STARTER=price_…
LIBREBASE_STRIPE_PRICE_PRO=price_…
LIBREBASE_STRIPE_PRICE_SCALE=price_…
LIBREBASE_STRIPE_METERED_PRICE=price_…      # optional instance metering
LIBREBASE_STRIPE_SUCCESS_URL=https://app.librebase.xyz/admin?billing=success
LIBREBASE_STRIPE_CANCEL_URL=https://app.librebase.xyz/admin?billing=cancel
LIBREBASE_STRIPE_PORTAL_RETURN_URL=https://app.librebase.xyz/admin
```

Webhook URL (Stripe dashboard → Developers → Webhooks →
`checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`):

```
https://app.librebase.xyz/api/admin-proxy/org/v1/billing/webhook
```

The studio `/api/admin-proxy/…` route is a strict allow-list ingress that passes
the raw body + `Stripe-Signature` header through to the private admin-api.
