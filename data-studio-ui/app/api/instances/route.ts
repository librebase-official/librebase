import { NextResponse } from "next/server";
import { requireEntitlement } from "@/lib/entitlements";
import { provisionDedicatedInstance } from "@/lib/k8s-provisioner";
import { createInstanceAsync, listInstancesAsync } from "@/lib/instances-store";
import { resolveStudioOrgId } from "@/lib/org-context";
import { getLibrebaseRuntime } from "@/lib/runtime-env";
import type { CreateInstanceInput } from "@/lib/types";

export async function GET() {
  const orgId = await resolveStudioOrgId();
  const instances = await listInstancesAsync(orgId);
  return NextResponse.json({
    instances,
    orgId,
    defaultRuntime: getLibrebaseRuntime(),
  });
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as CreateInstanceInput;
    if (!body.name?.trim()) {
      return NextResponse.json({ error: "name is required" }, { status: 400 });
    }

    const orgId = body.orgId ?? (await resolveStudioOrgId());
    await requireEntitlement("instance.launch", orgId);

    const instance = await createInstanceAsync({
      name: body.name.trim(),
      orgId,
      deploymentMode: body.deploymentMode,
      runtime: body.runtime,
      hostId: body.hostId,
      memLimitMb: body.memLimitMb,
    });

    let provision:
      | { ok: boolean; degraded: boolean; message: string; namespace?: string }
      | undefined;
    if (instance.runtimeTarget === "kubernetes") {
      await requireEntitlement("k8s.provision", orgId);
      provision = provisionDedicatedInstance(instance);
    }

    return NextResponse.json({ instance, provision }, { status: 201 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to create instance";
    const status = message.includes("entitlement") ? 403 : 500;
    return NextResponse.json({ error: message }, { status });
  }
}
