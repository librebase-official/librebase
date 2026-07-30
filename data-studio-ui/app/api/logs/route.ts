import { NextResponse } from "next/server";
import { readAccessLogTail, resolveAccessLogPath } from "@/lib/access-log";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const limit = Math.min(
    500,
    Math.max(1, Number(url.searchParams.get("limit") ?? "100") || 100),
  );
  const filePath = resolveAccessLogPath();
  if (!filePath) {
    return NextResponse.json({
      ok: true,
      path: null,
      lines: [],
      note: "No access log configured — set LIBREBASE_ACCESS_LOG or LIP_REGISTRY_AUDIT_LOG",
    });
  }
  const lines = readAccessLogTail(filePath, limit);
  return NextResponse.json({ ok: true, path: filePath, lines });
}
