import { NextResponse } from "next/server";
import { adminApiEnabled, adminBaseUrl } from "@/lib/librebase-admin-client";

/**
 * Root handler for /api/admin-proxy — returns service status.
 * The actual proxy logic is in [...path]/route.ts.
 */
export async function GET() {
  if (!adminApiEnabled()) {
    return NextResponse.json(
      { ok: false, error: "Admin API disabled", upstream: null },
      { status: 503 },
    );
  }
  try {
    const res = await fetch(`${adminBaseUrl()}/health`, {
      method: "GET",
      cache: "no-store",
      signal: AbortSignal.timeout(3000),
    });
    const upstream = await res.json().catch(() => null);
    return NextResponse.json({
      ok: true,
      service: "admin-proxy",
      upstream: adminBaseUrl(),
      upstreamHealth: upstream,
    });
  } catch {
    return NextResponse.json(
      { ok: false, service: "admin-proxy", error: "upstream unavailable" },
      { status: 502 },
    );
  }
}

export const runtime = "nodejs";
