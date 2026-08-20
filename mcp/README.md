# Librebase MCP server

Lets Cursor, Claude, Grok, and klautcode see your org and project.

SaaS path: copy the snippet from the project **Connect an agent** panel.
That is a remote URL — no Python, no `PYTHONPATH`, no local checkout.

```json
{
  "mcpServers": {
    "librebase": {
      "url": "https://app.librebase.xyz/mcp",
      "headers": {
        "Authorization": "Bearer lb_mcp_..."
      }
    }
  }
}
```

Claude Code:

```bash
claude mcp add --transport http librebase https://app.librebase.xyz/mcp \
  --header "Authorization: Bearer lb_mcp_..."
```

## Tools

- `org_whoami` — resolve the key's org
- `project_list` / `project_get` / `project_create`
- `instance_list` / `instance_get` / `instance_create` / `instance_launch` / `instance_stop`
- `member_list` / `member_invite` / `member_update_role`
- `host_list` / `host_create`

## Local stdio (open-source / air-gapped)

```json
{
  "mcpServers": {
    "librebase": {
      "command": "python3",
      "args": ["-m", "librebase_mcp"],
      "cwd": "/path/to/librebase/mcp",
      "env": {
        "PYTHONPATH": "/path/to/librebase/mcp",
        "LIBREBASE_ADMIN_URL": "http://127.0.0.1:54330",
        "LIBREBASE_MCP_KEY": "lb_mcp_..."
      }
    }
  }
}
```
