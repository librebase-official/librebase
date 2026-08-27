import type { AccessLogLine } from "./access-log";

export type LogKind =
  | "api"
  | "postgres"
  | "auth"
  | "storage"
  | "edge"
  | "realtime"
  | "other";

export function classifyLogPath(path?: string): LogKind {
  if (!path) return "other";
  const p = path.toLowerCase();
  if (p.startsWith("/auth") || p.includes("/v1/auth")) return "auth";
  if (p.startsWith("/storage")) return "storage";
  if (p.startsWith("/functions") || p.startsWith("/edge")) return "edge";
  if (p.startsWith("/realtime")) return "realtime";
  if (p.startsWith("/rest") || p.startsWith("/v1/sql") || p.includes("postgres")) {
    return "postgres";
  }
  if (p.startsWith("/v1") || p.startsWith("/api")) return "api";
  return "other";
}

export function filterLogLines(
  lines: AccessLogLine[],
  opts: { kind?: LogKind | "all"; sinceMs?: number },
): AccessLogLine[] {
  return lines.filter((line) => {
    if (opts.kind && opts.kind !== "all" && classifyLogPath(line.path) !== opts.kind) {
      return false;
    }
    if (opts.sinceMs && line.ts) {
      const t = Date.parse(line.ts);
      if (!Number.isNaN(t) && t < opts.sinceMs) return false;
    }
    return true;
  });
}
