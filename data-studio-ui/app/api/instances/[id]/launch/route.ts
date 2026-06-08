import { NextResponse } from "next/server";
import { getInstance } from "@/lib/instances-store";
import { launchInstanceDb } from "@/lib/project-runtime";

interface RouteParams {
  params: Promise<{ id: string }>;
}

export async function POST(_request: Request, { params }: RouteParams) {
  const { id } = await params;
  const instance = getInstance(id);
  if (!instance) {
    return NextResponse.json({ error: "Instance not found" }, { status: 404 });
  }

  const result = await launchInstanceDb(id);
  const updated = getInstance(id);

  return NextResponse.json({
    instance: updated,
    ok: result.ok,
    probe: result.probe,
    message: result.launchMessage,
  });
}
