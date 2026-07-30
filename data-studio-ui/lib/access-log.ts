import fs from "node:fs";
import os from "node:os";
import path from "node:path";

export type AccessLogLine = {
  raw: string;
  ts?: string;
  method?: string;
  path?: string;
  status?: number;
  event?: string;
};

/** Resolve JSONL access log path (lis registry audit or Librebase override). */
export function resolveAccessLogPath(): string | null {
  const explicit =
    process.env.LIBREBASE_ACCESS_LOG ??
    process.env.LIP_REGISTRY_AUDIT_LOG ??
    "";
  if (explicit.trim()) return explicit.trim();

  const dataDir =
    process.env.LI_DATA_DIR ??
    path.join(os.homedir(), ".local", "share", "lis", "data");
  const candidate = path.join(dataDir, "logs", "access.jsonl");
  if (fs.existsSync(candidate)) return candidate;
  return null;
}

export function parseAccessLogLine(line: string): AccessLogLine {
  const trimmed = line.trim();
  if (!trimmed) return { raw: line };
  try {
    const row = JSON.parse(trimmed) as Record<string, unknown>;
    return {
      raw: trimmed,
      ts: typeof row.ts === "string" ? row.ts : undefined,
      method: typeof row.method === "string" ? row.method : undefined,
      path: typeof row.path === "string" ? row.path : undefined,
      status: typeof row.status === "number" ? row.status : undefined,
      event: typeof row.event === "string" ? row.event : undefined,
    };
  } catch {
    return { raw: trimmed };
  }
}

/** Tail last N non-empty lines from a JSONL access log (newest last). */
export function readAccessLogTail(
  filePath: string,
  limit = 100,
): AccessLogLine[] {
  if (!fs.existsSync(filePath)) return [];
  const text = fs.readFileSync(filePath, "utf8");
  const lines = text.split(/\r?\n/).filter((l) => l.trim().length > 0);
  return lines.slice(-limit).map(parseAccessLogLine);
}
