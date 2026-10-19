# @librebase/mcp

Stdio **bridge** to the hosted Librebase MCP server. Tool definitions always come from the live hosted `tools/list` — one surface for production and local agents.

- **URL:** `LIBREBASE_MCP_URL` (default `https://app.librebase.xyz/api/mcp`)
- **Auth:** device flow via hosted `auth_start` / `auth_poll`, or `LIBREBASE_MCP_TOKEN` (`lb_mcp_*` / `lb_agt_*`). Tokens are never logged.

Local Admin/parity tooling lives in **`@librebase/mcp-dev-harness`** (private, not published).

## Install

```bash
npx -y @librebase/mcp
```

## Cursor

`~/.cursor/mcp.json` or project `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "librebase": {
      "command": "npx",
      "args": ["-y", "@librebase/mcp"]
    }
  }
}
```

Optional token (skip browser device flow):

```json
{
  "mcpServers": {
    "librebase": {
      "command": "npx",
      "args": ["-y", "@librebase/mcp"],
      "env": {
        "LIBREBASE_MCP_TOKEN": "lb_mcp_…"
      }
    }
  }
}
```

Custom endpoint:

```json
{
  "env": {
    "LIBREBASE_MCP_URL": "https://app.librebase.xyz/api/mcp"
  }
}
```

## VS Code (Copilot MCP)

`.vscode/mcp.json`:

```json
{
  "servers": {
    "librebase": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@librebase/mcp"]
    }
  }
}
```

## Claude Desktop

`claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "librebase": {
      "command": "npx",
      "args": ["-y", "@librebase/mcp"]
    }
  }
}
```

## Develop

```bash
cd packages/mcp
npm install
npm test
node src/server.js
```
