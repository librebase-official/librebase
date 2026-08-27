import { NextResponse } from "next/server";
import { resolveAccessLogPath, readAccessLogTail } from "@/lib/access-log";
import { aggregateLogs, statCards, rangeFromId } from "@/lib/analytics";
import { resolveStudioOrgId } from "@/lib/org-context";
import { getProjectAsync, listProjects } from "@/lib/projects-store";
import {
  initAnalyticsSchema,
  runtimeTotals,
  runtimeCounts,
} from "@/lib/analytics-store";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  const orgId = await resolveStudioOrgId();
  const { searchParams } = new URL(request.url);
  const projectId = searchParams.get("projectId") ?? null;
  const rangeId = searchParams.get("range") ?? "24h";
  const sinceMs = rangeFromId(rangeId);

  // Resolve a runtime to back the analytics. Prefer the requested project; on
  // the org-level view fall back to the first project in the org.
  let runtimeProjectId = projectId;
  if (!runtimeProjectId) {
    const projects = listProjects(orgId);
    runtimeProjectId = projects[0]?.id ?? null;
  }
  const runtimeProject = runtimeProjectId
    ? await getProjectAsync(runtimeProjectId)
    : undefined;

  // 1. Request traffic from the access-log JSONL (source of truth for logs).
  const filePath = resolveAccessLogPath();
  const lines = filePath ? readAccessLogTail(filePath, 5000) : [];
  const logStats = aggregateLogs(lines, sinceMs);
  const cards = statCards(logStats);

  // 2. Persisted events/todos from Librebase's own runtime Postgres (optional).
  let runtime: {
    ok: boolean;
    message?: string;
    totals: { events: number; todos: number; doneTodos: number };
    counts: { byKind: Record<string, number>; errors: number; logins: number };
  } = {
    ok: false,
    message: runtimeProjectId
      ? "Runtime not reachable; analytics are log-derived."
      : "No runtime selected; analytics are log-derived.",
    totals: { events: 0, todos: 0, doneTodos: 0 },
    counts: { byKind: {}, errors: 0, logins: 0 },
  };
  if (runtimeProjectId) {
    await initAnalyticsSchema(runtimeProjectId);
    const [totals, counts] = await Promise.all([
      runtimeTotals(runtimeProjectId),
      runtimeCounts(runtimeProjectId),
    ]);
    runtime = {
      ok: totals.ok && counts.ok,
      message:
        totals.ok && counts.ok ? undefined : runtime.message,
      totals: totals.data,
      counts: counts.data,
    };
  }

  return NextResponse.json({
    ok: true,
    orgId,
    projectId: runtimeProjectId,
    runtimeProjectName: runtimeProject?.name ?? null,
    rangeId,
    sinceMs,
    runtime,
    stats: {
      total: logStats.total,
      errors: logStats.errors,
      logins: logStats.logins,
      byKind: logStats.byKind,
      byStatus: logStats.byStatus,
    },
    cards,
  });
}
