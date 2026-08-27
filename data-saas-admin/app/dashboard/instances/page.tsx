import { getInstances, adminEnabled } from "@/lib/admin-client";
import { AutoRefresh } from "@/components/AutoRefresh";

export const dynamic = "force-dynamic";

export default async function InstancesPage() {
  if (!adminEnabled()) return <div className="admin-header"><h1>Instances</h1><p>Admin token not configured.</p></div>;

  let instances;
  try { instances = await getInstances(); } catch (e) {
    return <div className="admin-header"><h1>Instances</h1><p style={{ color: "var(--danger)" }}>{e instanceof Error ? e.message : "error"}</p></div>;
  }

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>Instances</h1>
          <p>{instances.length} database instance{instances.length !== 1 ? "s" : ""}</p>
        </div>
        <AutoRefresh interval={15_000} />
      </div>

      <div className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Status</th>
              <th>Memory</th>
              <th>Host</th>
              <th>Org</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {instances.map((i) => (
              <tr key={i.id}>
                <td><strong>{i.name}</strong></td>
                <td><span className={`badge ${i.status}`}>{i.status}</span></td>
                <td>{i.mem_limit_mb ? `${i.mem_limit_mb} MB` : "—"}</td>
                <td>{i.host_name || "—"}{i.host_ip ? <><br/><code style={{ fontSize: 11 }}>{i.host_ip}</code></> : null}</td>
                <td>{i.org_name || "—"}</td>
                <td style={{ fontSize: 12, color: "var(--muted)" }}>{new Date(i.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
            {instances.length === 0 && (
              <tr><td colSpan={6} className="empty-msg">No instances.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
