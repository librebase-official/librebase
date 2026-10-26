# @librebase/mcp

Stdio **bridge** to the hosted Librebase MCP server. Tool definitions always come from the live hosted `tools/list` — one surface for production and local agents.

- **URL:** `LIBREBASE_MCP_URL` (default `https://app.librebase.xyz/api/mcp`)
- **Auth:** device flow via hosted `auth_start` / `auth_poll`, or `LIBREBASE_MCP_TOKEN` (`lb_mcp_*` / `lb_agt_*`). Tokens are never logged.

Local Admin/parity tooling lives in **`@librebase/mcp-dev-harness`** (private, not published).

> **Packaging:** `@librebase/mcp` is not on npm yet. Use a **Librebase repo checkout** (paths below). `npx -y @librebase/mcp` will work after the first npm publish (LIB-150).

## Local (from a repo checkout)

```bash
cd packages/mcp
npm install
node src/server.js
```

## Cursor

`~/.cursor/mcp.json` or project `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "librebase": {
      "command": "node",
      "args": ["/path/to/librebase/packages/mcp/src/server.js"],
      "env": {
        "LIBREBASE_MCP_URL": "https://app.librebase.xyz/api/mcp"
      }
    }
  }
}
```

Optional token (skip browser device flow):

```json
{
  "mcpServers": {
    "librebase": {
      "command": "node",
      "args": ["/path/to/librebase/packages/mcp/src/server.js"],
      "env": {
        "LIBREBASE_MCP_URL": "https://app.librebase.xyz/api/mcp",
        "LIBREBASE_MCP_TOKEN": "lb_mcp_…"
      }
    }
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
      "command": "node",
      "args": ["/path/to/librebase/packages/mcp/src/server.js"]
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
      "command": "node",
      "args": ["/path/to/librebase/packages/mcp/src/server.js"]
    }
  }
}
```

## After npm publish (future)

```bash
npx -y @librebase/mcp
```

## Develop

```bash
cd packages/mcp
npm install
npm test
node src/server.js
```
