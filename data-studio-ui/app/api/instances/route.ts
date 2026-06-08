import { NextResponse } from "next/server";
import { createInstance, listInstances } from "@/lib/instances-store";
import type { CreateInstanceInput } from "@/lib/types";

export async function GET() {
  const instances = listInstances("default");
  return NextResponse.json({ instances });
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as CreateInstanceInput;
    if (!body.name?.trim()) {
      return NextResponse.json({ error: "name is required" }, { status: 400 });
    }
    const instance = createInstance({
      name: body.name.trim(),
      orgId: body.orgId ?? "default",
      deploymentMode: body.deploymentMode,
    });
    return NextResponse.json({ instance }, { status: 201 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to create instance";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
