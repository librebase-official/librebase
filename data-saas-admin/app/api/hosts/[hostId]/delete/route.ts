import { NextResponse } from "next/server";

const ADMIN_API = process.env.ADMIN_API_URL || "http://127.0.0.1:54330";
const ADMIN_TOKEN = process.env.LIBREBASE_ADMIN_DASHBOARD_TOKEN || "";

export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ hostId: string }> },
) {
  const { hostId } = await params;
  const res = await fetch(`${ADMIN_API}/admin/v1/hosts/${hostId}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${ADMIN_TOKEN}` },
  });
  return NextResponse.json(await res.json(), { status: res.status });
}
