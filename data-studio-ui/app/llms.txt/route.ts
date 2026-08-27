import { NextResponse } from "next/server";
import { SITE_URL } from "@/lib/site";

export const dynamic = "force-static";

function llmsBody(): string {
  const base = SITE_URL;
  return `# Librebase

> Open-source Postgres app platform. AI agents manage projects, instances, auth, and secrets through MCP -- the user authenticates once in their browser (no API keys pasted).

## For AI agents
Librebase ships an MCP (Model Context Protocol) server. Add it to your agent, then call \`auth_start\`: the user's browser opens for a one-click **Approve**. The resulting token is stored in the OS keychain and is **never shown to the model**.

- Full setup (human + agent readable): ${base}/for-agents
- Console origin: ${base}
- Hosted MCP endpoint (no install needed): ${base}/api/mcp
- Auto-discovery: ${base}/.well-known/mcp.json
- Public admin ingress (local MCP talks to this): ${base}/api/admin-proxy
- Agent approval page: ${base}/mcp/authorize

## Hosted MCP (recommended -- no install)
Point your remote MCP-capable agent at the hosted endpoint. It should discover the OAuth authorization server and show a browser connect card; do not paste a key into chat:

\`\`\`json
{
  "mcpServers": {
    "librebase": {
      "type": "mcp",
      "url": "${base}/api/mcp",
      "auth": {
        "authorization_server": "${base}/.well-known/oauth-authorization-server",
        "scopes": ["mcp"]
      }
    }
  }
}
\`\`\`

Or use auto-discovery: GET ${base}/.well-known/mcp.json returns the full config.

## Local MCP (alternative -- no network dependency)
The server is also available as a Python package. Add to your agent's MCP config:

\`\`\`json
{
  "mcpServers": {
    "librebase": {
      "command": "python3",
      "args": ["-m", "librebase_mcp"],
      "env": {
        "LIBREBASE_ADMIN_URL": "${base}/api/admin-proxy",
        "LIBREBASE_CONSOLE_URL": "${base}"
      }
    }
  }
}
\`\`\`

## Auth (remote OAuth/device flow -- self-signup)
No pre-shared key is needed for interactive use. Remote MCP clients should use the OAuth metadata endpoint to open a browser connect card. Clients without OAuth support may call auth_start without a key, then auth_poll after the user approves.

1. Call \`auth_start\` -- returns a user_code + verification URL.
2. The user opens the URL, signs in, and clicks Approve.
3. Call \`auth_poll\` until approved -- returns a session token.
4. The connector stores the token; it is never shown to the model.

## Tools
- \`auth_start\` / \`auth_poll\` -- browser login + device flow (self-signup)
- \`org_whoami\`, \`project_list\`, \`project_create\`
- \`auth_provider_list\` / \`auth_provider_upsert\` -- OAuth (github/google/grok); client secret is KMS-sealed, never returned
- \`instance_list\` / \`instance_create\` / \`instance_launch\` / \`instance_stop\`
- \`member_list\` / \`member_invite\` / \`member_update_role\`
- \`host_list\` / \`host_create\`

## Security
- Secrets are sealed in the KMS. \`key_get\` hands the value to the process only and redacts it in model output.
- Every decrypt/sign is audited. Agent tokens are revocable instantly.
- LIBREBASE_MCP_KEY is for local stdio/CI only; never request or paste it for interactive hosted use.
`;
}

export function GET() {
  return new NextResponse(llmsBody(), {
    headers: {
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
    },
  });
}
