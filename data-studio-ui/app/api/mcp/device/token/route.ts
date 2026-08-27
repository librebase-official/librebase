import { NextResponse } from "next/server";
import {
  AdminApiError,
  adminApiEnabled,
  adminErrorPayload,
  adminMcpDeviceToken,
} from "@/lib/librebase-admin-client";

export async function POST(request: Request) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const body = (await request.json().catch(() => ({}))) as { deviceCode?: string };
  const deviceCode = body.deviceCode?.trim() ?? "";
  if (!deviceCode) {
    return NextResponse.json({ error: "invalid_grant" }, { status: 400 });
  }
  try {
    const payload = await adminMcpDeviceToken(deviceCode);
    return NextResponse.json(payload);
  } catch (error) {
    if (error instanceof AdminApiError) {
      return NextResponse.json(error.body ?? { error: error.message }, {
        status: error.status || 400,
      });
    }
    const { error: message, status } = adminErrorPayload(error);
    return NextResponse.json({ error: message }, { status });
  }
}

export const runtime = "nodejs";
