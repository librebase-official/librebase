import { NextResponse } from "next/server";
import { adminErrorPayload } from "@/lib/librebase-admin-client";
import {
  deleteProjectAsync,
  getProjectAsync,
  updateProjectAsync,
} from "@/lib/projects-store";
import { getProjectUrlsAsync, probeProjectDb } from "@/lib/project-runtime";

interface RouteParams {
  params: Promise<{ projectId: string }>;
}

export async function GET(_request: Request, { params }: RouteParams) {
  const { projectId } = await params;
  const project = await getProjectAsync(projectId);
  if (!project) {
    return NextResponse.json({ error: "Project not found" }, { status: 404 });
  }
  const probe = await probeProjectDb(projectId);
  const urls = await getProjectUrlsAsync(project);
  return NextResponse.json({ project, probe, urls });
}

export async function PATCH(request: Request, { params }: RouteParams) {
  const { projectId } = await params;
  const project = await getProjectAsync(projectId);
  if (!project) {
    return NextResponse.json({ error: "Project not found" }, { status: 404 });
  }
  const body = (await request.json()) as { name?: string };
  try {
    const updated = await updateProjectAsync(projectId, { name: body.name });
    return NextResponse.json({ project: updated });
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Update failed" },
      { status: 400 },
    );
  }
}

export async function DELETE(_request: Request, { params }: RouteParams) {
  const { projectId } = await params;
  const project = await getProjectAsync(projectId);
  if (!project) {
    return NextResponse.json({ error: "Project not found" }, { status: 404 });
  }
  try {
    await deleteProjectAsync(projectId, project.orgId);
    return NextResponse.json({ ok: true });
  } catch (error) {
    const { error: message, status } = adminErrorPayload(error, "Delete failed");
    return NextResponse.json({ error: message }, { status });
  }
}
