import { NextResponse } from "next/server";
import {
  adminApiEnabled,
  adminDenyMcpDevice,
  adminErrorPayload,
} from "@/lib/librebase-admin-client";

export async function POST(request: Request) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const body = (await request.json().catch(() => ({}))) as { userCode?: string };
  if (!body.userCode?.trim()) {
    return NextResponse.json({ error: "userCode required" }, { status: 400 });
  }
  try {
    return NextResponse.json(await adminDenyMcpDevice(body.userCode.trim()));
  } catch (error) {
    const { error: message, status } = adminErrorPayload(error, "deny failed");
    return NextResponse.json({ error: message }, { status });
  }
}

export const runtime = "nodejs";
