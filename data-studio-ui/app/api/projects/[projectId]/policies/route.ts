import { NextResponse } from "next/server";
import { listPolicies } from "@/lib/runtime-client";

interface RouteParams {
  params: Promise<{ projectId: string }>;
}

export async function GET(_request: Request, { params }: RouteParams) {
  const result = await listPolicies((await params).projectId);
  return NextResponse.json(result);
}
