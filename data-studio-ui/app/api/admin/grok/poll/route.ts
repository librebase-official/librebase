import { NextResponse } from "next/server";
import {
  adminApiEnabled,
  adminBaseUrl,
  ADMIN_COOKIE_SECURE,
  SESSION_COOKIE,
  REFRESH_COOKIE,
} from "@/lib/librebase-admin-client";

export async function GET(request: Request) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "admin API disabled" }, { status: 503 });
  }
  const url = new URL(request.url);
  const deviceCode = url.searchParams.get("deviceCode") ?? "";
  if (!deviceCode) {
    return NextResponse.json({ error: "deviceCode required" }, { status: 400 });
  }
  try {
    const res = await fetch(
      `${adminBaseUrl()}/org/v1/auth/grok/poll?deviceCode=${encodeURIComponent(deviceCode)}`,
    );
    const data = await res.json();

    // If the poll returned a token (login success), set session cookies
    if (data.token && data.refreshToken) {
      const resp = NextResponse.json(data, { status: 200 });
      resp.cookies.set(SESSION_COOKIE, data.token, {
        httpOnly: true,
        sameSite: "lax",
        path: "/",
        maxAge: 60 * 15,
        secure: ADMIN_COOKIE_SECURE,
      });
      resp.cookies.set(REFRESH_COOKIE, data.refreshToken, {
        httpOnly: true,
        sameSite: "lax",
        path: "/",
        maxAge: 60 * 60 * 24 * 30,
        secure: ADMIN_COOKIE_SECURE,
      });
      return resp;
    }

    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    const message = error instanceof Error ? error.message : "grok poll failed";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
