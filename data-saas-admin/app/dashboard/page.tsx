import { getOverview, getHetznerCosts, adminEnabled } from "@/lib/admin-client";
import { AutoRefresh } from "@/components/AutoRefresh";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  if (!adminEnabled()) {
    return (
      <div className="admin-header">
        <div>
          <h1>Admin Dashboard</h1>
          <p>Set LIBREBASE_ADMIN_DASHBOARD_TOKEN to enable.</p>
        </div>
      </div>
    );
  }

  let overview;
  let hetzner;
  try {
    [overview, hetzner] = await Promise.all([
      getOverview(),
      getHetznerCosts(),
    ]);
  } catch (e) {
    return (
      <div className="admin-header">
        <div>
          <h1>Admin Dashboard</h1>
          <p style={{ color: "var(--danger)" }}>
            Could not reach admin-api: {e instanceof Error ? e.message : "unknown error"}
          </p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>Overview</h1>
          <p>Platform health at a glance</p>
        </div>
        <AutoRefresh interval={15_000} />
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="label">Organizations</div>
          <div className="value">{overview.orgCount}</div>
        </div>
        <div className="stat-card">
          <div className="label">Users</div>
          <div className="value">{overview.userCount}</div>
        </div>
        <div className="stat-card">
          <div className="label">Instances</div>
          <div className="value">{overview.instanceCount}</div>
        </div>
        <div className="stat-card">
          <div className="label">Hosts</div>
          <div className="value">{overview.hostCount}</div>
        </div>
        <div className="stat-card">
          <div className="label">Projects</div>
          <div className="value">{overview.projectCount}</div>
        </div>
        <div className="stat-card">
          <div className="label">Hetzner Spend</div>
          <div className="value cost-total">€{hetzner.totalMonthly.toFixed(2)}</div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
        <div className="panel">
          <div className="panel-header">Plan Distribution</div>
          <table className="table">
            <thead><tr><th>Plan</th><th>Count</th></tr></thead>
            <tbody>
              {Object.entries(overview.planDistribution).map(([plan, count]) => (
                <tr key={plan}>
                  <td><code>{plan}</code></td>
                  <td>{count}</td>
                </tr>
              ))}
              {Object.keys(overview.planDistribution).length === 0 && (
                <tr><td colSpan={2} style={{ color: "var(--muted)" }}>No data</td></tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="panel">
          <div className="panel-header">Instance States</div>
          <table className="table">
            <thead><tr><th>State</th><th>Count</th></tr></thead>
            <tbody>
              {Object.entries(overview.instanceByState).map(([state, count]) => (
                <tr key={state}>
                  <td><span className={`badge ${state}`}>{state}</span></td>
                  <td>{count}</td>
                </tr>
              ))}
              {Object.keys(overview.instanceByState).length === 0 && (
                <tr><td colSpan={2} style={{ color: "var(--muted)" }}>No data</td></tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="panel">
          <div className="panel-header">Host States</div>
          <table className="table">
            <thead><tr><th>Status</th><th>Count</th></tr></thead>
            <tbody>
              {Object.entries(overview.hostByState).map(([status, count]) => (
                <tr key={status}>
                  <td><span className={`badge ${status}`}>{status}</span></td>
                  <td>{count}</td>
                </tr>
              ))}
              {Object.keys(overview.hostByState).length === 0 && (
                <tr><td colSpan={2} style={{ color: "var(--muted)" }}>No data</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
