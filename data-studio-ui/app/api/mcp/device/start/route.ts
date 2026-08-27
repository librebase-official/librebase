import { NextResponse } from "next/server";
import {
  adminApiEnabled,
  adminErrorPayload,
  adminMcpDeviceStart,
} from "@/lib/librebase-admin-client";

export async function POST(request: Request) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const body = (await request.json().catch(() => ({}))) as { clientName?: string };
  try {
    const started = await adminMcpDeviceStart({
      clientName: body.clientName,
    });
    return NextResponse.json(started);
  } catch (error) {
    const { error: message, status } = adminErrorPayload(error);
    return NextResponse.json({ error: message }, { status });
  }
}

export const runtime = "nodejs";
