import { NextResponse } from "next/server";
import {
  adminApiEnabled,
  adminErrorPayload,
  adminListProjectProviders,
  adminUpsertProjectProvider,
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
    const providers = await adminListProjectProviders(project.orgId, projectId);
    return NextResponse.json({ providers });
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
  const body = (await request.json().catch(() => ({}))) as {
    provider?: string;
    clientId?: string;
    clientSecret?: string;
    redirectUris?: string[];
    enabled?: boolean;
  };
  try {
    const provider = await adminUpsertProjectProvider(project.orgId, projectId, {
      provider: body.provider ?? "",
      clientId: body.clientId ?? "",
      clientSecret: body.clientSecret,
      redirectUris: body.redirectUris ?? [],
      enabled: body.enabled,
    });
    return NextResponse.json({ provider });
  } catch (error) {
    const { error: message, status } = adminErrorPayload(error);
    return NextResponse.json({ error: message }, { status });
  }
}

export const runtime = "nodejs";
