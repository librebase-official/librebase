# librebase-mcp (Python stdio bridge)

Stdio MCP **bridge** to hosted Librebase MCP — same contract as `@librebase/mcp` on npm.

- **URL:** `LIBREBASE_MCP_URL` (default `https://app.librebase.xyz/api/mcp`)
- **Auth:** `auth_start` / `auth_poll` on the hosted server, or `LIBREBASE_MCP_TOKEN` (`lb_mcp_*` / `lb_agt_*`). `LIBREBASE_MCP_KEY` is a deprecated alias.

> Packaging: `pip install librebase-mcp` / `uvx librebase-mcp` (prep — not published yet, LIB-150).

## Cursor

```json
{
  "mcpServers": {
    "librebase": {
      "command": "uvx",
      "args": ["librebase-mcp"]
    }
  }
}
```

With token:

```json
{
  "mcpServers": {
    "librebase": {
      "command": "uvx",
      "args": ["librebase-mcp"],
      "env": {
        "LIBREBASE_MCP_TOKEN": "lb_mcp_…"
      }
    }
  }
}
```

## VS Code

```json
{
  "servers": {
    "librebase": {
      "type": "stdio",
      "command": "uvx",
      "args": ["librebase-mcp"]
    }
  }
}
```

## MCP token (optional)

Console keys work as `LIBREBASE_MCP_TOKEN` for stdio when you skip device flow. Issue in Studio: `/admin` → **MCP key** → **Generate new key**, or `POST /org/v1/orgs/{orgId}/mcp-keys/rotate` with an admin session JWT. Never commit tokens.

Production agents can also use hosted OAuth MCP directly (`docs/mcp/AUDIT.md`).

## Claude Desktop

```json
{
  "mcpServers": {
    "librebase": {
      "command": "uvx",
      "args": ["librebase-mcp"]
    }
  }
}
```

## Local checkout

```bash
cd mcp
LIBREBASE_MCP_URL=https://app.librebase.xyz/api/mcp \
  python3 -m librebase_mcp
```

## Test

```bash
pip install -e mcp
python3 -m unittest discover -s mcp/tests -v
```
