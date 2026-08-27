/**
 * Hosted MCP endpoint — Streamable HTTP transport.
 *
 * Agents POST JSON-RPC messages here (with an MCP key in Authorization)
 * instead of running `python3 -m librebase_mcp` locally.
 *
 * Auth: Authorization: Bearer lb_mcp_... or lb_agt_... (org-scoped).
 * The key is validated against the admin-api; the org is resolved once.
 */
import { NextResponse } from "next/server";
import { adminApiEnabled, adminBaseUrl } from "@/lib/librebase-admin-client";

/* ------------------------------------------------------------------ */
/* Tool definitions (mirrors mcp/librebase_mcp/__main__.py)           */
/* ------------------------------------------------------------------ */

interface Tool {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
}

const TOOLS: Tool[] = [
  {
    name: "org_whoami",
    description: "Resolve the MCP key's org (id, name, edition).",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "project_list",
    description: "List projects in the org.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "project_create",
    description: "Create a project (requires an existing instanceId).",
    inputSchema: {
      type: "object",
      required: ["name", "instanceId"],
      properties: {
        name: { type: "string" },
        instanceId: { type: "string" },
        region: { type: "string" },
        deploymentMode: { type: "string", enum: ["dedicated", "shared"] },
      },
    },
  },
  {
    name: "auth_provider_list",
    description: "List OAuth sign-in providers configured for a project.",
    inputSchema: {
      type: "object",
      required: ["projectId"],
      properties: { projectId: { type: "string" } },
    },
  },
  {
    name: "auth_provider_upsert",
    description:
      "Configure an OAuth sign-in provider for a project. " +
      "The client secret is KMS-sealed server-side; it is never returned.",
    inputSchema: {
      type: "object",
      required: ["projectId", "provider", "clientId", "clientSecret", "redirectUris"],
      properties: {
        projectId: { type: "string" },
        provider: { type: "string", enum: ["github", "google", "grok"] },
        clientId: { type: "string" },
        clientSecret: { type: "string" },
        redirectUris: { type: "array", items: { type: "string" } },
        enabled: { type: "boolean" },
      },
    },
  },
  {
    name: "instance_list",
    description: "List instances in the org.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "instance_get",
    description: "Get one instance by id.",
    inputSchema: {
      type: "object",
      required: ["instanceId"],
      properties: { instanceId: { type: "string" } },
    },
  },
  {
    name: "instance_create",
    description: "Create an instance (stopped by default).",
    inputSchema: {
      type: "object",
      required: ["name"],
      properties: {
        name: { type: "string" },
        region: { type: "string" },
        runtimeTarget: { type: "string" },
        deploymentMode: { type: "string", enum: ["dedicated", "shared"] },
        memLimitMb: { type: "integer" },
      },
    },
  },
  {
    name: "instance_launch",
    description: "Launch an instance (status -> running).",
    inputSchema: {
      type: "object",
      required: ["instanceId"],
      properties: { instanceId: { type: "string" } },
    },
  },
  {
    name: "instance_stop",
    description: "Stop an instance (status -> stopped).",
    inputSchema: {
      type: "object",
      required: ["instanceId"],
      properties: { instanceId: { type: "string" } },
    },
  },
  {
    name: "member_list",
    description: "List org members (users).",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "member_invite",
    description: "Invite a user by email with a role.",
    inputSchema: {
      type: "object",
      required: ["email", "role"],
      properties: {
        email: { type: "string" },
        role: { type: "string", enum: ["owner", "admin", "member"] },
      },
    },
  },
  {
    name: "member_update_role",
    description: "Update a member's role.",
    inputSchema: {
      type: "object",
      required: ["userId", "role"],
      properties: {
        userId: { type: "string" },
        role: { type: "string", enum: ["owner", "admin", "member"] },
      },
    },
  },
  {
    name: "host_list",
    description: "List hosts in the org.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "host_create",
    description: "Create a host (VM).",
    inputSchema: {
      type: "object",
      required: ["name"],
      properties: {
        name: { type: "string" },
        region: { type: "string" },
        memMb: { type: "integer" },
      },
    },
  },
];

/* ------------------------------------------------------------------ */
/* Admin-api proxy                                                    */
/* ------------------------------------------------------------------ */

function extractBearer(req: Request): string | null {
  const auth = req.headers.get("authorization");
  if (!auth) return null;
  const m = auth.match(/^Bearer\s+(.+)$/i);
  return m ? m[1].trim() : null;
}

async function adminFetch(
  method: string,
  path: string,
  token: string,
  body?: Record<string, unknown>,
) {
  const url = `${adminBaseUrl()}${path}`;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
  const res = await fetch(url, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });
  const text = await res.text();
  try {
    return JSON.parse(text) as Record<string, unknown>;
  } catch {
    return { error: "parse_error", raw: text, status: res.status };
  }
}

async function callTool(
  name: string,
  args: Record<string, unknown>,
  token: string,
  orgId: string,
) {
  const clean = (o: Record<string, unknown>) =>
    Object.fromEntries(
      Object.entries(o).filter(([, v]) => v != null && v !== ""),
    );

  switch (name) {
    case "org_whoami":
      return adminFetch("GET", "/org/v1/mcp/org", token);
    case "project_list":
      return adminFetch("GET", `/org/v1/orgs/${orgId}/projects`, token);
    case "project_create":
      return adminFetch(
        "POST",
        `/org/v1/orgs/${orgId}/projects`,
        token,
        clean(args),
      );
    case "auth_provider_list":
      return adminFetch(
        "GET",
        `/org/v1/orgs/${orgId}/projects/${String(args.projectId)}/providers`,
        token,
      );
    case "auth_provider_upsert": {
      const projectId = String(args.projectId ?? "");
      const body = { ...clean(args), enabled: true };
      return adminFetch(
        "POST",
        `/org/v1/orgs/${orgId}/projects/${projectId}/providers`,
        token,
        body,
      );
    }
    case "instance_list":
      return adminFetch("GET", `/org/v1/orgs/${orgId}/instances`, token);
    case "instance_get":
      return adminFetch(
        "GET",
        `/org/v1/orgs/${orgId}/instances/${args.instanceId}`,
        token,
      );
    case "instance_create": {
      const body = { ...clean(args), status: "stopped" };
      return adminFetch(
        "POST",
        `/org/v1/orgs/${orgId}/instances`,
        token,
        body,
      );
    }
    case "instance_launch":
      return adminFetch(
        "PATCH",
        `/org/v1/orgs/${orgId}/instances/${args.instanceId}`,
        token,
        { status: "running" },
      );
    case "instance_stop":
      return adminFetch(
        "PATCH",
        `/org/v1/orgs/${orgId}/instances/${args.instanceId}`,
        token,
        { status: "stopped" },
      );
    case "member_list":
      return adminFetch("GET", `/org/v1/orgs/${orgId}/members`, token);
    case "member_invite":
      return adminFetch(
        "POST",
        `/org/v1/orgs/${orgId}/invites`,
        token,
        clean(args),
      );
    case "member_update_role":
      return adminFetch(
        "PATCH",
        `/org/v1/members/${args.userId}`,
        token,
        clean(args),
      );
    case "host_list":
      return adminFetch("GET", `/org/v1/orgs/${orgId}/hosts`, token);
    case "host_create":
      return adminFetch(
        "POST",
        `/org/v1/orgs/${orgId}/hosts`,
        token,
        clean(args),
      );
    default:
      return { error: "not_found", message: `unknown tool ${name}` };
  }
}

/* ------------------------------------------------------------------ */
/* JSON-RPC handler                                                   */
/* ------------------------------------------------------------------ */

function jsonRpc(
  id: string | number | null,
  result: unknown,
): Record<string, unknown> {
  return { jsonrpc: "2.0", id, result };
}

function jsonRpcError(
  id: string | number | null,
  code: number,
  message: string,
): Record<string, unknown> {
  return { jsonrpc: "2.0", id, error: { code, message } };
}

async function handleJsonRpc(
  msg: Record<string, unknown>,
  token: string,
): Promise<Record<string, unknown> | null> {
  const method = msg.method as string;
  const id = msg.id as string | number | null;

  // Validate key early — only for methods that need auth
  let orgId = "";
  if (method !== "initialize" && method !== "notifications/initialized") {
    const orgRes = await adminFetch("GET", "/org/v1/mcp/org", token);
    orgId = String(orgRes.orgId ?? "");
    if (!orgId) {
      // Invalid key — return MCP error, not HTTP error
      return jsonRpc(id, {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              error: "auth_error",
              message: "Invalid or revoked MCP key",
            }),
          },
        ],
      });
    }
  }

  if (method === "initialize") {
    return jsonRpc(id, {
      protocolVersion: "2024-11-05",
      capabilities: { tools: {} },
      serverInfo: { name: "librebase", version: "0.1.5" },
    });
  }
  if (method === "notifications/initialized") return null;

  if (method === "tools/list") {
    return jsonRpc(id, { tools: TOOLS });
  }

  if (method === "tools/call") {
    const params = (msg.params ?? {}) as Record<string, unknown>;
    const toolName = String(params.name ?? "");
    const args = (params.arguments ?? {}) as Record<string, unknown>;

    try {
      const payload = await callTool(toolName, args, token, orgId);
      return jsonRpc(id, {
        content: [{ type: "text", text: JSON.stringify(payload, null, 2) }],
      });
    } catch (exc) {
      return jsonRpc(id, {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              error: "tool_error",
              message: exc instanceof Error ? exc.message : String(exc),
            }),
          },
        ],
      });
    }
  }

  if (id != null) {
    return jsonRpcError(id, -32601, `method not found: ${method}`);
  }
  return null;
}

/* ------------------------------------------------------------------ */
/* Rate limiting (per-IP, in-memory token bucket)                      */
/* ------------------------------------------------------------------ */

const RATE_LIMIT = {
  /** Max requests per window. */
  max: 30,
  /** Window in seconds. */
  windowSec: 60,
};

const hits = new Map<string, { count: number; resetAt: number }>();

// Evict stale entries every 5 min to prevent unbounded growth.
let lastEvict = Date.now();
function evictStale() {
  const now = Date.now();
  if (now - lastEvict < 300_000) return;
  lastEvict = now;
  for (const [k, v] of hits) {
    if (v.resetAt <= now) hits.delete(k);
  }
}

function rateLimit(ip: string): { ok: boolean; retryAfter: number } {
  evictStale();
  const now = Date.now();
  const entry = hits.get(ip);
  if (!entry || entry.resetAt <= now) {
    hits.set(ip, { count: 1, resetAt: now + RATE_LIMIT.windowSec * 1000 });
    return { ok: true, retryAfter: 0 };
  }
  entry.count++;
  if (entry.count > RATE_LIMIT.max) {
    return { ok: false, retryAfter: Math.ceil((entry.resetAt - now) / 1000) };
  }
  return { ok: true, retryAfter: 0 };
}

function getClientIp(request: Request): string {
  return (
    request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ??
    request.headers.get("x-real-ip") ??
    "unknown"
  );
}

/* ------------------------------------------------------------------ */
/* HTTP route                                                         */
/* ------------------------------------------------------------------ */

export async function POST(request: Request) {
  if (!adminApiEnabled()) {
    return NextResponse.json(
      { error: "Admin API disabled" },
      { status: 503 },
    );
  }

  // Rate limit by IP
  const ip = getClientIp(request);
  const rl = rateLimit(ip);
  if (!rl.ok) {
    return NextResponse.json(
      { error: "Rate limited", retryAfter: rl.retryAfter },
      {
        status: 429,
        headers: {
          "Retry-After": String(rl.retryAfter),
          "X-RateLimit-Limit": String(RATE_LIMIT.max),
          "X-RateLimit-Remaining": "0",
          "X-RateLimit-Reset": String(Math.ceil(Date.now() / 1000) + rl.retryAfter),
        },
      },
    );
  }

  const token = extractBearer(request);
  if (!token) {
    return NextResponse.json(
      { error: "Missing Authorization: Bearer <mcp_key>" },
      { status: 401 },
    );
  }

  // Validate token prefix
  if (!token.startsWith("lb_mcp_") && !token.startsWith("lb_agt_")) {
    return NextResponse.json(
      { error: "Invalid MCP key format (expected lb_mcp_ or lb_agt_)" },
      { status: 401 },
    );
  }

  let body: Record<string, unknown>;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error: "Invalid JSON body" },
      { status: 400 },
    );
  }

  const response = await handleJsonRpc(body, token);
  if (response === null) {
    // Notification — no response body
    return new NextResponse(null, { status: 204 });
  }

  return NextResponse.json(response, {
    headers: {
      "Content-Type": "application/json",
      "Mcp-Session-Id": crypto.randomUUID(),
      "X-RateLimit-Limit": String(RATE_LIMIT.max),
      "X-RateLimit-Remaining": String(Math.max(0, RATE_LIMIT.max - (hits.get(ip)?.count ?? 0))),
    },
  });
}

export async function GET() {
  // MCP spec: GET returns server info for discovery
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  return NextResponse.json({
    name: "Librebase MCP",
    version: "0.1.5",
    protocol: "2024-11-05",
    capabilities: { tools: {} },
    toolCount: TOOLS.length,
  });
}

export const runtime = "nodejs";
