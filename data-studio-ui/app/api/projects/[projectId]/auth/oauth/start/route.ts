import { NextResponse } from "next/server";
import { adminApiEnabled, adminBaseUrl } from "@/lib/librebase-admin-client";
import { projectOAuthFail, wantsJson } from "@/lib/project-oauth";

interface RouteParams {
  params: Promise<{ projectId: string }>;
}

export async function GET(request: Request, { params }: RouteParams) {
  const url = new URL(request.url);
  const redirectTo =
    url.searchParams.get("redirect_to") ?? url.searchParams.get("redirectTo") ?? "";
  const json = wantsJson(request, url);
  const fail = (reason: string, status = 404) =>
    json
      ? NextResponse.json({ error: reason }, { status, headers: { "Cache-Control": "no-store" } })
      : projectOAuthFail(request, reason, redirectTo);

  if (!adminApiEnabled()) return fail("disabled", 503);
  const { projectId } = await params;
  const provider = (url.searchParams.get("provider") ?? "").toLowerCase();
  if (provider !== "github" && provider !== "google") {
    return NextResponse.json({ error: "unsupported provider" }, { status: 400 });
  }
  const upstream = new URL(
    `${adminBaseUrl()}/org/v1/projects/${encodeURIComponent(projectId)}/oauth/start`,
  );
  upstream.searchParams.set("provider", provider);
  if (redirectTo) upstream.searchParams.set("redirect_to", redirectTo);
  try {
    const res = await fetch(upstream, {
      headers: { Accept: "application/json" },
      cache: "no-store",
    });
    const data = (await res.json().catch(() => ({}))) as { url?: string; error?: string };
    if (!res.ok || !data.url) {
      return fail(data.error ?? "oauth", res.status || 502);
    }
    if (json) {
      return NextResponse.json(
        { url: data.url },
        { headers: { "Cache-Control": "no-store" } },
      );
    }
    return NextResponse.redirect(data.url, { headers: { "Cache-Control": "no-store" } });
  } catch {
    return fail("oauth", 502);
  }
}

export const runtime = "nodejs";
