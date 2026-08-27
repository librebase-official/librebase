import { NextResponse } from "next/server";
import {
  adminApiEnabled,
  adminApproveMcpDevice,
  adminErrorPayload,
} from "@/lib/librebase-admin-client";

export async function POST(request: Request) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const body = (await request.json().catch(() => ({}))) as {
    userCode?: string;
    orgId?: string;
    fullAgentMode?: boolean;
    scope?: "user" | "project";
    projectId?: string;
  };
  if (!body.userCode?.trim()) {
    return NextResponse.json({ error: "userCode required" }, { status: 400 });
  }
  try {
    return NextResponse.json(
      await adminApproveMcpDevice(
        body.userCode.trim(),
        body.orgId?.trim(),
        body.fullAgentMode === true,
        body.scope,
        body.projectId?.trim() || undefined,
      ),
    );
  } catch (error) {
    const { error: message, status } = adminErrorPayload(error, "approve failed");
    return NextResponse.json({ error: message }, { status });
  }
}

export const runtime = "nodejs";
