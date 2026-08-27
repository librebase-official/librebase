import { NextResponse } from "next/server";
import { createAuthUser, listAuthUsers } from "@/lib/runtime-client";
import { probeProjectDb } from "@/lib/project-runtime";

interface RouteParams {
  params: Promise<{ projectId: string }>;
}

export async function GET(_request: Request, { params }: RouteParams) {
  const { projectId } = await params;
  const result = await listAuthUsers(projectId);
  return NextResponse.json(result);
}

export async function POST(request: Request, { params }: RouteParams) {
  const { projectId } = await params;
  const probe = await probeProjectDb(projectId);
  if (!probe.reachable) {
    return NextResponse.json({ error: "Project is paused" }, { status: 409 });
  }
  const body = (await request.json()) as { email?: string; password?: string };
  if (!body.email?.trim() || !body.password) {
    return NextResponse.json({ error: "email and password required" }, { status: 400 });
  }
  const result = await createAuthUser(projectId, {
    email: body.email.trim(),
    password: body.password,
  });
  return NextResponse.json(result, { status: result.ok ? 201 : 502 });
}
