import { NextResponse } from "next/server";
import { adminErrorPayload } from "@/lib/librebase-admin-client";
import { deleteInstanceAsync, getInstanceAsync } from "@/lib/instances-store";

interface RouteParams {
  params: Promise<{ id: string }>;
}

export async function DELETE(_request: Request, { params }: RouteParams) {
  const { id } = await params;
  const instance = await getInstanceAsync(id);
  if (!instance) {
    return NextResponse.json({ error: "Instance not found" }, { status: 404 });
  }
  try {
    await deleteInstanceAsync(id, instance.orgId);
    return NextResponse.json({ ok: true });
  } catch (error) {
    const { error: message, status } = adminErrorPayload(error, "Delete failed");
    return NextResponse.json({ error: message }, { status });
  }
}