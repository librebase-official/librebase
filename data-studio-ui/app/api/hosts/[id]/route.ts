import { NextResponse } from "next/server";
import { adminErrorPayload } from "@/lib/librebase-admin-client";
import { deleteHostAsync, getHostAsync } from "@/lib/hosts-store";

interface RouteParams {
  params: Promise<{ id: string }>;
}

export async function DELETE(_request: Request, { params }: RouteParams) {
  const { id } = await params;
  const host = await getHostAsync(id);
  if (!host) {
    return NextResponse.json({ error: "Host not found" }, { status: 404 });
  }
  try {
    await deleteHostAsync(id, host.orgId);
    return NextResponse.json({ ok: true });
  } catch (error) {
    const { error: message, status } = adminErrorPayload(error, "Delete failed");
    return NextResponse.json({ error: message }, { status });
  }
}
