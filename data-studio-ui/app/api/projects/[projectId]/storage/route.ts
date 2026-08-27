import { NextResponse } from "next/server";
import { probeNamedSurface } from "@/lib/runtime-client";

interface RouteParams {
  params: Promise<{ projectId: string }>;
}

export async function GET(_request: Request, { params }: RouteParams) {
  const result = await probeNamedSurface((await params).projectId, [
    "/storage/v1/bucket",
    "/storage/v1",
  ]);
  return NextResponse.json(result);
}
