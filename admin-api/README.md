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
