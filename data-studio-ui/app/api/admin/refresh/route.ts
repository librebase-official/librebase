import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import {
  adminRefresh,
  adminApiEnabled,
  SESSION_COOKIE,
  REFRESH_COOKIE,
} from "@/lib/librebase-admin-client";

export async function POST() {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  try {
    const jar = await cookies();
    const refreshToken = jar.get(REFRESH_COOKIE)?.value;
    if (!refreshToken) {
      return NextResponse.json({ error: "no refresh token" }, { status: 401 });
    }
    const result = await adminRefresh(refreshToken);
    process.env.LIBREBASE_ADMIN_SESSION = result.token;
    process.env.LIBREBASE_ORG_ID = result.orgId;
    const res = NextResponse.json(result, { status: 200 });
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
    const message = error instanceof Error ? error.message : "Refresh failed";
    return NextResponse.json({ error: message }, { status: 401 });
  }
}
