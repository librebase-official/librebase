"use client";

import { useEffect, useState } from "react";
import { EmptyState } from "@/components/studio/EmptyState";
import { IconChart } from "@/components/studio/icons";

export type StatCard = {
  label: string;
  value: number;
  sub?: string;
  kind: "info" | "warn" | "error" | "accent";
};

type StatsPayload = {
  ok: boolean;
  orgId: string;
  projectId?: string | null;
  runtimeProjectName?: string | null;
  rangeId: string;
  stats: {
    total: number;
    errors: number;
    logins: number;
    byKind: Record<string, number>;
    byStatus: Record<string, number>;
  };
  cards: StatCard[];
  runtime: {
    ok: boolean;
    message?: string;
    totals: { events: number; todos: number; doneTodos: number };
    counts: { byKind: Record<string, number>; errors: number; logins: number };
  };
};

const RANGES = [
  { id: "60m", label: "60 min" },
  { id: "24h", label: "24h" },
  { id: "7d", label: "7d" },
  { id: "all", label: "All" },
];

export function AnalyticsDashboard({
  projectId,
  className,
}: {
  projectId?: string;
  className?: string;
}) {
  const [data, setData] = useState<StatsPayload | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [range, setRange] = useState("24h");

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const qs = new URLSearchParams();
    if (projectId) qs.set("projectId", projectId);
    qs.set("range", range);
    fetch(`/api/analytics/stats?${qs.toString()}`)
      .then((r) => r.json())
      .then((j: StatsPayload) => {
        if (!cancelled) setData(j);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, range]);

  const CARD_KIND_CLASS: Record<StatCard["kind"], string> = {
    info: "stat-card info",
    warn: "stat-card warn",
    error: "stat-card error",
    accent: "stat-card accent",
  };

  // Initial load: show spinner without flickering the whole page on subsequent range changes.
  if (!data) {
    return (
      <div className={`analytics-dashboard ${className ?? ""}`}>
        <div className="st-toolbar">
          <select
            className="select"
            style={{ maxWidth: 200 }}
            value={range}
            onChange={(e) => setRange(e.target.value)}
          >
            {RANGES.map((r) => (
              <option key={r.id} value={r.id}>
                {r.label}
              </option>
            ))}
          </select>
          {loading ? <span className="spinner" style={{ width: 14, height: 14 }} aria-label="Loading" /> : null}
        </div>
        <p className="muted text-sm">Loading analytics…</p>
      </div>
    );
  }

  if (!data.ok) {
    return (
      <EmptyState
        icon={<IconChart />}
        title="Analytics unavailable"
        body="The control plane didn't return stats."
      />
    );
  }

  const { stats, runtime } = data;
  const kinds = Object.entries(stats.byKind).sort((a, b) => b[1] - a[1]);
  const statuses = Object.entries(stats.byStatus).sort(
    (a, b) => Number(b[0]) - Number(a[0]),
  );
  const runtimeKinds = Object.entries(runtime.counts.byKind).sort(
    (a, b) => b[1] - a[1],
  );

  return (
    <div className={`analytics-dashboard ${className ?? ""}`}>
      <div className="st-toolbar">
        <select
          className="select"
          style={{ maxWidth: 200 }}
          value={range}
          onChange={(e) => setRange(e.target.value)}
        >
          {RANGES.map((r) => (
            <option key={r.id} value={r.id}>
              {r.label}
            </option>
          ))}
        </select>
        {loading ? <span className="spinner" style={{ width: 14, height: 14 }} aria-label="Loading" /> : null}
      </div>

      <div className="stat-cards">
        {data.cards.map((c) => (
          <div key={c.label} className={CARD_KIND_CLASS[c.kind]}>
            <div className="stat-card-value">{c.value}</div>
            <div className="stat-card-label">{c.label}</div>
            {c.sub ? <div className="stat-card-sub">{c.sub}</div> : null}
          </div>
        ))}
      </div>

      <div className="stat-panels">
        <div className="st-panel">
          <h3 className="section-title">By kind</h3>
          {kinds.length === 0 ? (
            <p className="muted text-sm">No requests in this window.</p>
          ) : (
            <ul className="stat-list">
              {kinds.map(([k, v]) => (
                <li key={k} className="stat-list-row">
                  <span>{k}</span>
                  <strong>{v}</strong>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="st-panel">
          <h3 className="section-title">By status</h3>
          {statuses.length === 0 ? (
            <p className="muted text-sm">No responses recorded.</p>
          ) : (
            <ul className="stat-list">
              {statuses.map(([s, v]) => (
                <li key={s} className="stat-list-row">
                  <span>{s}</span>
                  <strong>{v}</strong>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      <div className="st-panel">
        <h3 className="section-title">Librebase runtime</h3>
        {!runtime.ok && runtime.message ? (
          <p className="muted text-sm">{runtime.message}</p>
        ) : null}
        {data.runtimeProjectName ? (
          <p className="muted text-sm">
            Backed by project <strong>{data.runtimeProjectName}</strong> (Librebase
            runtime Postgres).
          </p>
        ) : null}
        <ul className="stat-list">
          <li className="stat-list-row">
            <span>Recorded events</span>
            <strong>{runtime.totals.events}</strong>
          </li>
          <li className="stat-list-row">
            <span>Todos (agent)</span>
            <strong>{runtime.totals.todos}</strong>
          </li>
          <li className="stat-list-row">
            <span>Completed agent runs</span>
            <strong>{runtime.totals.doneTodos}</strong>
          </li>
        </ul>
        {runtimeKinds.length > 0 ? (
          <h4 className="section-title" style={{ marginTop: "0.75rem" }}>
            Events by kind
          </h4>
        ) : null}
        <ul className="stat-list">
          {runtimeKinds.map(([k, v]) => (
            <li key={k} className="stat-list-row">
              <span>{k}</span>
              <strong>{v}</strong>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
