import { NextResponse } from "next/server";
import { requireEntitlement } from "@/lib/entitlements";
import { createProjectAsync, listProjectsAsync } from "@/lib/projects-store";
import { resolveStudioOrgId } from "@/lib/org-context";
import { getLibrebaseRuntime } from "@/lib/runtime-env";
import type { CreateProjectInput } from "@/lib/types";

export async function GET() {
  const orgId = await resolveStudioOrgId();
  const projects = await listProjectsAsync(orgId);
  return NextResponse.json({ projects, orgId });
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

    const orgId = body.orgId ?? (await resolveStudioOrgId());
    await requireEntitlement("project.create", orgId);

    const result = await createProjectAsync({
      name: body.name.trim(),
      orgId,
      region: body.region ?? "local",
      runtimeChoice,
      instanceId: body.instanceId,
      runtime: body.runtime,
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
