import { getHetznerCosts, adminEnabled } from "@/lib/admin-client";
import { AutoRefresh } from "@/components/AutoRefresh";

export const dynamic = "force-dynamic";

export default async function SystemPage() {
  if (!adminEnabled()) return <div className="admin-header"><h1>System</h1><p>Admin token not configured.</p></div>;

  let hetzner;
  try { hetzner = await getHetznerCosts(); } catch (e) {
    return <div className="admin-header"><h1>System</h1><p style={{ color: "var(--danger)" }}>{e instanceof Error ? e.message : "error"}</p></div>;
  }

  const now = new Date();
  const yearCost = hetzner.totalMonthly * 12;

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>System</h1>
          <p>Hetzner costs · {now.toLocaleDateString("en-GB", { month: "long", year: "numeric" })}</p>
        </div>
        <AutoRefresh interval={30_000} />
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="label">Active Servers</div>
          <div className="value">{hetzner.servers.filter((s) => s.status === "running").length}</div>
        </div>
        <div className="stat-card">
          <div className="label">Monthly Spend</div>
          <div className="value cost-total">€{hetzner.totalMonthly.toFixed(2)}</div>
        </div>
        <div className="stat-card">
          <div className="label">Annual Estimate</div>
          <div className="value">€{yearCost.toFixed(2)}</div>
        </div>
      </div>

      <div className="panel">
        <div className="panel-header">Hetzner Servers</div>
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Status</th>
              <th>Type</th>
              <th>IP</th>
              <th>Region</th>
              <th>Monthly</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {hetzner.servers.map((s) => (
              <tr key={s.id}>
                <td><strong>{s.name}</strong><br/><code style={{ fontSize: 11 }}>{s.id}</code></td>
                <td><span className={`badge ${s.status}`}>{s.status}</span></td>
                <td><code>{s.serverType}</code></td>
                <td><code>{s.ip || "—"}</code></td>
                <td>{s.region || "—"}</td>
                <td>€{s.monthlyCost.toFixed(2)}</td>
                <td style={{ fontSize: 12, color: "var(--muted)" }}>
                  {s.createdAt ? new Date(s.createdAt).toLocaleDateString() : "—"}
                </td>
              </tr>
            ))}
            {hetzner.servers.length === 0 && (
              <tr><td colSpan={7} className="empty-msg">No servers on Hetzner.</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {Object.keys(hetzner.pricing).length > 0 && (
        <div className="panel">
          <div className="panel-header">Pricing Catalog (fsn1)</div>
          <table className="table">
            <thead><tr><th>Server Type</th><th>Monthly (€)</th></tr></thead>
            <tbody>
              {Object.entries(hetzner.pricing)
                .sort((a, b) => a[1] - b[1])
                .map(([type, price]) => (
                <tr key={type}>
                  <td><code>{type}</code></td>
                  <td>€{price.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
