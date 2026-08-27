import { NextResponse } from "next/server";
import { SITE_URL } from "@/lib/site";

/**
 * MCP auto-discovery endpoint.
 *
 * When an agent hits /.well-known/mcp.json it gets the server config
 * so the user never has to hand-edit mcp.json — they just point the
 * agent at https://app.librebase.xyz and it self-configures.
 *
 * Spec: https://modelcontextprotocol.io/specification/2025-03-26/basic/authorization
 */
export async function GET() {
  const body = {
    schema_version: "1.0",
    name: "Librebase",
    description:
      "Open-source Postgres app platform. AI agents manage projects, instances, auth, and secrets through MCP.",
    url: SITE_URL,
    mcp: {
      servers: [
        {
          type: "mcp",
          url: `${SITE_URL}/api/mcp`,
          name: "Librebase MCP (hosted)",
        },
      ],
    },
    config: {
      mcpServers: {
        librebase: {
          command: "python3",
          args: ["-m", "librebase_mcp"],
          env: {
            LIBREBASE_ADMIN_URL: `${SITE_URL}/api/admin-proxy`,
            LIBREBASE_CONSOLE_URL: SITE_URL,
          },
        },
      },
    },
    docs: {
      setup: `${SITE_URL}/for-agents`,
      llms_txt: `${SITE_URL}/llms.txt`,
      authorize: `${SITE_URL}/mcp/authorize`,
    },
  };

  return NextResponse.json(body, {
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "public, max-age=3600",
      "Access-Control-Allow-Origin": "*",
    },
  });
}

export const runtime = "nodejs";
