import { NextResponse } from "next/server";
import { adminApiEnabled, adminBaseUrl } from "@/lib/librebase-admin-client";

export async function GET() {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "admin API disabled" }, { status: 503 });
  }
  try {
    const res = await fetch(`${adminBaseUrl()}/org/v1/auth/grok/start`);
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    const message = error instanceof Error ? error.message : "grok start failed";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
