import { NextResponse } from "next/server";
import {
  adminApiEnabled,
  adminCreateOrgKey,
  adminErrorPayload,
  adminListOrgKeys,
  type KmsKeyInput,
} from "@/lib/librebase-admin-client";
import { getProjectAsync } from "@/lib/projects-store";

interface RouteParams {
  params: Promise<{ projectId: string }>;
}

export async function GET(_request: Request, { params }: RouteParams) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const { projectId } = await params;
  const project = await getProjectAsync(projectId);
  if (!project) {
    return NextResponse.json({ error: "Project not found" }, { status: 404 });
  }
  try {
    // All keys visible in this project's org (org + project scope).
    const { keys } = await adminListOrgKeys(project.orgId);
    return NextResponse.json({ keys });
  } catch (error) {
    const { error: message, status } = adminErrorPayload(error);
    return NextResponse.json({ error: message }, { status });
  }
}

export async function POST(request: Request, { params }: RouteParams) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const { projectId } = await params;
  const project = await getProjectAsync(projectId);
  if (!project) {
    return NextResponse.json({ error: "Project not found" }, { status: 404 });
  }
  const body = (await request.json().catch(() => ({}))) as KmsKeyInput;
  if (!body.name || !body.plaintext) {
    return NextResponse.json(
      { error: "name and plaintext are required" },
      { status: 400 },
    );
  }
  try {
    const key = await adminCreateOrgKey(project.orgId, {
      name: body.name,
      plaintext: body.plaintext,
      scope: body.scope ?? "org",
      projectId: body.scope === "project" ? projectId : body.projectId,
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