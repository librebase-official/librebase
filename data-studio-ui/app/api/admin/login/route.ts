import { NextResponse } from "next/server";
import {
  adminLogin,
  adminApiEnabled,
  SESSION_COOKIE,
  REFRESH_COOKIE,
} from "@/lib/librebase-admin-client";

export async function POST(request: Request) {
  if (!adminApiEnabled()) {
    return NextResponse.json(
      {
        error:
          "Admin API disabled — set LIBREBASE_ADMIN_URL (e.g. http://127.0.0.1:54330)",
      },
      { status: 503 },
    );
  }
  try {
    const body = (await request.json()) as {
      email?: string;
      password?: string;
    };
    if (!body.email?.trim() || !body.password) {
      return NextResponse.json(
        { error: "email and password required" },
        { status: 400 },
      );
    }
    const result = await adminLogin(body.email.trim(), body.password);
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
    const message = error instanceof Error ? error.message : "Login failed";
    const status = message.includes("401") ? 401 : 500;
    return NextResponse.json({ error: message }, { status });
  }
}
