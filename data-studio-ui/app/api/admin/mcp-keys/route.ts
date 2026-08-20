import { NextResponse } from "next/server";
import {
  adminApiEnabled,
  adminIssueMcpKey,
  adminListMcpKeys,
} from "@/lib/librebase-admin-client";

function err(message: string, status: number) {
  return NextResponse.json({ error: message }, { status });
}

export async function GET(request: Request) {
  if (!adminApiEnabled()) return err("Admin API disabled", 503);
  const orgId = new URL(request.url).searchParams.get("orgId") ?? "";
  if (!orgId) return err("orgId required", 400);
  try {
    return NextResponse.json(await adminListMcpKeys(orgId));
  } catch (e) {
    return err(e instanceof Error ? e.message : "failed", 500);
  }
}

export async function POST(request: Request) {
  if (!adminApiEnabled()) return err("Admin API disabled", 503);
  const body = (await request.json().catch(() => ({}))) as {
    orgId?: string;
    rotate?: boolean;
    label?: string;
  };
  if (!body.orgId) return err("orgId required", 400);
  try {
    return NextResponse.json(
      await adminIssueMcpKey(body.orgId, {
        rotate: body.rotate ?? true,
        label: body.label,
      }),
    );
  } catch (e) {
    return err(e instanceof Error ? e.message : "failed", 500);
  }
}
