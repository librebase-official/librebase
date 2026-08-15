import { NextResponse } from "next/server";
import { adminApiEnabled, adminChangePassword } from "@/lib/librebase-admin-client";

export async function POST(request: Request) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const body = (await request.json().catch(() => ({}))) as {
    currentPassword?: string;
    newPassword?: string;
  };
  try {
    const result = await adminChangePassword(
      body.currentPassword ?? "",
      body.newPassword ?? "",
    );
    return NextResponse.json(result);
  } catch (e) {
    const message = e instanceof Error ? e.message : "failed";
    return NextResponse.json({ error: message }, { status: message.includes("401") ? 401 : 500 });
  }
}
