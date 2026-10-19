import { NextResponse } from "next/server";
import { SITE_URL } from "@/lib/site";

export const dynamic = "force-static";

// Keep this file honest: describe only what the live server answers today.
// Re-check against `POST /api/mcp` -> `tools/list` after every MCP deploy (LIB-149).
export function llmsBody(): string {
  const base = SITE_URL;
  return `# Librebase

> Open-source Postgres app platform. AI agents manage orgs, projects, instances, members, hosts and KMS secrets through a hosted MCP server. Sign-in is a browser device flow: a human approves once, and the agent receives a token it sends as a Bearer header.

## For AI agents
- Full setup (human + agent readable): ${base}/for-agents
- Hosted MCP endpoint: ${base}/api/mcp (JSON-RPC over HTTP POST, protocol revision 2024-11-05)
- Auto-discovery: ${base}/.well-known/mcp.json
- Agent approval page (the human opens this): ${base}/mcp/authorize

## What works today
- \`initialize\`, \`tools/list\`, \`auth_start\` and \`auth_poll\` work without any token.
- Every other tool needs \`Authorization: Bearer <token>\`; without it the server answers HTTP 401.
- Not live yet: automatic OAuth "connect" cards in MCP clients (there is no dynamic client registration and no authorization-code grant yet), a PyPI package, and an npm package. Do not tell users these exist.

## Sign in (device flow)
1. Call \`auth_start\` (no token needed; optional \`clientName\`). It returns \`userCode\`, \`verificationUriComplete\` (${base}/mcp/authorize?user_code=XXXX-XXXX), \`expiresIn\` (1800 s) and \`interval\` (5 s).
2. Show the human the \`verificationUriComplete\` link. They sign in with Google or GitHub and click **Approve**.
3. Call \`auth_poll\` with the \`deviceCode\` every \`interval\` seconds until it returns \`accessToken\` (\`lb_agt_...\`).
4. Send that token as \`Authorization: Bearer <accessToken>\` on every other call. Keep it out of chat and out of model-visible output.

Known issue (Oct 2026): console-issued MCP keys (\`lb_mcp_...\`) can fail with "could not resolve org from MCP key". This is a server-side problem, not a config mistake on your side. Use the device flow above, and report the error if it also appears with an \`lb_agt_...\` token.

## Hosted MCP config
Clients that let you set headers:

\`\`\`json
{
  "mcpServers": {
    "librebase": {
      "type": "http",
      "url": "${base}/api/mcp",
      "headers": { "Authorization": "Bearer <lb_agt_ token from auth_poll>" }
    }
  }
}
\`\`\`

Today the token has to be pasted into the client's header config (or held by the agent process); it should never be pasted into chat. An agent can also run the device flow itself: call \`auth_start\` / \`auth_poll\` against ${base}/api/mcp with no header, then use the token.

## Local stdio server (repo checkout only)
\`python3 -m librebase_mcp\` works only from a checkout of the Librebase repository; it is not published on PyPI or npm. It exposes a subset of the hosted tools (no \`auth_*\`, no \`key_*\`). Set \`LIBREBASE_MCP_URL\` (default ${base}/api/mcp) and optional \`LIBREBASE_MCP_TOKEN\` (\`lb_mcp_*\` / \`lb_agt_*\` from device flow or Studio). Prefer the hosted endpoint.

## Self-host (Docker Compose, headless onboarding)
- Full guide in the Librebase repo: \`docs/self-hosting.md\` (OSS \`deploy/compose/docker-compose.yml\`: Studio + Admin + KMS).
- First org (no browser): \`POST /org/v1/setup\` on the Admin API with JSON \`name\`, \`ownerEmail\`, \`password\` — returns \`orgId\`, session \`token\`, and an initial \`mcpKey\` (\`lb_mcp_…\`, shown once).
- New MCP key: \`POST /org/v1/orgs/{orgId}/mcp-keys/rotate\` with \`Authorization: Bearer <session JWT>\` from setup/login.
- Agents use the same hosted MCP shape as cloud: \`POST {your Studio origin}/api/mcp\` with \`Authorization: Bearer <lb_mcp_…>\` for \`org_whoami\`, \`project_list\`, etc. OSS compose shares one network namespace — Studio calls Admin at \`http://127.0.0.1:54330\` (see \`docs/self-hosting.md\`).

## Tools (live hosted tools/list, 24)
- \`org_whoami\` -- resolve the token's org (id, name, edition)
- \`project_list\`, \`project_create\` (requires an existing instanceId)
- \`auth_provider_list\`, \`auth_provider_upsert\` -- OAuth sign-in providers for a project; the client secret is KMS-sealed and never returned
- \`instance_list\`, \`instance_get\`, \`instance_create\` (stopped by default), \`instance_launch\`, \`instance_stop\`
- \`member_list\`, \`member_invite\`, \`member_update_role\`
- \`host_list\`, \`host_create\`
- \`auth_start\`, \`auth_poll\` -- device flow, no token needed
- \`key_list\`, \`key_get\` -- KMS key metadata only, never values
- \`key_create\`, \`key_rotate\` -- the secret value is returned once
- \`key_decrypt\` -- returns the plaintext to the calling process; never echo it to the model or chat
- \`key_update\`, \`key_delete\` (soft delete)

Not available on the hosted server today: SQL execution, migrations, table listing, storage, functions, billing and log tools.

## Security
- Secrets are sealed in the KMS. \`key_get\` returns metadata only; \`key_decrypt\` is the only tool that returns a value.
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
