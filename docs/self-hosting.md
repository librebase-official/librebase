<<<<<<< HEAD
# Self-hosting Librebase (OSS)

Run **Librebase Studio**, the **Admin API**, and **KMS** on your own machine or VM. This path uses `deploy/compose/docker-compose.yml` — no Hetzner, Stripe, or other SaaS-only provisioning is required for a working control plane.

For database/runtime workloads (lidb instances on the same host, Kubernetes, or licontainer), see [kubernetes.md](kubernetes.md) and [architecture-instances.md](architecture-instances.md). This runbook covers the **console + operator API** stack only.

## Prerequisites

- Docker Engine 24+ with Compose v2
- A public URL or local-only access (loopback ports are the default)
- TLS termination in front of Studio if you expose it on the internet (reverse proxy; not included in the minimal compose file)

## Quick start (Compose)

1. Copy the environment template:

   ```bash
   cp deploy/compose/.env.example deploy/compose/.env
   ```

2. Generate secrets (examples — use your own values):

   ```bash
   openssl rand -hex 32   # LIBREBASE_ADMIN_JWT_SECRET
   openssl rand -hex 32   # LIBREBASE_KMS_SERVICE_ROLE
   ```

3. Edit `deploy/compose/.env`: set `NEXT_PUBLIC_SITE_URL` and `LIBREBASE_CONSOLE_URL` to the URL users will open (e.g. `https://studio.example.com` or `http://127.0.0.1:3005` for local-only).

4. From `deploy/compose/`:

   ```bash
   docker compose up -d --build
   ```

5. Open Studio at the URL you configured (compose binds Studio on `127.0.0.1:3005` by default — put nginx or Caddy on the host if you need HTTPS or a public hostname).

6. Complete **first-time setup** in the browser (`/setup`): create the org admin account. The Admin API applies SQLite migrations automatically on startup.

## Services and ports

| Service | Compose name | Default bind | Role |
|---------|--------------|--------------|------|
| Studio | `studio` | `127.0.0.1:3005` | Next.js console; talks to Admin API over the compose network |
| Admin API | `librebase-admin` | `127.0.0.1:54330` | Orgs, projects, instances metadata, MCP keys, auth |
| KMS | `kms` | internal `54340` | Seals project secrets; Admin API calls it with `LIBREBASE_KMS_SERVICE_ROLE` |

Volumes `librebase-admin-data` and `librebase-kms-data` hold SQLite databases. Back them up before upgrades.

## Required environment variables

See [`deploy/compose/.env.example`](../deploy/compose/.env.example) for the full list with placeholders.

| Variable | Required | Notes |
|----------|----------|--------|
| `LIBREBASE_ADMIN_JWT_SECRET` | yes | Signs session JWTs for Admin API |
| `LIBREBASE_KMS_SERVICE_ROLE` | yes | Bearer token Studio/Admin use to call KMS |
| `NEXT_PUBLIC_SITE_URL` | yes (build) | Public origin for Studio (OAuth redirects, MCP discovery) |
| `LIBREBASE_CONSOLE_URL` | recommended | Admin API email/links; should match Studio origin |
| `LIBREBASE_VERSION` | yes (build) | Set in `deploy/compose/.env`; Compose reads `${LIBREBASE_VERSION}` from that file only. `scripts/sync-version.py` updates `deploy/compose/compose.env` as a repo reference — copy the value into `.env` when upgrading. |

Optional (only if you enable those features):

- `LIBREBASE_GOOGLE_CLIENT_ID` / `LIBREBASE_GOOGLE_CLIENT_SECRET` — Google sign-in
- `LIBREBASE_GITHUB_CLIENT_ID` / `LIBREBASE_GITHUB_CLIENT_SECRET` — GitHub sign-in
- `LIBREBASE_RUNTIME=local` — default local lidb/dev runtime from Studio (`LIBREBASE_HARNESS=oss` for Kubernetes/licontainer on your infra)

Do **not** commit real secrets. `.env` is gitignored; use `.env.example` as the template only.

## First run checklist

1. `docker compose ps` — all services healthy (`librebase-admin` healthcheck on `/health`).
2. Visit `/setup` once; login at `/login` afterward.
3. Studio reaches Admin API via `LIBREBASE_ADMIN_URL=http://librebase-admin:54330` (set in compose; do not expose Admin API publicly).
4. Create a project and launch a **local** runtime instance, or attach Kubernetes/licontainer per [kubernetes.md](kubernetes.md).

Optional: smoke test the Admin API process directly (not a check of the Compose stack):

```bash
python admin-api/scripts/smoke_admin.py
```

`smoke_admin.py` is a standalone Admin API smoke test against a running `admin_server.py` (local Python env); it does not validate Studio, KMS, or `docker compose` wiring. See [admin-api/README.md](../admin-api/README.md).

## Migrations

Admin API and KMS apply SQL migrations from `admin-api/migrations/` and KMS schema on startup (`schema_migrations` table). No manual migration step is required for a fresh install.

If you restore an older volume backup onto a newer image, start the stack once and watch logs for migration errors before serving traffic.

## Upgrades

1. Back up Docker volumes (`librebase-admin-data`, `librebase-kms-data`).
2. Bump `LIBREBASE_VERSION` in `deploy/compose/.env` (after pulling the new release). If you use `python3 scripts/sync-version.py` from the repo root, copy the version from `deploy/compose/compose.env` into `.env` — Compose does not load `compose.env` automatically.
3. `docker compose up -d --build` from `deploy/compose/`.
4. Verify `/health` on Admin API and sign-in to Studio.

## Reverse proxy (recommended for production)

The compose file keeps Studio and Admin API on loopback. Terminate TLS on the host (e.g. `deploy/nginx-librebase.xyz.conf` as a reference) and proxy to `127.0.0.1:3005`. Never publish `54330` to the internet.

## MCP and agents on self-host

Point agents at your Studio origin:

- Discovery: `GET {SITE_URL}/.well-known/mcp.json`
- Endpoint: `POST {SITE_URL}/api/mcp`
- Stdio bridge env: `LIBREBASE_MCP_URL`, `LIBREBASE_MCP_TOKEN` — see [mcp/README.md](../mcp/README.md).

**Migration:** older installs may still set `LIBREBASE_MCP_KEY`. The stdio bridges accept it as a deprecated alias (`LIBREBASE_MCP_TOKEN` wins if both are set). Rename to `LIBREBASE_MCP_TOKEN` when you next rotate credentials.

## Related docs

- [admin-api/README.md](../admin-api/README.md) — API auth and env reference
- [kms/README.md](../kms/README.md) — KMS service
- [architecture-instances.md](architecture-instances.md) — dedicated vs shared instances
- [cli-db.md](cli-db.md) — local lidb / `lis` workflows
=======
# Self-hosting Librebase (Docker Compose)

Run **Librebase Studio**, the **Librebase Admin API**, and **KMS** on your own machine with the OSS stack in `deploy/compose/docker-compose.yml`. No managed cloud services are required for the default compose file.

## Prerequisites

- Docker Engine with Compose v2
- Ports available on the host: `3005` (Studio), `54330` (Admin, loopback-only publish)

## Quick start

From the repository root:

```bash
cd deploy/compose
cp .env.example .env
# Edit .env: set LIBREBASE_ADMIN_JWT_SECRET and LIBREBASE_KMS_SERVICE_ROLE to long random strings.

docker compose --env-file compose.env build
docker compose --env-file compose.env up -d
```

Open Studio at `http://127.0.0.1:3005`. The first human visit can use the `/setup` UI, or use **headless onboarding** below.

### Networking

- **Studio** uses `LIBREBASE_ADMIN_URL=http://librebase-admin:54330` on the internal compose network.
- **Admin** must bind `0.0.0.0` inside its container (set in compose). Do not set `LIBREBASE_ADMIN_BIND=127.0.0.1` in `.env` for Docker — other containers cannot reach a loopback-only listener.

## Headless onboarding (API + MCP)

Use this when you are automating install (no browser) or issuing keys for agents.

### 1. First-run setup

`POST /org/v1/setup` is allowed only while the database has no organization.

```bash
ADMIN=http://127.0.0.1:54330

curl -sS -X POST "$ADMIN/org/v1/setup" \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "My Org",
    "ownerEmail": "owner@example.com",
    "password": "REPLACE_WITH_STRONG_PASSWORD"
  }'
```

Example response fields (save secrets locally; never commit them):

- `orgId` — organization id
- `token` — short-lived session JWT for the owner
- `mcpKey` — initial `lb_mcp_…` key (shown once)
- `refreshToken` — session refresh token

### 2. Rotate or issue a new MCP key (optional)

To mint a fresh MCP key with an owner/admin session JWT:

```bash
ORG_ID=org_REPLACE_ME
SESSION_JWT=REPLACE_WITH_TOKEN_FROM_SETUP

curl -sS -X POST "$ADMIN/org/v1/orgs/$ORG_ID/mcp-keys/rotate" \
  -H "Authorization: Bearer $SESSION_JWT" \
  -H 'Content-Type: application/json'
```

Response: `{ "mcpKey": "lb_mcp_…" }` (shown once).

### 3. Call hosted MCP through Studio

Point agents at your Studio origin. MCP is JSON-RPC over HTTP:

```bash
STUDIO=http://127.0.0.1:3005
MCP_KEY=lb_mcp_REPLACE_ME

curl -sS -X POST "$STUDIO/api/mcp" \
  -H "Authorization: Bearer $MCP_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "org_whoami",
      "arguments": {}
    }
  }'
```

Public device-flow tools (`auth_start`, `auth_poll`, `initialize`, `tools/list`) work without a Bearer token; all other tools require `Authorization: Bearer <lb_mcp_…>`.

### 4. Health checks

```bash
curl -sS "$ADMIN/health"
curl -sS "$STUDIO/api/mcp" -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## Environment reference (OSS compose)

| Variable | Purpose |
|----------|---------|
| `LIBREBASE_ADMIN_JWT_SECRET` | Signs console session JWTs (set in `.env`) |
| `LIBREBASE_KMS_SERVICE_ROLE` | Bearer token for Admin → KMS calls |
| `NEXT_PUBLIC_SITE_URL` | Public Studio URL (default `http://127.0.0.1:3005`) |
| `LIBREBASE_VERSION` | Passed into Studio build via `compose.env` |

## Upgrades

```bash
cd deploy/compose
docker compose --env-file compose.env pull   # when using published images
docker compose --env-file compose.env build  # when building from source
docker compose --env-file compose.env up -d
```

Admin data persists in the `librebase-admin-data` volume; KMS data in `librebase-kms-data`.
>>>>>>> 37362ea (fix(compose): LIB-168 LIB-169 LIB-170 OSS Docker self-host)
