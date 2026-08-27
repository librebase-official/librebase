import { NextResponse } from "next/server";
import { checkEntitlement, EntitlementError, requireEntitlement } from "@/lib/entitlements";
import { createHostAsync, listHostsAsync } from "@/lib/hosts-store";
import { resolveStudioOrgId } from "@/lib/org-context";
import { AdminApiError } from "@/lib/librebase-admin-client";
import type { CreateHostInput } from "@/lib/types";

export async function GET() {
  try {
    const orgId = await resolveStudioOrgId();
    const hosts = await listHostsAsync(orgId);
    const canCreate = await checkEntitlement("host.create", orgId);
    return NextResponse.json({ hosts, orgId, canCreate });
  } catch (error) {
    if (error instanceof AdminApiError) {
      return NextResponse.json({ error: error.message, hosts: [] }, { status: error.status });
    }
    const msg = error instanceof Error ? error.message : "failed to load hosts";
    const status = msg.includes("unauthorized") || msg.includes("401") ? 401 : 500;
    return NextResponse.json({ error: msg, hosts: [] }, { status });
  }
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
    if (error instanceof AdminApiError) {
      const msg =
        typeof error.body === "object" && error.body !== null && "error" in error.body
          ? String((error.body as { error: unknown }).error)
          : error.message;
      return NextResponse.json({ error: msg }, { status: error.status });
    }
    if (error instanceof EntitlementError) {
      return NextResponse.json(
        {
          error: "Renting a VM requires a paid plan. Open Admin to upgrade.",
          code: error.featureKey,
        },
        { status: 403 },
      );
    }
    const message = error instanceof Error ? error.message : "Failed to create host";
    const status = message.includes("entitlement") ? 403 : 500;
    return NextResponse.json({ error: message }, { status });
  }
}
