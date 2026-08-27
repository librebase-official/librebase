# Librebase MCP server

Stdio MCP server that lets AI tools (Cursor, Claude, etc.) maintain a
Librebase org's **users, instances, and projects** through the admin API.

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
