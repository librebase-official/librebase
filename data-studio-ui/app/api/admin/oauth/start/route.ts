import { NextResponse } from "next/server";
import { adminApiEnabled, adminOAuthStart } from "@/lib/librebase-admin-client";
import { SITE_URL } from "@/lib/site";

export async function GET(request: Request) {
  const fail = (reason: string) =>
    NextResponse.redirect(new URL(`/login?error=${reason}`, SITE_URL));

  if (!adminApiEnabled()) {
    return fail("disabled");
  }
  const url = new URL(request.url);
  const provider = (url.searchParams.get("provider") ?? "").toLowerCase();
  const next = url.searchParams.get("next") ?? "/projects";
  if (provider !== "github" && provider !== "google") {
    return NextResponse.json({ error: "unsupported provider" }, { status: 400 });
  }
  try {
    const authorizeUrl = await adminOAuthStart(provider, next);
    return NextResponse.redirect(authorizeUrl);
  } catch {
    return fail("oauth");
  }
}
