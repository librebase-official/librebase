import { NextResponse } from "next/server";
import { getInstanceStatus } from "@/lib/k8s-provisioner";
import { getInstance } from "@/lib/instances-store";
import { probeInstanceDb } from "@/lib/project-runtime";

interface RouteParams {
  params: Promise<{ id: string }>;
}

export async function GET(_request: Request, { params }: RouteParams) {
  const { id } = await params;
  const instance = getInstance(id);
  if (!instance) {
    return NextResponse.json({ error: "Instance not found" }, { status: 404 });
  }

  const probe = await probeInstanceDb(instance);
  const k8s =
    instance.runtimeTarget === "kubernetes" ? getInstanceStatus(id) : undefined;

  return NextResponse.json({ instance, probe, k8s });
}
