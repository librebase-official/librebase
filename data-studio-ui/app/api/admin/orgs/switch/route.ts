import { NextResponse } from "next/server";
import {
  adminApiEnabled,
  adminSwitchOrg,
  ADMIN_COOKIE_SECURE,
  SESSION_COOKIE,
  REFRESH_COOKIE,
} from "@/lib/librebase-admin-client";

export async function POST(request: Request) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const body = (await request.json().catch(() => ({}))) as { orgId?: string };
  if (!body.orgId) {
    return NextResponse.json({ error: "orgId required" }, { status: 400 });
  }
  try {
    const result = await adminSwitchOrg(body.orgId);
    const res = NextResponse.json(result, { status: 200 });
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
    const message = error instanceof Error ? error.message : "switch failed";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
