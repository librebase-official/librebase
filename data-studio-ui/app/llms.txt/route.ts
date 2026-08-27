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
Point your agent at the hosted endpoint. Just add your MCP key:

\`\`\`json
{
  "mcpServers": {
    "librebase": {
      "type": "mcp",
      "url": "${base}/api/mcp",
      "headers": {
        "Authorization": "Bearer <your-mcp-key>"
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

## Auth (device flow -- self-signup)
No pre-shared key needed. The agent calls \`auth_start\` to initiate browser login; the user approves in their browser; the agent stores the token.

1. Call \`auth_start\` -- returns a user_code + verification URL.
2. The user opens the URL, signs in, and clicks Approve.
3. Call \`auth_poll\` until approved -- returns a session token.
4. The agent stores the token; it is never shown to the model.

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
- Never set \`LIBREBASE_MCP_KEY\` for interactive use (CI override only).
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
