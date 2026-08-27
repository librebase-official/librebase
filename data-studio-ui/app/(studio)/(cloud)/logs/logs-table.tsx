"use client";

import { useMemo, useState } from "react";
import { EmptyState } from "@/components/studio/EmptyState";
import { IconLogs } from "@/components/studio/icons";
import { classifyLogPath, type LogKind } from "@/lib/log-classify";
import type { AccessLogLine } from "@/lib/access-log";

const KINDS: { id: LogKind | "all"; label: string }[] = [
  { id: "all", label: "All" },
  { id: "api", label: "API" },
  { id: "postgres", label: "Postgres" },
  { id: "auth", label: "Auth" },
  { id: "storage", label: "Storage" },
  { id: "edge", label: "Edge" },
  { id: "realtime", label: "Realtime" },
];

const RANGES = [
  { id: "60", label: "Last 60 minutes", ms: 60 * 60 * 1000 },
  { id: "24h", label: "Last 24 hours", ms: 24 * 60 * 60 * 1000 },
  { id: "all", label: "All time", ms: 0 },
];

export function LogsTable({
  lines,
  source,
}: {
  lines: AccessLogLine[];
  source: string | null;
}) {
  const [kind, setKind] = useState<LogKind | "all">("all");
  const [range, setRange] = useState("60");

  const visible = useMemo(() => {
    const since = RANGES.find((r) => r.id === range)?.ms ?? 0;
    const cutoff = since ? Date.now() - since : 0;
    return lines.filter((line) => {
      if (kind !== "all" && classifyLogPath(line.path) !== kind) return false;
      if (cutoff && line.ts) {
        const t = Date.parse(line.ts);
        if (!Number.isNaN(t) && t < cutoff) return false;
      }
      return true;
    });
  }, [lines, kind, range]);

  return (
    <>
      <div className="st-toolbar">
        <select className="select" style={{ maxWidth: 200 }} value={range} onChange={(e) => setRange(e.target.value)}>
          {RANGES.map((r) => (
            <option key={r.id} value={r.id}>
              {r.label}
            </option>
          ))}
        </select>
        <div className="flex-gap" style={{ flexWrap: "wrap" }}>
          {KINDS.map((k) => (
            <button
              key={k.id}
              type="button"
              className={`btn btn-sm ${kind === k.id ? "btn-primary" : "btn-ghost"}`}
              onClick={() => setKind(k.id)}
            >
              {k.label}
            </button>
          ))}
        </div>
      </div>
      <p className="muted text-sm mb-2">
        Source: {source ? <code>{source}</code> : "not configured"}
      </p>
      {visible.length === 0 ? (
        <EmptyState
          icon={<IconLogs />}
          title="No log lines match"
          body="Traffic through the API lands here as JSONL. Filters never invent rows."
        />
      ) : (
        <div className="st-panel" style={{ overflow: "auto" }}>
          <table className="table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Method</th>
                <th>Path</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((l, i) => (
                <tr key={`${l.ts ?? "row"}-${i}`}>
                  <td className="mono">{l.ts ?? "—"}</td>
                  <td>{classifyLogPath(l.path)}</td>
                  <td>{l.method ?? "—"}</td>
                  <td className="mono">{l.path ?? l.raw}</td>
                  <td>{l.status ?? ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
