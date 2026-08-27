import { getHosts, adminEnabled } from "@/lib/admin-client";
import { HostActions } from "@/components/HostActions";
import { AutoRefresh } from "@/components/AutoRefresh";

export const dynamic = "force-dynamic";

export default async function HostsPage() {
  if (!adminEnabled()) return <div className="admin-header"><h1>Hosts</h1><p>Admin token not configured.</p></div>;

  let hosts;
  try { hosts = await getHosts(); } catch (e) {
    return <div className="admin-header"><h1>Hosts</h1><p style={{ color: "var(--danger)" }}>{e instanceof Error ? e.message : "error"}</p></div>;
  }

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>Hosts</h1>
          <p>{hosts.length} Hetzner server{hosts.length !== 1 ? "s" : ""} provisioned</p>
        </div>
        <AutoRefresh interval={15_000} />
      </div>

      <div className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Status</th>
              <th>IP</th>
              <th>Region</th>
              <th>Org</th>
              <th>Instances</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {hosts.map((h) => (
              <tr key={h.id}>
                <td><strong>{h.name}</strong><br/><code style={{ fontSize: 11 }}>{h.id}</code></td>
                <td><span className={`badge ${h.status}`}>{h.status}</span></td>
                <td><code>{h.ip || "—"}</code></td>
                <td>{h.region || "—"}</td>
                <td>{h.org_name || "—"}</td>
                <td>{h.instance_count}</td>
                <td><HostActions hostId={h.id} status={h.status} /></td>
              </tr>
            ))}
            {hosts.length === 0 && (
              <tr><td colSpan={7} className="empty-msg">No hosts provisioned yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
