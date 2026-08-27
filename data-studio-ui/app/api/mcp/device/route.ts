import { NextResponse } from "next/server";
import {
  adminApiEnabled,
  adminErrorPayload,
  adminGetMcpDevice,
} from "@/lib/librebase-admin-client";

export async function GET(request: Request) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const userCode = new URL(request.url).searchParams.get("user_code") ?? "";
  if (!userCode.trim()) {
    return NextResponse.json({ error: "user_code required" }, { status: 400 });
  }
  try {
    return NextResponse.json(await adminGetMcpDevice(userCode.trim()));
  } catch (error) {
    const { error: message, status } = adminErrorPayload(error, "device lookup failed");
    return NextResponse.json({ error: message }, { status });
  }
}

export const runtime = "nodejs";
