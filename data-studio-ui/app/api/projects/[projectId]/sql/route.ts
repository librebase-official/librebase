import { NextResponse } from "next/server";
import { executeSql } from "@/lib/runtime-client";
import { probeProjectDb } from "@/lib/project-runtime";

interface RouteParams {
  params: Promise<{ projectId: string }>;
}

export async function POST(request: Request, { params }: RouteParams) {
  const { projectId } = await params;
  const probe = await probeProjectDb(projectId);
  if (!probe.reachable) {
    return NextResponse.json(
      { ok: false, error: "Project is paused", probe },
      { status: 409 },
    );
  }
  const body = (await request.json()) as { sql?: string };
  if (!body.sql?.trim()) {
    return NextResponse.json({ error: "sql is required" }, { status: 400 });
  }
  const result = await executeSql(projectId, body.sql.trim());
  return NextResponse.json(result, { status: result.ok ? 200 : 502 });
}
