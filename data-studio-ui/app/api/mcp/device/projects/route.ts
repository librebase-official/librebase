import { NextResponse } from "next/server";
import {
  adminApiEnabled,
  adminErrorPayload,
  adminListProjects,
} from "@/lib/librebase-admin-client";

export async function GET(request: Request) {
  if (!adminApiEnabled()) {
    return NextResponse.json({ error: "Admin API disabled" }, { status: 503 });
  }
  const orgId = new URL(request.url).searchParams.get("orgId") ?? "";
  if (!orgId.trim()) {
    return NextResponse.json({ error: "orgId required" }, { status: 400 });
  }
  try {
    const projects = await adminListProjects(orgId.trim());
    return NextResponse.json({ projects });
  } catch (error) {
    const { error: message, status } = adminErrorPayload(
      error,
      "list projects failed",
    );
    return NextResponse.json({ error: message, projects: [] }, { status });
  }
}

export const runtime = "nodejs";