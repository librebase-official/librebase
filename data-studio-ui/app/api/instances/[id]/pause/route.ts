import { NextResponse } from "next/server";
import { getInstanceAsync } from "@/lib/instances-store";
import { pauseInstanceDb } from "@/lib/project-runtime";

interface RouteParams {
  params: Promise<{ id: string }>;
}

export async function POST(_request: Request, { params }: RouteParams) {
  const { id } = await params;
  const instance = await getInstanceAsync(id);
  if (!instance) {
    return NextResponse.json({ error: "Instance not found" }, { status: 404 });
  }
  const result = await pauseInstanceDb(id);
  const updated = await getInstanceAsync(id, instance.orgId);
  return NextResponse.json({
    instance: updated,
    ok: result.ok,
    probe: result.probe,
    message: result.message,
  });
}
