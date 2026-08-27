import { NextResponse } from "next/server";
import { FEEDBACK_ORIGIN } from "@/lib/demo";

const CONSOLE_HOSTS = new Set(["app.librebase.xyz", "app-stage.librebase.xyz"]);

function isSafeHttpUrl(raw: string): URL | null {
  try {
    const url = new URL(raw);
    if (url.protocol !== "https:" && url.protocol !== "http:") return null;
    if (!url.hostname) return null;
    return url;
  } catch {
    return null;
  }
}

function isConsoleDump(url: URL): boolean {
  const host = url.hostname.toLowerCase();
  if (CONSOLE_HOSTS.has(host)) return true;
  if (url.pathname === "/login" || url.pathname.startsWith("/login/")) return true;
  return false;
}

/** Never send project-user OAuth failures to Studio operator login. */
export function projectOAuthFail(request: Request, reason: string, redirectTo = ""): NextResponse {
  const candidates = [redirectTo, request.headers.get("referer") ?? ""];
  for (const raw of candidates) {
    const url = isSafeHttpUrl(raw);
    if (!url || isConsoleDump(url)) continue;
    url.hash = "";
    url.search = "";
    url.searchParams.set("oauth_error", reason);
    return NextResponse.redirect(url, { headers: { "Cache-Control": "no-store" } });
  }
  return NextResponse.redirect(
    new URL(`/?oauth_error=${encodeURIComponent(reason)}`, FEEDBACK_ORIGIN),
    { headers: { "Cache-Control": "no-store" } },
  );
}

export function wantsJson(request: Request, url: URL): boolean {
  if ((url.searchParams.get("format") ?? "").toLowerCase() === "json") return true;
  return (request.headers.get("accept") ?? "").includes("application/json");
}
