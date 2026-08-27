import { NextResponse } from "next/server";
import { adminApiEnabled, adminBaseUrl } from "@/lib/librebase-admin-client";

/**
 * Minimal public ingress for the internal admin-api.
 *
 * The admin-api binds 127.0.0.1 inside the private network, so Stripe,
 * the host agent, and other external callers cannot reach it directly.
 * This route proxies a strictly ALLOWLISTED set of upstream admin-api paths
 * and passes through the raw body plus the headers that path requires
 * (e.g. Stripe-Signature, whose HMAC covers the exact bytes — so the body
 * MUST NOT be re-serialized).
 */

const PROXY_ALLOW = new Set<string>([
  "/org/v1/billing/webhook",
  "/org/v1/host-agent/register",
  "/org/v1/host-agent/heartbeat",
  "/org/v1/host-agent/instances",
  "/org/v1/mcp/device/start",
  "/org/v1/mcp/device/token",
  "/org/v1/auth/grok/start",
  "/org/v1/auth/grok/poll",
  "/health",
]);

function mcpAgentBearer(auth: string | null): boolean {
  if (!auth) return false;
  const token = auth.replace(/^Bearer\s+/i, "").trim();
  return token.startsWith("lb_mcp_") || token.startsWith("lb_agt_");
}

function pathAllowed(upstreamPath: string, request: Request): boolean {
  if (PROXY_ALLOW.has(upstreamPath)) return true;
  // Host agent fetches its per-instance runtime keys (dynamic instance id). The
  // admin validates the host-agent token (401 if invalid) and scopes the keys to
  // the calling host's instances, so forwarding this path is safe.
  if (/^\/org\/v1\/host-agent\/instances\/[^/]+\/runtime-keys$/.test(upstreamPath)) {
    return true;
  }
  // Host agent acks a completed instance restart (clears restart_requested).
  // Same token validation + host scoping as runtime-keys.
  if (/^\/org\/v1\/host-agent\/instances\/[^/]+\/restart-ack$/.test(upstreamPath)) {
    return true;
  }
  if (/^\/org\/v1\/host-agent\/backups$/.test(upstreamPath)) return true;
  if (/^\/org\/v1\/host-agent\/backups\/[^/]+\/complete$/.test(upstreamPath)) return true;
  if (/^\/org\/v1\/host-agent\/instances\/[^/]+\/backup-keys$/.test(upstreamPath)) return true;
  if (/^\/org\/v1\/host-agent\/buckets\/[^/]+\/creds$/.test(upstreamPath)) return true;
  // KMS key management (scoped to caller's org via admin-api auth)
  if (/^\/org\/v1\/orgs\/[^/]+\/keys$/.test(upstreamPath)) return true;
  if (/^\/org\/v1\/keys\/[^/]+$/.test(upstreamPath)) return true;
  if (/^\/org\/v1\/keys\/[^/]+\/decrypt$/.test(upstreamPath)) return true;
  if (/^\/org\/v1\/keys\/[^/]+\/rotate$/.test(upstreamPath)) return true;
  if (/^\/org\/v1\/me\/keys$/.test(upstreamPath)) return true;
  // BYO external buckets — Studio (session JWT) and MCP (agent) both allowed (admin validates org membership)
  if (/^\/org\/v1\/orgs\/[^/]+\/buckets$/.test(upstreamPath)) return true;
  if (/^\/org\/v1\/orgs\/[^/]+\/buckets\/[^/]+$/.test(upstreamPath)) return true;
  if (/^\/org\/v1\/orgs\/[^/]+\/projects\/[^/]+\/backup-external-bucket$/.test(upstreamPath)) return true;
  // Agent tokens obtained via browser login may call the admin API through
  // this public ingress. Session JWTs must not.
  return upstreamPath.startsWith("/org/v1/") && mcpAgentBearer(request.headers.get("authorization"));
}

function paramsPath(path: string[] | undefined): string | null {
  if (!path || path.length === 0) return null;
  for (const seg of path) {
    if (!seg || seg.includes("..") || seg.includes("/") || seg.includes("\0")) {
      return null;
    }
  }
  return "/" + path.join("/");
}

async function forward(
  request: Request,
  upstreamPath: string,
): Promise<NextResponse> {
  if (!adminApiEnabled()) {
    return NextResponse.json(
      {
        error:
          "Admin API disabled — set LIBREBASE_ADMIN_URL (e.g. http://127.0.0.1:54330)",
      },
      { status: 503 },
    );
  }
  if (!pathAllowed(upstreamPath, request)) {
    return NextResponse.json({ error: "not allowed" }, { status: 404 });
  }

  const body = await request.arrayBuffer();
  const headers = new Headers();
  if (request.headers.has("content-type")) {
    headers.set("content-type", request.headers.get("content-type")!);
  }
  // Webhook signature depends on the exact raw bytes of the body.
  if (request.headers.has("stripe-signature")) {
    headers.set("stripe-signature", request.headers.get("stripe-signature")!);
  }
  // Host agent authenticates with a bearer token bound at provisioning time.
  if (request.headers.has("authorization")) {
    headers.set("authorization", request.headers.get("authorization")!);
  }

  try {
    const method = request.method.toUpperCase();
    const sendBody = method !== "GET" && method !== "HEAD" && body.byteLength > 0;
    const res = await fetch(`${adminBaseUrl()}${upstreamPath}`, {
      method: request.method,
      body: sendBody ? body : undefined,
      headers,
      cache: "no-store",
    });
    const text = await res.text();
    return new NextResponse(text, {
      status: res.status,
      headers: { "content-type": "application/json" },
    });
  } catch {
    return NextResponse.json(
      { error: "upstream unavailable" },
      { status: 502 },
    );
  }
}

type RouteCtx = { params: Promise<{ path?: string[] }> };

async function handle(request: Request, ctx: RouteCtx) {
  const { path } = await ctx.params;
  const upstreamPath = paramsPath(path);
  if (!upstreamPath) {
    return NextResponse.json({ error: "invalid path" }, { status: 400 });
  }
  return forward(request, upstreamPath);
}

export async function GET(request: Request, ctx: RouteCtx) {
  return handle(request, ctx);
}

export async function POST(request: Request, ctx: RouteCtx) {
  return handle(request, ctx);
}

export async function PATCH(request: Request, ctx: RouteCtx) {
  return handle(request, ctx);
}

export async function DELETE(request: Request, ctx: RouteCtx) {
  return handle(request, ctx);
}

export const runtime = "nodejs";
