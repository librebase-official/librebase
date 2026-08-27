import { NextResponse } from "next/server";
import { listTableRows } from "@/lib/runtime-client";
import { probeProjectDb } from "@/lib/project-runtime";

interface RouteParams {
  params: Promise<{ projectId: string; table: string }>;
}

export async function GET(request: Request, { params }: RouteParams) {
  const { projectId, table } = await params;
  const probe = await probeProjectDb(projectId);
  if (!probe.reachable) {
    return NextResponse.json(
      { ok: false, error: "Project is paused", table, columns: [], rows: [] },
      { status: 409 },
    );
  }
  const url = new URL(request.url);
  const limit = Number(url.searchParams.get("limit") ?? "200");
  const schema = url.searchParams.get("schema") ?? "public";
  const result = await listTableRows(projectId, table, { limit, schema });
  return NextResponse.json(result, { status: result.ok ? 200 : 502 });
}
