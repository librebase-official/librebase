import { NextResponse } from "next/server";
import {
  adminApiEnabled,
  adminErrorPayload,
  adminRotateInstanceKeys,
} from "@/lib/librebase-admin-client";
import { resolveStudioOrgId } from "@/lib/org-context";

interface RouteParams {
  params: Promise<{ instanceId: string }>;
}

export async function POST(_request: Request, { params }: RouteParams) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const { instanceId } = await params;
  try {
    const orgId = await resolveStudioOrgId();
    return NextResponse.json(
      await adminRotateInstanceKeys(orgId, instanceId),
    );
  } catch (error) {
    const { error: message, status } = adminErrorPayload(error);
    return NextResponse.json({ error: message }, { status });
  }
}

export const runtime = "nodejs";