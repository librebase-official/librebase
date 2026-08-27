import { NextResponse } from "next/server";
import { requireEntitlement } from "@/lib/entitlements";
import { createProjectAsync, listProjectsAsync } from "@/lib/projects-store";
import { resolveStudioOrgId } from "@/lib/org-context";
import { getLibrebaseRuntime, isSaasHarness } from "@/lib/runtime-env";
import { AdminApiError } from "@/lib/librebase-admin-client";
import type { CreateProjectInput } from "@/lib/types";

export async function GET() {
  try {
    const orgId = await resolveStudioOrgId();
    const projects = await listProjectsAsync(orgId);
    return NextResponse.json({ projects, orgId });
  } catch (error) {
    if (error instanceof AdminApiError) {
      return NextResponse.json(
        { error: error.message, projects: [] },
        { status: error.status },
      );
    }
    const msg = error instanceof Error ? error.message : "failed to load projects";
    const status = msg.includes("401") || msg.includes("unauthorized") ? 401 : 500;
    return NextResponse.json({ error: msg, projects: [] }, { status });
  }
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as CreateProjectInput;
    if (!body.name?.trim()) {
      return NextResponse.json({ error: "name is required" }, { status: 400 });
    }

    const runtimeChoice = body.runtimeChoice ?? "new";
    if (runtimeChoice === "existing" && !body.instanceId) {
      return NextResponse.json(
        { error: "instanceId is required for existing runtime" },
        { status: 400 },
      );
    }

    if (isSaasHarness() && body.runtime === "kubernetes") {
      return NextResponse.json(
        {
          error:
            "Kubernetes is OSS-only. SaaS provisions Hetzner VMs — use runtime local or set LIBREBASE_HARNESS=oss.",
        },
        { status: 400 },
      );
    }

    const orgId = body.orgId ?? (await resolveStudioOrgId());
    await requireEntitlement("project.create", orgId);

    const result = await createProjectAsync({
      name: body.name.trim(),
      orgId,
      region: body.region ?? "local",
      runtimeChoice,
      instanceId: body.instanceId,
      runtime: body.runtime,
      hostId: body.hostId,
      memLimitMb: body.memLimitMb,
    });

    return NextResponse.json(
      { ...result, defaultRuntime: getLibrebaseRuntime() },
      { status: 201 },
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to create project";
    const status = message.includes("entitlement") ? 403 : 400;
    return NextResponse.json({ error: message }, { status });
  }
}
