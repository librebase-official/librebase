import { NextResponse } from "next/server";
import {
  adminApiEnabled,
  adminCreateMyKey,
  adminErrorPayload,
  adminListMyKeys,
  type KmsKeyInput,
} from "@/lib/librebase-admin-client";

export async function GET() {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  try {
    return NextResponse.json(await adminListMyKeys());
  } catch (error) {
    const { error: message, status } = adminErrorPayload(error);
    return NextResponse.json({ error: message }, { status });
  }
}

export async function POST(request: Request) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const body = (await request.json().catch(() => ({}))) as KmsKeyInput;
  if (!body.name || !body.plaintext) {
    return NextResponse.json(
      { error: "name and plaintext are required" },
      { status: 400 },
    );
  }
  try {
    const key = await adminCreateMyKey({
      name: body.name,
      plaintext: body.plaintext,
      rateLimit: body.rateLimit,
      expiresAt: body.expiresAt,
    });
    return NextResponse.json({ key }, { status: 201 });
  } catch (error) {
    const { error: message, status } = adminErrorPayload(error);
    return NextResponse.json({ error: message }, { status });
  }
}

export const runtime = "nodejs";