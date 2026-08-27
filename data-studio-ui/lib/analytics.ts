import { classifyLogPath, type LogKind } from "./log-classify";
import type { AccessLogLine, } from "./access-log";

export type AnalyticEvent = {
  orgId: string;
  projectId?: string | null;
  kind: "request" | "login" | "todo" | "agent_step";
  severity?: "info" | "warn" | "error";
  status?: number | null;
  path?: string | null;
  method?: string | null;
  event?: string | null;
  data?: unknown;
};

export type Todo = {
  id: string;
  orgId: string;
  projectId?: string | null;
  title: string;
  done: boolean;
  createdAt: string;
  completedAt: string | null;
};

export type LogStats = {
  total: number;
  byKind: Record<string, number>;
  byStatus: Record<string, number>;
  errors: number;
  logins: number;
  rangeMs: number;
};

export type StatCard = {
  label: string;
  value: number;
  sub?: string;
  kind: "info" | "warn" | "error" | "accent";
};

/** Derive aggregate analytics from the access-log JSONL (source of truth).
 * Falls back to an empty result when no log sink is configured. */
export function aggregateLogs(
  lines: AccessLogLine[],
  sinceMs: number,
): LogStats {
  const byKind: Record<string, number> = {};
  const byStatus: Record<string, number> = {};
  let errors = 0;
  let logins = 0;
  let total = 0;

  const cutoff = sinceMs ? Date.now() - sinceMs : 0;
  for (const line of lines) {
    if (cutoff && line.ts) {
      const t = Date.parse(line.ts);
      if (!Number.isNaN(t) && t < cutoff) continue;
    }
    total += 1;
    const kind = classifyLogPath(line.path) as LogKind;
    byKind[kind] = (byKind[kind] ?? 0) + 1;
    if (line.status) {
      const bucket = String(line.status);
      byStatus[bucket] = (byStatus[bucket] ?? 0) + 1;
      if (line.status >= 500) errors += 1;
    }
    if (kind === "auth" && (line.path?.startsWith("/auth") || line.path?.includes("/v1/auth"))) {
      logins += 1;
    }
  }

  return {
    total,
    byKind,
    byStatus,
    errors,
    logins,
    rangeMs: sinceMs,
  };
}

const RANGE_PRESETS: { id: string; label: string; ms: number }[] = [
  { id: "60m", label: "Last 60 minutes", ms: 60 * 60 * 1000 },
  { id: "24h", label: "Last 24 hours", ms: 24 * 60 * 60 * 1000 },
  { id: "7d", label: "Last 7 days", ms: 7 * 24 * 60 * 60 * 1000 },
  { id: "all", label: "All time", ms: 0 },
];

export function rangeFromId(id: string): number {
  return RANGE_PRESETS.find((r) => r.id === id)?.ms ?? 60 * 60 * 1000;
}

export function statCards(stats: LogStats): StatCard[] {
  return [
    { label: "Requests", value: stats.total, kind: "info" },
    {
      label: "Errors (5xx)",
      value: stats.errors,
      kind: stats.errors > 0 ? "error" : "info",
    },
    {
      label: "Auth / logins",
      value: stats.logins,
      sub: `${stats.byKind.auth ?? 0} auth reqs`,
      kind: "accent",
    },
    {
      label: "DB traffic",
      value: stats.byKind.postgres ?? 0,
      kind: "info",
    },
  ];
}
