# Librebase MCP audit (2026-10-18)

## Surfaces (three different servers)

| Surface | Transport | Audience | Tool count (approx.) |
| --- | --- | --- | --- |
| **Hosted** `data-studio-ui/app/api/mcp/route.ts` | Streamable HTTP `POST /api/mcp` | Production agents (Cursor remote MCP) | **22** |
| **Python stdio** `mcp/librebase_mcp/__main__.py` | `python3 -m librebase_mcp` | Local / air-gapped with `LIBREBASE_MCP_KEY` | **11** |
| **Node dev harness** `packages/mcp/src/server.js` | stdio | Local dev, parity matrix, Supabase-shaped stubs | **30+** (different names) |

**Canonical product API for agents:** hosted HTTP at `{SITE_URL}/api/mcp`, discovered via `GET /.well-known/mcp.json`.

The Node package is a **developer harness**, not the same contract as production. Do not point user-facing docs at `packages/mcp` paths on a contributor machine.

## Hosted tool catalog (source of truth)

Org / projects / runtime:

- `org_whoami`, `project_list`, `project_create`
- `auth_provider_list`, `auth_provider_upsert`
- `instance_list`, `instance_get`, `instance_create`, `instance_launch`, `instance_stop`
- `member_list`, `member_invite`, `member_update_role`
- `host_list`, `host_create`

Device flow (no MCP key on `tools/list` / `auth_start` / `auth_poll`):

- `auth_start`, `auth_poll` → browser approval at `/mcp/authorize`

KMS secrets (org-scoped key; values must not be echoed to the model):

- `key_list`, `key_create`, `key_get`, `key_decrypt`, `key_rotate`, `key_update`, `key_delete`

**Not implemented on hosted MCP today:** `migration_apply`, `sql_execute`, `table_list`, `migration_list` (these appeared in marketing/handoff copy but are not in `route.ts`).

## Python stdio gap

Python mirrors the **first 11** hosted tools only. It does **not** implement device auth or KMS key tools. After org bootstrap via console key, stdio is enough for instances/projects/members/hosts; agents needing browser login or secrets should use **hosted** MCP.

## Auth & security (hosted)

- Protected calls: `Authorization: Bearer lb_mcp_*` or `lb_agt_*`.
- Public without key: `initialize`, `notifications/initialized`, `tools/list`, `tools/call` for `auth_start` / `auth_poll`.
- Rate limit: 30 req/min per IP (in-memory).
- Usage logged to admin API `POST /org/v1/mcp/usage` (best-effort).
- Requires **Admin API enabled**; otherwise `503 { "error": "Admin API disabled" }` (local Studio default without admin).

## Discovery & docs

- `GET /.well-known/mcp.json` — public, CORS `*`, points at hosted URL and `llms.txt`.
- `GET /api/mcp` — server metadata when admin enabled.
- `GET /for-agents`, `GET /llms.txt` — human/agent onboarding.

## Cursor / Cloud Agent wiring

Repo `.cursor/mcp.json` points at production with a placeholder bearer. Cursor MCP discovery **fails** until a real `lb_mcp_…` key is set (or OAuth device flow is used per agent client). In this cloud run, the `librebase` MCP namespace reports **tool discovery error** for that reason.

**Recommended Cursor config (hosted, no pasted key):**

```json
{
  "mcpServers": {
    "librebase": {
      "url": "https://app.librebase.xyz/api/mcp",
      "auth": {
        "authorization_server": "https://app.librebase.xyz/.well-known/oauth-authorization-server",
        "scopes": ["mcp"]
      }
    }
  }
}
```

Cursor opens a browser card; you **Continue with Google** (or GitHub) on `/mcp/authorize` and approve. The resulting `lb_agt_*` token is stored by Cursor — not typed into settings.

`LIBREBASE_MCP_KEY` / console keys remain for **CI and local stdio only**.

### Issuing or rotating a console MCP key

1. **Studio (recommended):** org admin → `/admin` → **MCP key** → **Generate new key** (revokes the previous active key).
2. **API:** `POST /org/v1/orgs/{orgId}/mcp-keys/rotate` with `Authorization: Bearer <session JWT>` (caller must have admin role on that org). Response: `{ "mcpKey": "lb_mcp_…" }` (shown once).
3. **New org:** `POST /org/v1/setup` includes an initial `mcpKey` in the JSON body.

Store the key in `LIBREBASE_MCP_KEY` (or Cursor env for stdio). Do not commit keys to the repo.

## Branding / UX

- `/mcp/authorize` uses auth shell; should show bird wordmark (same as login).
- `/for-agents` updated to list real hosted tools only.

## Recommended follow-ups

1. **Parity:** Port `auth_*` + `key_*` to Python stdio, or generate tool defs from one shared manifest.
2. **SQL/migrations:** Either implement `migration_apply` / `sql_execute` on hosted MCP or remove from all handoff/marketing strings.
3. **CI:** Smoke test `tools/list` against route when admin fixture is up.
4. **Rename/clarify** `packages/mcp` README as “dev harness” to avoid confusion with `mcp/librebase_mcp`.
