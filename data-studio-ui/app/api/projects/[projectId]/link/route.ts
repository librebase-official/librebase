import { NextResponse } from "next/server";
import { linkProjectToInstanceAsync } from "@/lib/projects-store";

interface RouteParams {
  params: Promise<{ projectId: string }>;
}

export async function POST(request: Request, { params }: RouteParams) {
  try {
    const { projectId } = await params;
    const body = (await request.json()) as { instanceId?: string };
    if (!body.instanceId?.trim()) {
      return NextResponse.json(
        { error: "instanceId is required" },
        { status: 400 },
      );
    }
    const project = await linkProjectToInstanceAsync(
      projectId,
      body.instanceId.trim(),
    );
    return NextResponse.json({ project }, { status: 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to link database";
    return NextResponse.json({ error: message }, { status: 400 });
  }
}
