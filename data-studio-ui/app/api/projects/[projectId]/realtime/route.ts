import { NextResponse } from "next/server";
import { listRealtime } from "@/lib/runtime-client";

interface RouteParams {
  params: Promise<{ projectId: string }>;
}

export async function GET(_request: Request, { params }: RouteParams) {
  const result = await listRealtime((await params).projectId);
  return NextResponse.json(result);
}
