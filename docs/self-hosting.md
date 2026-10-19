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

3. Edit `deploy/compose/.env`: set `NEXT_PUBLIC_SITE_URL` and `LIBREBASE_CONSOLE_URL` to the URL users will open (e.g. `https://studio.example.com` or `http://127.0.0.1:3005` for local-only). Set `LIBREBASE_VERSION` when upgrading (see **Upgrades**).

4. From `deploy/compose/`:

   ```bash
   docker compose up -d --build
   ```

5. **Agent-first onboarding (recommended):** call `POST /org/v1/setup` on the Admin API and use the returned `mcpKey` with Studio MCP — see **Headless onboarding** below.

6. **Browser alternative:** open Studio at your configured URL (compose publishes `127.0.0.1:3005` by default) and complete `/setup` once, then sign in at `/login`.

### Compose networking and exposure

The OSS stack runs **KMS, Admin, and Studio in one shared network namespace** (all attached to the `kms` service via `network_mode: service:kms`). Inside that namespace:

- Studio → Admin: `http://127.0.0.1:54330`
- Admin → KMS: `http://127.0.0.1:54340`

Admin and KMS bind `0.0.0.0` **inside the container netns** so processes in the same namespace can connect; they are **not** published on the Docker host by default.

**Host exposure (default):** only Studio is mapped — `127.0.0.1:3005:3005` on the `kms` service (the netns owner). Admin (`54330`) and KMS (`54340`) have **no** host port mapping. Do not add bare `54330:54330`, `0.0.0.0:54330`, or public binds for Admin/KMS unless you fully understand the risk.

To reach the public internet, put a **reverse proxy** in front of Studio (`127.0.0.1:3005`) — see **Reverse proxy** below. Never expose Admin or KMS on `0.0.0.0`.

- Do **not** set `LIBREBASE_ADMIN_BIND=127.0.0.1` in `.env` unless you know you need it; compose sets `LIBREBASE_ADMIN_BIND=0.0.0.0` on the admin process (in-netns only).

## Services and ports

| Service | Compose service | Host bind (default) | Role |
|---------|-----------------|---------------------|------|
| Studio | `studio` | `127.0.0.1:3005` | Next.js console; MCP at `/api/mcp` |
| Admin API | `librebase-admin` | (not published) | Orgs, projects, instances metadata, MCP keys, auth |
| KMS | `kms` | (not published) | Seals project secrets; owns the shared netns |

Volumes `librebase-admin-data` and `librebase-kms-data` hold SQLite databases. Back them up before upgrades.

## Required environment variables

See [`deploy/compose/.env.example`](../deploy/compose/.env.example) for the full list with placeholders.

| Variable | Required | Notes |
|----------|----------|--------|
| `LIBREBASE_ADMIN_JWT_SECRET` | yes | Signs session JWTs for Admin API |
| `LIBREBASE_KMS_SERVICE_ROLE` | yes | Bearer token Studio/Admin use to call KMS |
| `NEXT_PUBLIC_SITE_URL` | yes (build) | Public origin for Studio (OAuth redirects, MCP discovery) |
| `LIBREBASE_CONSOLE_URL` | recommended | Admin API email/links; should match Studio origin |
| `LIBREBASE_VERSION` | yes (build) | Set in `deploy/compose/.env` for image build args |

Optional (only if you enable those features):

- `LIBREBASE_GOOGLE_CLIENT_ID` / `LIBREBASE_GOOGLE_CLIENT_SECRET` — Google sign-in
- `LIBREBASE_GITHUB_CLIENT_ID` / `LIBREBASE_GITHUB_CLIENT_SECRET` — GitHub sign-in
- `LIBREBASE_RUNTIME=local` — default local lidb/dev runtime from Studio (`LIBREBASE_HARNESS=oss` for Kubernetes/licontainer on your infra)

Do **not** commit real secrets. `.env` is gitignored; use `.env.example` as the template only.

## Headless onboarding (API + MCP)

Primary path for agents and automation. Placeholders below — replace with your values; never commit real secrets.

### 1. First-run setup

`POST /org/v1/setup` is allowed only while the database has no organization. Admin is not on the host loopback — run setup **inside** the stack (from `deploy/compose/`):

```bash
docker compose exec -T librebase-admin python3 -c "
import json, urllib.request
body = json.dumps({
    'name': 'My Org',
    'ownerEmail': 'owner@example.com',
    'password': 'REPLACE_WITH_STRONG_PASSWORD',
}).encode()
req = urllib.request.Request(
    'http://127.0.0.1:54330/org/v1/setup',
    data=body,
    method='POST',
    headers={'Content-Type': 'application/json'},
)
print(urllib.request.urlopen(req, timeout=10).read().decode())
"
```

Example response fields (save locally):

- `orgId` — organization id
- `token` — short-lived session JWT for the owner
- `mcpKey` — initial `lb_mcp_…` key (shown once)
- `refreshToken` — session refresh token

### 2. Rotate or issue a new MCP key (optional)

```bash
docker compose exec -T librebase-admin python3 -c "
import json, os, urllib.request
org_id = 'org_REPLACE_ME'
token = 'REPLACE_WITH_TOKEN_FROM_SETUP'
body = json.dumps({}).encode()
req = urllib.request.Request(
    f'http://127.0.0.1:54330/org/v1/orgs/{org_id}/mcp-keys/rotate',
    data=body,
    method='POST',
    headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {token}'},
)
print(urllib.request.urlopen(req, timeout=10).read().decode())
"
```

Response: `{ "mcpKey": "lb_mcp_…" }` (shown once).

### 3. Call hosted MCP through Studio

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
docker compose exec -T librebase-admin wget -qO- http://127.0.0.1:54330/health
curl -sS "http://127.0.0.1:3005/api/mcp" -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## First run checklist

1. `docker compose ps` — KMS and `librebase-admin` healthy.
2. Complete **headless onboarding** (above) or browser `/setup` once.
3. Authenticated MCP `org_whoami` via `POST /api/mcp` succeeds.
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
2. Bump `LIBREBASE_VERSION` in `deploy/compose/.env` after pulling the new release. `scripts/sync-version.py` updates `deploy/compose/compose.env` as a repo reference — copy that value into `.env` when upgrading.
3. From `deploy/compose/`: `docker compose up -d --build`.
4. Verify Admin health inside the stack (`docker compose exec librebase-admin wget -qO- http://127.0.0.1:54330/health`) and sign-in to Studio.

## Reverse proxy (recommended for production)

The compose file publishes only Studio on `127.0.0.1:3005`. Terminate TLS on the host (e.g. `deploy/nginx-librebase.xyz.conf` as a reference) and proxy to that address. Do not map Admin (`54330`) or KMS (`54340`) to the host or to `0.0.0.0`.

## MCP and agents on self-host

Point agents at your Studio origin:

- Discovery: `GET {SITE_URL}/.well-known/mcp.json`
- Endpoint: `POST {SITE_URL}/api/mcp`
- Stdio bridge env: `LIBREBASE_MCP_URL`, `LIBREBASE_MCP_TOKEN` — see [mcp/README.md](../mcp/README.md).
- Headless install and `lb_mcp_…` keys: **Headless onboarding** above.

**Migration:** older installs may still set `LIBREBASE_MCP_KEY`. The stdio bridges accept it as a deprecated alias (`LIBREBASE_MCP_TOKEN` wins if both are set). Rename to `LIBREBASE_MCP_TOKEN` when you next rotate credentials.

## Related docs

- [admin-api/README.md](../admin-api/README.md) — API auth and env reference
- [kms/README.md](../kms/README.md) — KMS service
- [architecture-instances.md](architecture-instances.md) — dedicated vs shared instances
- [cli-db.md](cli-db.md) — local lidb / `lis` workflows
