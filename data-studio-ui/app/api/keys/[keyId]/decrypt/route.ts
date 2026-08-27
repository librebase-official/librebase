import { NextResponse } from "next/server";
import {
  adminApiEnabled,
  adminDecryptKey,
  adminErrorPayload,
} from "@/lib/librebase-admin-client";

interface RouteParams {
  params: Promise<{ keyId: string }>;
}

export async function POST(_request: Request, { params }: RouteParams) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const { keyId } = await params;
  try {
    // The plaintext is returned to the browser so the operator can copy it
    // once. It is never persisted client-side and never logged.
    return NextResponse.json(await adminDecryptKey(keyId));
  } catch (error) {
    const { error: message, status } = adminErrorPayload(error);
    return NextResponse.json({ error: message }, { status });
  }
}

export const runtime = "nodejs";