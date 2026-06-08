import { NextResponse } from "next/server";
import { getProject } from "@/lib/projects-store";
import { getProjectUrls, launchProjectDb, probeProjectDb } from "@/lib/project-runtime";

interface RouteParams {
  params: Promise<{ id: string }>;
}

export async function GET(_request: Request, { params }: RouteParams) {
  const { id } = await params;
  const project = getProject(id);
  if (!project) {
    return NextResponse.json({ error: "Project not found" }, { status: 404 });
  }

  const probe = await probeProjectDb(id);
  const urls = getProjectUrls(project);

  return NextResponse.json({ project, probe, urls });
}

export async function POST(_request: Request, { params }: RouteParams) {
  const { id } = await params;
  const project = getProject(id);
  if (!project) {
    return NextResponse.json({ error: "Project not found" }, { status: 404 });
  }

  const result = await launchProjectDb(id);
  const urls = getProjectUrls(project);

  return NextResponse.json({
    project,
    ok: result.ok,
    probe: result.probe,
    message: result.launchMessage,
    urls,
  });
}
