import { getMcpUsage, adminEnabled } from "@/lib/admin-client";
import { AutoRefresh } from "@/components/AutoRefresh";

export const dynamic = "force-dynamic";

export default async function McpAnalyticsPage() {
  if (!adminEnabled())
    return (
      <div className="admin-header">
        <h1>MCP Analytics</h1>
        <p>Admin token not configured.</p>
      </div>
    );

  let usage;
  try {
    usage = await getMcpUsage();
  } catch (e) {
    return (
      <div className="admin-header">
        <h1>MCP Analytics</h1>
        <p style={{ color: "var(--danger)" }}>
          {e instanceof Error ? e.message : "error"}
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>MCP Analytics</h1>
          <p>
            {usage.totalCalls.toLocaleString()} total calls
            {" · "}
            {usage.callsToday.toLocaleString()} today
          </p>
        </div>
        <AutoRefresh interval={30_000} />
      </div>

      {/* Summary cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: 16,
          marginBottom: 24,
        }}
      >
        <StatCard label="Total Calls" value={usage.totalCalls} />
        <StatCard label="Calls Today" value={usage.callsToday} />
        <StatCard
          label="Unique Orgs"
          value={usage.byOrg.length}
        />
        <StatCard
          label="Tools Used"
          value={usage.byTool.length}
        />
        <StatCard
          label="Total Errors"
          value={usage.byTool.reduce((s, t) => s + (t.errors ?? 0), 0)}
          danger
        />
      </div>

      {/* Tool breakdown */}
      {usage.byTool.length > 0 && (
        <div className="panel" style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 16, margin: "0 0 12px" }}>Tool Usage</h2>
          <table className="table">
            <thead>
              <tr>
                <th>Tool</th>
                <th style={{ textAlign: "right" }}>Calls</th>
                <th style={{ textAlign: "right" }}>Avg Latency</th>
                <th style={{ textAlign: "right" }}>Errors</th>
                <th style={{ textAlign: "right" }}>Error Rate</th>
              </tr>
            </thead>
            <tbody>
              {usage.byTool.map((t) => (
                <tr key={t.tool_name}>
                  <td>
                    <code style={{ fontSize: 13 }}>{t.tool_name}</code>
                  </td>
                  <td style={{ textAlign: "right" }}>{t.cnt.toLocaleString()}</td>
                  <td style={{ textAlign: "right" }}>
                    {t.avg_ms != null ? `${Math.round(t.avg_ms)}ms` : "—"}
                  </td>
                  <td
                    style={{
                      textAlign: "right",
                      color: t.errors > 0 ? "var(--danger)" : undefined,
                    }}
                  >
                    {t.errors ?? 0}
                  </td>
                  <td style={{ textAlign: "right" }}>
                    {t.cnt > 0
                      ? `${(((t.errors ?? 0) / t.cnt) * 100).toFixed(1)}%`
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Hourly trend (last 24h) */}
      {usage.hourly.length > 0 && (
        <div className="panel" style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 16, margin: "0 0 12px" }}>
            Hourly Trend (24h)
          </h2>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: 120 }}>
            {usage.hourly.map((h) => {
              const max = Math.max(...usage.hourly.map((x) => x.cnt), 1);
              const pct = (h.cnt / max) * 100;
              return (
                <div
                  key={h.hour}
                  title={`${h.hour}: ${h.cnt} calls`}
                  style={{
                    flex: 1,
                    minWidth: 8,
                    height: `${Math.max(pct, 4)}%`,
                    background: "var(--accent, #7aa2ff)",
                    borderRadius: 3,
                  }}
                />
              );
            })}
          </div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              fontSize: 11,
              color: "#6b7484",
              marginTop: 4,
            }}
          >
            <span>
              {usage.hourly[0]?.hour?.replace("T", " ").replace("Z", "")}
            </span>
            <span>
              {usage.hourly[usage.hourly.length - 1]?.hour
                ?.replace("T", " ")
                .replace("Z", "")}
            </span>
          </div>
        </div>
      )}

      {/* Per-org usage */}
      {usage.byOrg.length > 0 && (
        <div className="panel">
          <h2 style={{ fontSize: 16, margin: "0 0 12px" }}>Usage by Org</h2>
          <table className="table">
            <thead>
              <tr>
                <th>Org ID</th>
                <th style={{ textAlign: "right" }}>Calls</th>
                <th>Last Call</th>
              </tr>
            </thead>
            <tbody>
              {usage.byOrg.map((o) => (
                <tr key={o.org_id}>
                  <td>
                    <code style={{ fontSize: 12 }}>{o.org_id}</code>
                  </td>
                  <td style={{ textAlign: "right" }}>
                    {o.cnt.toLocaleString()}
                  </td>
                  <td style={{ fontSize: 12, color: "#6b7484" }}>
                    {o.last_call
                      ? new Date(o.last_call).toLocaleString()
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {usage.totalCalls === 0 && (
        <div className="panel" style={{ textAlign: "center", padding: 48, color: "#6b7484" }}>
          <p style={{ fontSize: 15, margin: 0 }}>
            No MCP calls recorded yet. Tool usage will appear here once agents
            start using the hosted MCP endpoint.
          </p>
        </div>
      )}
    </>
  );
}

function StatCard({
  label,
  value,
  danger,
}: {
  label: string;
  value: number;
  danger?: boolean;
}) {
  return (
    <div
      className="panel"
      style={{ padding: "16px 20px", textAlign: "center" }}
    >
      <div
        style={{
          fontSize: 28,
          fontWeight: 700,
          color: danger ? "var(--danger, #ff4444)" : undefined,
        }}
      >
        {value.toLocaleString()}
      </div>
      <div style={{ fontSize: 13, color: "#6b7484", marginTop: 4 }}>
        {label}
      </div>
    </div>
  );
}
