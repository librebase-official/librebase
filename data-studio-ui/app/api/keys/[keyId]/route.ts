import { NextResponse } from "next/server";
import {
  adminApiEnabled,
  adminDeleteKey,
  adminErrorPayload,
  adminGetKey,
  adminUpdateKey,
} from "@/lib/librebase-admin-client";

interface RouteParams {
  params: Promise<{ keyId: string }>;
}

export async function GET(_request: Request, { params }: RouteParams) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const { keyId } = await params;
  try {
    return NextResponse.json(await adminGetKey(keyId));
  } catch (error) {
    const { error: message, status } = adminErrorPayload(error);
    return NextResponse.json({ error: message }, { status });
  }
}

export async function PATCH(request: Request, { params }: RouteParams) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const { keyId } = await params;
  const body = (await request.json().catch(() => ({}))) as {
    rateLimit?: number;
    expiresAt?: string | null;
  };
  try {
    return NextResponse.json(
      await adminUpdateKey(keyId, {
        rateLimit: body.rateLimit,
        expiresAt: body.expiresAt,
      }),
    );
  } catch (error) {
    const { error: message, status } = adminErrorPayload(error);
    return NextResponse.json({ error: message }, { status });
  }
}

export async function DELETE(_request: Request, { params }: RouteParams) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const { keyId } = await params;
  try {
    return NextResponse.json(await adminDeleteKey(keyId));
  } catch (error) {
    const { error: message, status } = adminErrorPayload(error);
    return NextResponse.json({ error: message }, { status });
  }
}

export const runtime = "nodejs";