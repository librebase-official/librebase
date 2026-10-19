# Librebase MCP server (Python stdio)

Stdio MCP server for **local / air-gapped** use with a console MCP key.

**Production agents** should use **hosted** Streamable HTTP MCP at `{SITE}/api/mcp`
(see `docs/mcp/AUDIT.md` and `GET /.well-known/mcp.json`). The hosted server exposes
**22 tools** (device auth + KMS keys); this Python package implements the **11** org/project/instance tools only.

## Setup

```json
{
  "mcpServers": {
    "librebase": {
      "command": "python3",
      "args": ["-m", "librebase_mcp"],
      "cwd": "/path/to/librebase/mcp",
      "env": {
        "PYTHONPATH": "/path/to/librebase/mcp",
        "LIBREBASE_ADMIN_URL": "https://app.librebase.xyz/api/admin-proxy",
        "LIBREBASE_MCP_KEY": "lb_mcp_..."
      }
    }
  }
}
```

`LIBREBASE_ADMIN_URL` is the admin API base URL. `LIBREBASE_MCP_KEY` is the
MCP key generated in the console (`/admin`); it scopes every call to one org.

## MCP key (issue / rotate)

Console keys are for **CI and local stdio** (`python3 -m librebase_mcp`). Production
agents should use hosted OAuth MCP (`docs/mcp/AUDIT.md`).

| Method | Who | Action |
| --- | --- | --- |
| **Studio UI** | Org **admin** or **owner** | Sign in → `/admin` → **MCP key** → **Generate new key**. Copy once; prior active keys are revoked. |
| **Admin API** | Session JWT with **admin** role on the org | `POST /org/v1/orgs/{orgId}/mcp-keys/rotate` → `{ "mcpKey": "lb_mcp_…" }` |
| **Bootstrap** | First-time setup | `POST /org/v1/setup` returns an initial `mcpKey` for the new org (one-time in the response). |

Set `LIBREBASE_MCP_KEY` to the plaintext value (starts with `lb_mcp_`, ~50 characters).
Never commit keys to git — use env vars or your secret store.

`GET /org/v1/mcp/org` with `Authorization: Bearer <mcpKey>` resolves the org for stdio startup.

## Tools

- `org_whoami` — resolve the key's org
- `project_list` / `project_create`
- `auth_provider_list` / `auth_provider_upsert` — OAuth sign-in (github/google) per project; client secret is KMS-sealed, never returned
- `instance_list` / `instance_get` / `instance_create` / `instance_launch` / `instance_stop`
- `member_list` / `member_invite` / `member_update_role`
- `host_list` / `host_create`

## Test locally

```bash
cd mcp
LIBREBASE_ADMIN_URL=https://... LIBREBASE_MCP_KEY=lb_mcp_... \
  python3 -m librebase_mcp < <(printf '%s\n' \
    '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
    '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
    '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"org_whoami","arguments":{}}}')
```
