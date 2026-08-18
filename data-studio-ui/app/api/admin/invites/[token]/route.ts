import { NextResponse } from "next/server";
import {
  adminApiEnabled,
  adminPreviewInvite,
  adminAcceptInvite,
} from "@/lib/librebase-admin-client";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ token: string }> },
) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const { token } = await params;
  try {
    return NextResponse.json(await adminPreviewInvite(token));
  } catch (e: any) {
    const status = e?.message?.includes("404") ? 404 : 410;
    return NextResponse.json({ error: e instanceof Error ? e.message : "not found" }, { status });
  }
}

export async function POST(
  _request: Request,
  { params }: { params: Promise<{ token: string }> },
) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const { token } = await params;
  try {
    return NextResponse.json(await adminAcceptInvite(token));
  } catch (e: any) {
    const m = e instanceof Error ? e.message : String(e);
    const status = m.includes("403") ? 403 : m.includes("401") ? 401 : 410;
    return NextResponse.json({ error: m }, { status });
  }
}
