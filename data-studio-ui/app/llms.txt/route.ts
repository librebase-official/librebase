import { NextResponse } from "next/server";
import { SITE_URL } from "@/lib/site";

export const dynamic = "force-static";

function llmsBody(): string {
  const base = SITE_URL;
  return `# Librebase

> Open-source Postgres app platform. AI agents manage projects, instances, auth, and secrets through a local MCP server — the user authenticates once in their browser (no API keys pasted).

## For AI agents
Librebase ships an MCP (Model Context Protocol) server. Add it to your agent, then call \`auth_login\`: the user's browser opens for a one-click **Approve**. The resulting token is stored in the OS keychain and is **never shown to the model**.

- Full setup (human + agent readable): ${base}/for-agents
- Console origin: ${base}
- Public admin ingress (the MCP talks to this): ${base}/api/admin-proxy
- Agent approval page: ${base}/mcp/authorize

## MCP server config
Add to your agent's MCP config. The server is the \`mcp/\` directory of the Librebase repo (run it from there).

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

## Auth (device flow)
1. Call \`auth_status\`. If unauthenticated, call \`auth_login\`.
2. The user's browser opens ${base}/mcp/authorize?user_code=XXXX-XXXX.
3. The user signs in (if needed) and clicks **Approve**. The MCP stores the
   user-bound token in the keychain; it is never returned to the model.

## Tools
- \`auth_status\` / \`auth_login\` / \`auth_logout\` — browser login + keychain
- \`org_whoami\`, \`project_list\`, \`project_create\`, \`project_delete\`
- \`key_list\` / \`key_create\` / \`key_get\` — secrets; the value is redacted from the model and stored locally
- \`auth_provider_list\` / \`auth_provider_upsert\` — OAuth (github/google); client secret is KMS-sealed, never returned
- \`migration_apply\` / \`migration_list\` / \`sql_execute\` / \`table_list\`
- \`instance_list\` / \`instance_create\` / \`instance_launch\` / \`instance_stop\`
- \`member_list\` / \`member_invite\` / \`member_update_role\`

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