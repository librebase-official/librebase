import { NextResponse } from "next/server";
import { SITE_URL } from "@/lib/site";

export async function GET() {
  const body = {
    schema_version: "1.0",
    name: "Librebase",
    description:
      "Open-source Postgres app platform for AI agents via hosted MCP.",
    url: SITE_URL,
    mcp: {
      transport: "streamable-http",
      url: `${SITE_URL}/api/mcp`,
      authorization_server: `${SITE_URL}/.well-known/oauth-authorization-server`,
      name: "Librebase MCP (hosted)",
    },
    config: {
      mcpServers: {
        librebase: {
          type: "http",
          url: `${SITE_URL}/api/mcp`,
        },
      },
    },
    fallback: {
      type: "stdio",
      command: "python3",
      args: ["-m", "librebase_mcp"],
      env: {
        LIBREBASE_ADMIN_URL: `${SITE_URL}/api/admin-proxy`,
        LIBREBASE_CONSOLE_URL: SITE_URL,
        LIBREBASE_MCP_KEY: "CI-only-static-key",
      },
    },
    docs: {
      setup: `${SITE_URL}/for-agents`,
      llms_txt: `${SITE_URL}/llms.txt`,
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
