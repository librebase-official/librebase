import { NextResponse } from "next/server";
import { adminApiEnabled, adminOAuthStartUrl } from "@/lib/librebase-admin-client";

export async function GET(request: Request) {
  if (!adminApiEnabled()) {
    return NextResponse.redirect(new URL("/login?error=disabled", request.url));
  }
  const url = new URL(request.url);
  const provider = (url.searchParams.get("provider") ?? "").toLowerCase();
  const next = url.searchParams.get("next") ?? "/projects";
  if (provider !== "github" && provider !== "google") {
    return NextResponse.json({ error: "unsupported provider" }, { status: 400 });
  }
  return NextResponse.redirect(adminOAuthStartUrl(provider, next));
}
