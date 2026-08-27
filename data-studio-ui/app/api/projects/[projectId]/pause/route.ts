import { NextResponse } from "next/server";
import { getProjectAsync } from "@/lib/projects-store";
import { pauseProjectDb } from "@/lib/project-runtime";

interface RouteParams {
  params: Promise<{ projectId: string }>;
}

export async function POST(_request: Request, { params }: RouteParams) {
  const { projectId } = await params;
  const project = await getProjectAsync(projectId);
  if (!project) {
    return NextResponse.json({ error: "Project not found" }, { status: 404 });
  }
  const result = await pauseProjectDb(projectId);
  return NextResponse.json({
    project,
    ok: result.ok,
    probe: result.probe,
    message: result.message,
  });
}
