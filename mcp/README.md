# librebase-mcp (Python stdio bridge)

Stdio MCP **bridge** to hosted Librebase MCP — same contract as `packages/mcp` on Node.

- **URL:** `LIBREBASE_MCP_URL` (default `https://app.librebase.xyz/api/mcp`)
- **Auth:** `auth_start` / `auth_poll` on the hosted server, or `LIBREBASE_MCP_TOKEN` (`lb_mcp_*` / `lb_agt_*`). `LIBREBASE_MCP_KEY` is a deprecated alias.

> Packaging: `pip install librebase-mcp` / `uvx librebase-mcp` (prep — not published yet, LIB-150). Until then, run from a **Librebase repo checkout** (`python3 -m librebase_mcp`).

## Local checkout (recommended today)

```bash
cd /path/to/librebase
LIBREBASE_MCP_URL=https://app.librebase.xyz/api/mcp \
  PYTHONPATH=mcp python3 -m librebase_mcp
```

## Cursor (repo checkout)

```json
{
  "mcpServers": {
    "librebase": {
      "command": "python3",
      "args": ["-m", "librebase_mcp"],
      "cwd": "/path/to/librebase/mcp",
      "env": {
        "PYTHONPATH": "/path/to/librebase/mcp",
        "LIBREBASE_MCP_URL": "https://app.librebase.xyz/api/mcp"
      }
    }
  }
}
```

With token:

```json
{
  "mcpServers": {
    "librebase": {
      "command": "python3",
      "args": ["-m", "librebase_mcp"],
      "cwd": "/path/to/librebase/mcp",
      "env": {
        "PYTHONPATH": "/path/to/librebase/mcp",
        "LIBREBASE_MCP_URL": "https://app.librebase.xyz/api/mcp",
        "LIBREBASE_MCP_TOKEN": "lb_mcp_…"
      }
    }
  }
}
```

## VS Code (repo checkout)

```json
{
  "servers": {
    "librebase": {
      "type": "stdio",
      "command": "python3",
      "args": ["-m", "librebase_mcp"],
      "cwd": "/path/to/librebase/mcp",
      "env": {
        "PYTHONPATH": "/path/to/librebase/mcp"
      }
    }
  }
}
```

## MCP token (optional)

Console keys work as `LIBREBASE_MCP_TOKEN` for stdio when you skip device flow. Issue in Studio: `/admin` → **MCP key** → **Generate new key**, or `POST /org/v1/orgs/{orgId}/mcp-keys/rotate` with an admin session JWT. Never commit tokens.

Production agents can also use hosted OAuth MCP directly (`docs/mcp/AUDIT.md`).

## Claude Desktop (repo checkout)

```json
{
  "mcpServers": {
    "librebase": {
      "command": "python3",
      "args": ["-m", "librebase_mcp"],
      "cwd": "/path/to/librebase/mcp",
      "env": {
        "PYTHONPATH": "/path/to/librebase/mcp"
      }
    }
  }
}
```

## After PyPI publish (future)

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

## Test

```bash
pip install -e mcp
python3 -m unittest discover -s mcp/tests -v
```
