import { NextResponse } from "next/server";
import { adminApiEnabled, adminBaseUrl } from "@/lib/librebase-admin-client";
import { extractMcpKey, handleMcpRpc, type JsonRpcRequest } from "@/lib/mcp-protocol";

export const dynamic = "force-dynamic";

const CORS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "Authorization, Content-Type, MCP-Protocol-Version, X-Librebase-Mcp-Key",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Max-Age": "86400",
};

function json(body: unknown, status = 200) {
  return NextResponse.json(body, { status, headers: CORS });
}

export async function OPTIONS() {
  return new NextResponse(null, { status: 204, headers: CORS });
}

export async function GET() {
  return json({
    name: "librebase",
    version: "0.2.0",
    transport: "streamable-http",
    protocolVersion: "2024-11-05",
  });
}

export async function POST(request: Request) {
  if (!adminApiEnabled()) {
    return json({ error: "Admin API disabled" }, 503);
  }
  const mcpKey = extractMcpKey(request);
  if (!mcpKey) {
    return json(
      {
        jsonrpc: "2.0",
        id: null,
        error: { code: -32001, message: "Missing MCP key. Set Authorization: Bearer lb_mcp_…" },
      },
      401,
    );
  }

  let msg: JsonRpcRequest;
  try {
    msg = (await request.json()) as JsonRpcRequest;
  } catch {
    return json(
      { jsonrpc: "2.0", id: null, error: { code: -32700, message: "parse error" } },
      400,
    );
  }

  const reply = await handleMcpRpc(msg, {
    adminUrl: adminBaseUrl(),
    mcpKey,
  });
  if (reply === null) {
    return new NextResponse(null, { status: 202, headers: CORS });
  }
  return json(reply);
}
