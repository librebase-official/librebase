import { NextResponse } from "next/server";
import { adminApiEnabled, adminGetBilling, adminMe } from "@/lib/librebase-admin-client";

export async function GET() {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  try {
    const me = await adminMe();
    const billing = await adminGetBilling(me.activeOrgId);
    return NextResponse.json(billing);
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "billing unavailable" },
      { status: 401 },
    );
  }
}
