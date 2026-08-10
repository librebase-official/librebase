import { NextResponse } from "next/server";
import { requireEntitlement } from "@/lib/entitlements";
import { createHostAsync, listHostsAsync } from "@/lib/hosts-store";
import { resolveStudioOrgId } from "@/lib/org-context";
import type { CreateHostInput } from "@/lib/types";

export async function GET() {
  const orgId = await resolveStudioOrgId();
  const hosts = await listHostsAsync(orgId);
  return NextResponse.json({ hosts, orgId });
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as CreateHostInput;
    if (!body.name?.trim()) {
      return NextResponse.json({ error: "name is required" }, { status: 400 });
    }

    const orgId = body.orgId ?? (await resolveStudioOrgId());
    await requireEntitlement("host.create", orgId);

    const host = await createHostAsync({
      name: body.name.trim(),
      orgId,
      provider: body.provider,
      region: body.region,
      memMb: body.memMb,
    });

    return NextResponse.json({ host }, { status: 201 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to create host";
    const status = message.includes("entitlement") ? 403 : 500;
    return NextResponse.json({ error: message }, { status });
  }
}
