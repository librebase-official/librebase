import { NextResponse } from "next/server";
import {
  adminApiEnabled,
  adminOAuthCallback,
  ADMIN_COOKIE_SECURE,
  SESSION_COOKIE,
  REFRESH_COOKIE,
} from "@/lib/librebase-admin-client";
import { SITE_URL } from "@/lib/site";

function decodeState(state: string): { provider: string; next: string } {
  try {
    const padded = state + "=".repeat((4 - (state.length % 4)) % 4);
    const decoded = JSON.parse(Buffer.from(padded, "base64url").toString("utf-8")) as {
      provider?: string;
      next?: string;
    };
    return {
      provider: (decoded.provider ?? "").toLowerCase(),
      next: decoded.next ?? "/projects",
    };
  } catch {
    return { provider: "", next: "/projects" };
  }
}

export async function GET(request: Request) {
  const url = new URL(request.url);
  const code = url.searchParams.get("code") ?? "";
  const state = url.searchParams.get("state") ?? "";
  const fail = (reason: string) =>
    NextResponse.redirect(new URL(`/login?error=${reason}`, SITE_URL));

  if (!adminApiEnabled()) {
    return fail("disabled");
  }
  const { provider, next } = decodeState(state);
  if (!code || !provider) {
    return fail("oauth");
  }
  try {
    const result = await adminOAuthCallback(provider, code);
    process.env.LIBREBASE_ADMIN_SESSION = result.token;
    process.env.LIBREBASE_ORG_ID = result.orgId;
    const redirectPath = next.startsWith("/") ? next : "/projects";
    const res = NextResponse.redirect(new URL(redirectPath, SITE_URL));
    res.cookies.set(SESSION_COOKIE, result.token, {
      httpOnly: true,
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 15,
      secure: ADMIN_COOKIE_SECURE,
    });
    res.cookies.set(REFRESH_COOKIE, result.refreshToken, {
      httpOnly: true,
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 24 * 30,
      secure: ADMIN_COOKIE_SECURE,
    });
    return res;
  } catch (error) {
    const message = error instanceof Error ? error.message : "oauth failed";
    const reason =
      message.includes("invite") || message.includes("403")
        ? "no_account"
        : "oauth";
    return fail(reason);
  }
}
