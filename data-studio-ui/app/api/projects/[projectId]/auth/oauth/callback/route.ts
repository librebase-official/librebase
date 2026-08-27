import { NextResponse } from "next/server";
import { adminApiEnabled, adminBaseUrl } from "@/lib/librebase-admin-client";
import { projectOAuthFail } from "@/lib/project-oauth";

interface RouteParams {
  params: Promise<{ projectId: string }>;
}

export async function GET(request: Request, { params }: RouteParams) {
  const fail = (reason: string) => projectOAuthFail(request, reason);
  if (!adminApiEnabled()) return fail("disabled");
  const { projectId } = await params;
  const incoming = new URL(request.url);
  const upstream = new URL(
    `${adminBaseUrl()}/org/v1/projects/${encodeURIComponent(projectId)}/oauth/callback`,
  );
  incoming.searchParams.forEach((value, key) => upstream.searchParams.set(key, value));
  try {
    const res = await fetch(upstream.toString(), {
      redirect: "manual",
      cache: "no-store",
    });
    const location = res.headers.get("location");
    if (res.status >= 300 && res.status < 400 && location) {
      const dest = new URL(location, incoming);
      if (dest.pathname === "/login" || dest.pathname.startsWith("/login/")) {
        return fail("oauth");
      }
      return NextResponse.redirect(location, { headers: { "Cache-Control": "no-store" } });
    }
    const data = (await res.json().catch(() => ({}))) as { error?: string };
    return fail(data.error ?? "oauth");
  } catch {
    return fail("oauth");
  }
}

export const runtime = "nodejs";
