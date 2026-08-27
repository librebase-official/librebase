import { NextResponse } from "next/server";
import {
  adminApiEnabled,
  adminCreateOrg,
  adminMe,
  adminUpdateOrg,
} from "@/lib/librebase-admin-client";

export async function GET() {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  try {
    const me = await adminMe();
    return NextResponse.json({
      activeOrgId: me.activeOrgId,
      memberships: me.memberships,
      role: me.role,
    });
  } catch (e) {
    return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  }
}

export async function PATCH(request: Request) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const body = (await request.json().catch(() => ({}))) as {
    orgId?: string;
    name?: string;
  };
  if (!body.orgId || !body.name || !body.name.trim()) {
    return NextResponse.json({ error: "orgId and name required" }, { status: 400 });
  }
  try {
    const org = await adminUpdateOrg(body.orgId, { name: body.name.trim() });
    return NextResponse.json({ org });
  } catch {
    return NextResponse.json({ error: "rename failed" }, { status: 400 });
  }
}

export async function POST(request: Request) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const body = (await request.json().catch(() => ({}))) as { name?: string };
  if (!body.name || !body.name.trim()) {
    return NextResponse.json({ error: "name required" }, { status: 400 });
  }
  try {
    const org = await adminCreateOrg({ name: body.name });
    const me = org && (await adminMe().catch(() => null));
    return NextResponse.json({
      orgId: org?.id,
      name: org?.name,
      memberships: me?.memberships ?? [],
    });
  } catch (e) {
    const m = e instanceof Error ? e.message : "create failed";
    return NextResponse.json({ error: m }, { status: m.includes("409") ? 409 : 500 });
  }
}
