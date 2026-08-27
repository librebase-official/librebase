import { NextResponse } from "next/server";
import { getAuthSettings, saveAuthSettings } from "@/lib/auth-settings-store";
import { getProjectAsync } from "@/lib/projects-store";

interface RouteParams {
  params: Promise<{ projectId: string }>;
}

export async function GET(_request: Request, { params }: RouteParams) {
  const { projectId } = await params;
  if (!(await getProjectAsync(projectId))) {
    return NextResponse.json({ error: "Project not found" }, { status: 404 });
  }
  return NextResponse.json({ settings: getAuthSettings(projectId) });
}

export async function PATCH(request: Request, { params }: RouteParams) {
  const { projectId } = await params;
  if (!(await getProjectAsync(projectId))) {
    return NextResponse.json({ error: "Project not found" }, { status: 404 });
  }
  const body = (await request.json()) as Record<string, unknown>;
  const settings = saveAuthSettings(projectId, body);
  return NextResponse.json({ settings });
}
