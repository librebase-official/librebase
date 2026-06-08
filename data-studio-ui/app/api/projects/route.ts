import { NextResponse } from "next/server";
import { createProject, listProjects } from "@/lib/projects-store";
import type { CreateProjectInput } from "@/lib/types";

export async function GET() {
  const projects = listProjects("default");
  return NextResponse.json({ projects });
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

    const result = createProject({
      name: body.name.trim(),
      orgId: body.orgId ?? "default",
      region: body.region ?? "local",
      runtimeChoice,
      instanceId: body.instanceId,
    });

    return NextResponse.json(result, { status: 201 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to create project";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
