/**
 * Hosted MCP endpoint — Streamable HTTP transport.
 *
 * Agents POST JSON-RPC messages here. Device-flow auth_start/auth_poll are
 * public; all resource and administration tools require an org-scoped MCP key.
 */
import { NextResponse } from "next/server";
import { HOSTED_MCP_TOOLS } from "@/lib/hosted-mcp-tools";
import { adminApiEnabled, adminBaseUrl } from "@/lib/librebase-admin-client";

const APP_VERSION = process.env.LIBREBASE_VERSION ?? "0.0.0";

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

    case "auth_start": {
      const clientName = String(args.clientName ?? "MCP Agent");
      const startBody: Record<string, unknown> = { clientName };
      if (args.botId) startBody.botId = args.botId;
      const res = await fetch(`${adminBaseUrl()}/org/v1/mcp/device/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(startBody),
        cache: "no-store",
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(
          typeof payload === "object" && payload && "error" in payload
            ? String((payload as { error?: string }).error)
            : `device start failed (${res.status})`,
        );
      }
      return payload;
    }
    case "auth_poll": {
      const dc = String(args.deviceCode ?? "");
      const res = await fetch(`${adminBaseUrl()}/org/v1/mcp/device/token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ deviceCode: dc }),
        cache: "no-store",
      });
      return await res.json();
    }

    case "key_list":
      return adminFetch("GET", `/org/v1/orgs/${orgId}/keys`, token);
    case "key_create": {
      const body = { ...clean(args) };
      return adminFetch("POST", `/org/v1/orgs/${orgId}/keys`, token, body);
    }
    case "key_get":
      return adminFetch("GET", `/org/v1/keys/${String(args.keyId)}`, token);
    case "key_decrypt":
      return adminFetch("POST", `/org/v1/keys/${String(args.keyId)}/decrypt`, token, {});
    case "key_rotate":
      return adminFetch("POST", `/org/v1/keys/${String(args.keyId)}/rotate`, token, {});
    case "key_update":
      return adminFetch("PATCH", `/org/v1/keys/${String(args.keyId)}`, token, clean(args));
    case "key_delete":
      return adminFetch("DELETE", `/org/v1/keys/${String(args.keyId)}`, token);
    case "mcp_agent_token_list":
      return adminFetch(
        "GET",
        `/org/v1/orgs/${orgId}/bots/${String(args.botId)}/mcp-tokens`,
        token,
      );
    case "mcp_agent_token_rotate":
      return adminFetch(
        "POST",
        `/org/v1/orgs/${orgId}/bots/${String(args.botId)}/mcp-tokens/rotate`,
        token,
        {},
      );
    case "mcp_agent_token_revoke":
      return adminFetch(
        "POST",
        `/org/v1/orgs/${orgId}/bots/${String(args.botId)}/mcp-tokens/${String(args.tokenId)}/revoke`,
        token,
        {},
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

  // Validate key early — only for methods that need auth.
  // Public protocol and device-flow calls work without a key:
  // initialize, notifications/initialized, tools/list, and
  // tools/call auth_start / auth_poll.
  const msgParams = (msg.params ?? {}) as Record<string, unknown>;
  const msgToolName = method === "tools/call" ? String(msgParams.name ?? "") : "";
  const needsOrg =
    method !== "initialize" &&
    method !== "notifications/initialized" &&
    method !== "tools/list" &&
    !(method === "tools/call" && (msgToolName === "auth_start" || msgToolName === "auth_poll"));

  let orgId = "";
  if (needsOrg) {
    const orgRes = await adminFetch("GET", "/org/v1/mcp/org", token);
    orgId = String(orgRes.orgId ?? "");
    if (!orgId) {
      const cause =
        typeof orgRes.cause === "string" ? orgRes.cause : "unknown_token";
      return jsonRpc(id, {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              error: "auth_error",
              cause,
              message: `MCP token rejected (${cause})`,
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
      serverInfo: { name: "librebase", version: APP_VERSION },
    });
  }
  if (method === "notifications/initialized") return null;

  if (method === "tools/list") {
    return jsonRpc(id, { tools: HOSTED_MCP_TOOLS });
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
/* Usage logging (best-effort, non-blocking)                          */
/* ------------------------------------------------------------------ */

async function logMcpUsage(
  toolName: string,
  status: string,
  latencyMs: number,
  ip: string,
  request: Request,
): Promise<void> {
  try {
    await fetch(`${adminBaseUrl()}/org/v1/mcp/usage`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: request.headers.get("authorization") ?? "",
      },
      body: JSON.stringify({
        tool: toolName,
        status,
        latency_ms: latencyMs,
        ip,
        user_agent: request.headers.get("user-agent") ?? "",
      }),
      cache: "no-store",
      signal: AbortSignal.timeout(3000),
    });
  } catch {
    // best-effort — never block the response
  }
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

  let body: Record<string, unknown>;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error: "Invalid JSON body" },
      { status: 400 },
    );
  }

  const method = String(body.method ?? "");
  const params = (body.params ?? {}) as Record<string, unknown>;
  const toolName = method === "tools/call" ? String(params.name ?? "") : "";
  const publicAuthTool = method === "tools/call" &&
    (toolName === "auth_start" || toolName === "auth_poll");

  const publicMethod =
    method === "initialize" ||
    method === "notifications/initialized" ||
    method === "tools/list" ||
    publicAuthTool;
  if (!publicMethod && !token) {
    return NextResponse.json(
      { error: "Missing Authorization: Bearer <mcp_key>" },
      {
        status: 401,
        headers: {
          "WWW-Authenticate": 'Bearer realm="librebase-mcp", resource_metadata="https://app.librebase.xyz/.well-known/oauth-authorization-server"',
        },
      },
    );
  }

  // Validate token prefix for protected calls; public protocol/auth calls do not need one.
  if (!publicMethod && token && !token.startsWith("lb_mcp_") && !token.startsWith("lb_agt_")) {
    return NextResponse.json(
      { error: "Invalid MCP key format (expected lb_mcp_ or lb_agt_)" },
      { status: 401 },
    );
  }

  const started = Date.now();
  const response = await handleJsonRpc(body, token ?? "");
  const latencyMs = Date.now() - started;

  if (response === null) {
    // Notification — no response body
    return new NextResponse(null, { status: 204 });
  }

  // Log usage to admin-api (best-effort, non-blocking)
  const hasError = !!(response as Record<string, unknown>).error;
  void logMcpUsage(toolName, hasError ? "error" : "ok", latencyMs, ip, request).catch(() => {});

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
    version: APP_VERSION,
    protocol: "2024-11-05",
    capabilities: { tools: {} },
    toolCount: HOSTED_MCP_TOOLS.length,
  });
}

export const runtime = "nodejs";
