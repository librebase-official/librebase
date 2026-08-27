import { NextResponse } from "next/server";
import { getConnectInfo } from "@/lib/runtime-client";

interface RouteParams {
  params: Promise<{ projectId: string }>;
}

export async function GET(_request: Request, { params }: RouteParams) {
  try {
    const info = await getConnectInfo((await params).projectId);
    return NextResponse.json(info);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Not found" },
      { status: 404 },
    );
  }
}
