import { NextResponse } from "next/server";
import {
  adminApiEnabled,
  adminOAuthCallback,
  SESSION_COOKIE,
  REFRESH_COOKIE,
} from "@/lib/librebase-admin-client";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const provider = (url.searchParams.get("provider") ?? "").toLowerCase();
  const code = url.searchParams.get("code") ?? "";
  const fail = (reason: string) =>
    NextResponse.redirect(new URL(`/login?error=${reason}`, request.url));

  if (!adminApiEnabled()) {
    return fail("disabled");
  }
  if (!code) {
    return fail("oauth");
  }
  try {
    const result = await adminOAuthCallback(provider, code);
    process.env.LIBREBASE_ADMIN_SESSION = result.token;
    process.env.LIBREBASE_ORG_ID = result.orgId;
    const next = result.next.startsWith("/") ? result.next : "/projects";
    const res = NextResponse.redirect(new URL(next, request.url));
    res.cookies.set(SESSION_COOKIE, result.token, {
      httpOnly: true,
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 15,
    });
    res.cookies.set(REFRESH_COOKIE, result.refreshToken, {
      httpOnly: true,
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 24 * 30,
    });
    return res;
  } catch (error) {
    const message = error instanceof Error ? error.message : "oauth failed";
    const reason = message.includes("invite") || message.includes("403")
      ? "no_account"
      : "oauth";
    return fail(reason);
  }
}
