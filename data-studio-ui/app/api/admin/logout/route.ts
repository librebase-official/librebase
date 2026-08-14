import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import {
  adminLogout,
  adminApiEnabled,
  SESSION_COOKIE,
  REFRESH_COOKIE,
} from "@/lib/librebase-admin-client";

export async function POST() {
  const jar = await cookies();
  const refreshToken = jar.get(REFRESH_COOKIE)?.value;

  if (adminApiEnabled() && refreshToken) {
    try {
      await adminLogout(refreshToken);
    } catch {
      // best-effort: clear local session even if the admin-api is unreachable
    }
  }

  delete process.env.LIBREBASE_ADMIN_SESSION;
  delete process.env.LIBREBASE_ORG_ID;

  const res = NextResponse.json({ ok: true });
  res.cookies.set(SESSION_COOKIE, "", { httpOnly: true, path: "/", maxAge: 0 });
  res.cookies.set(REFRESH_COOKIE, "", { httpOnly: true, path: "/", maxAge: 0 });
  return res;
}
