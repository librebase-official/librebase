import { NextResponse } from "next/server";
import {
  adminApiEnabled,
  adminCreateApp,
  adminErrorPayload,
  adminListApps,
} from "@/lib/librebase-admin-client";
import { resolveStudioOrgId } from "@/lib/org-context";

export async function GET() {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  try {
    const orgId = await resolveStudioOrgId();
    return NextResponse.json(await adminListApps(orgId));
  } catch (error) {
    const { error: message, status } = adminErrorPayload(error);
    return NextResponse.json({ error: message }, { status });
  }
}

export async function POST(request: Request) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const body = (await request.json().catch(() => ({}))) as {
    name?: string;
    projectId?: string;
  };
  if (!body.name) {
    return NextResponse.json({ error: "name is required" }, { status: 400 });
  }
  try {
    const orgId = await resolveStudioOrgId();
    return NextResponse.json(
      await adminCreateApp(orgId, { name: body.name, projectId: body.projectId }),
      { status: 201 },
    );
  } catch (error) {
    const { error: message, status } = adminErrorPayload(error);
    return NextResponse.json({ error: message }, { status });
  }
}

export const runtime = "nodejs";