import { NextResponse } from "next/server";
import { requireEntitlement } from "@/lib/entitlements";
import { provisionDedicatedInstance } from "@/lib/k8s-provisioner";
import { createInstanceAsync, listInstancesAsync } from "@/lib/instances-store";
import { resolveStudioOrgId } from "@/lib/org-context";
import { getLibrebaseRuntime, isSaasHarness } from "@/lib/runtime-env";
import { AdminApiError } from "@/lib/librebase-admin-client";
import type { CreateInstanceInput } from "@/lib/types";

export async function GET() {
  try {
    const orgId = await resolveStudioOrgId();
    const instances = await listInstancesAsync(orgId);
    return NextResponse.json({
      instances,
      orgId,
      defaultRuntime: getLibrebaseRuntime(),
    });
  } catch (error) {
    if (error instanceof AdminApiError) {
      return NextResponse.json(
        { error: error.message, instances: [], orgId: "default" },
        { status: error.status },
      );
    }
    const msg = error instanceof Error ? error.message : "failed to load instances";
    const status = msg.includes("401") || msg.includes("unauthorized") ? 401 : 500;
    return NextResponse.json({ error: msg, instances: [] }, { status });
  }
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as CreateInstanceInput;
    if (!body.name?.trim()) {
      return NextResponse.json({ error: "name is required" }, { status: 400 });
    }

    const orgId = body.orgId ?? (await resolveStudioOrgId());
    await requireEntitlement("instance.launch", orgId);

    if (isSaasHarness() && body.runtime === "kubernetes") {
      return NextResponse.json(
        {
          error:
            "Kubernetes is OSS-only. This SaaS harness provisions Hetzner VMs — use runtime local + hostId, or set LIBREBASE_HARNESS=oss for your own cluster.",
        },
        { status: 400 },
      );
    }

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
      if (isSaasHarness()) {
        return NextResponse.json(
          {
            error: "Kubernetes is OSS-only in this SaaS harness.",
            instance,
          },
          { status: 400 },
        );
      }
      await requireEntitlement("k8s.provision", orgId);
      provision = provisionDedicatedInstance(instance);
    }

    return NextResponse.json({ instance, provision }, { status: 201 });
  } catch (error) {
    if (error instanceof AdminApiError) {
      const msg =
        typeof error.body === "object" && error.body !== null && "error" in error.body
          ? String((error.body as { error: unknown }).error)
          : error.message;
      return NextResponse.json({ error: msg }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : "Failed to create instance";
    const status = message.includes("entitlement") ? 403 : 500;
    return NextResponse.json({ error: message }, { status });
  }
}
