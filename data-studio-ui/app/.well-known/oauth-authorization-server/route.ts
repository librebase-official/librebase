import { NextResponse } from "next/server";
import { SITE_URL } from "@/lib/site";

export function GET() {
  return NextResponse.json(
    {
      issuer: SITE_URL,
      authorization_endpoint: `${SITE_URL}/mcp/authorize`,
      token_endpoint: `${SITE_URL}/api/mcp/device/token`,
      scopes_supported: ["mcp"],
      response_types_supported: ["code"],
      grant_types_supported: ["urn:ietf:params:oauth:grant-type:device_code"],
      code_challenge_methods_supported: ["S256"],
    },
    {
      headers: {
        "Cache-Control": "public, max-age=3600",
        "Access-Control-Allow-Origin": "*",
      },
    },
  );
}

export const runtime = "nodejs";
