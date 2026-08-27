import { NextResponse } from "next/server";
import { adminApiEnabled, adminCreateBillingPortal, adminMe } from "@/lib/librebase-admin-client";

export async function POST() {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  try {
    const me = await adminMe();
    const portal = await adminCreateBillingPortal(me.activeOrgId);
    return NextResponse.json(portal);
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "portal failed" },
      { status: 502 },
    );
  }
}
