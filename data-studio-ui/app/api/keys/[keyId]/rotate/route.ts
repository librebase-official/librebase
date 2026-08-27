import { NextResponse } from "next/server";
import {
  adminApiEnabled,
  adminErrorPayload,
  adminRotateKey,
} from "@/lib/librebase-admin-client";

interface RouteParams {
  params: Promise<{ keyId: string }>;
}

export async function POST(request: Request, { params }: RouteParams) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const { keyId } = await params;
  const body = (await request.json().catch(() => ({}))) as {
    plaintext?: string;
  };
  try {
    return NextResponse.json(await adminRotateKey(keyId, body.plaintext));
  } catch (error) {
    const { error: message, status } = adminErrorPayload(error);
    return NextResponse.json({ error: message }, { status });
  }
}

export const runtime = "nodejs";