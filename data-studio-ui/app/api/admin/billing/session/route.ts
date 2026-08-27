import { NextResponse } from "next/server";
import { adminApiEnabled, adminCreateBillingSession, adminMe } from "@/lib/librebase-admin-client";

const PLANS = new Set(["starter", "pro", "scale"]);

export async function POST(request: Request) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const body = (await request.json().catch(() => ({}))) as { plan?: string };
  const plan = (body.plan ?? "").trim().toLowerCase();
  if (!PLANS.has(plan)) {
    return NextResponse.json({ error: "plan must be starter, pro, or scale" }, { status: 400 });
  }
  try {
    const me = await adminMe();
    const session = await adminCreateBillingSession(
      me.activeOrgId,
      plan as "starter" | "pro" | "scale",
    );
    return NextResponse.json(session);
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "checkout failed" },
      { status: 502 },
    );
  }
}
