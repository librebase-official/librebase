import { getOrgs, adminEnabled } from "@/lib/admin-client";
import { AutoRefresh } from "@/components/AutoRefresh";

export const dynamic = "force-dynamic";

export default async function OrgsPage() {
  if (!adminEnabled()) return <div className="admin-header"><h1>Organizations</h1><p>Admin token not configured.</p></div>;

  let orgs;
  try { orgs = await getOrgs(); } catch (e) {
    return <div className="admin-header"><h1>Organizations</h1><p style={{ color: "var(--danger)" }}>{e instanceof Error ? e.message : "error"}</p></div>;
  }

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>Organizations</h1>
          <p>{orgs.length} organization{orgs.length !== 1 ? "s" : ""}</p>
        </div>
        <AutoRefresh interval={15_000} />
      </div>

      <div className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Plan</th>
              <th>Edition</th>
              <th>Stripe</th>
              <th>Members</th>
              <th>Instances</th>
              <th>Projects</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {orgs.map((o) => (
              <tr key={o.id}>
                <td><strong>{o.name}</strong><br/><code style={{ fontSize: 11 }}>{o.id}</code></td>
                <td><code>{o.plan}</code></td>
                <td>{o.edition}</td>
                <td><span className={`badge ${o.stripe_status === "active" ? "running" : ""}`}>{o.stripe_status || "none"}</span></td>
                <td>{o.member_count}</td>
                <td>{o.instance_count}</td>
                <td>{o.project_count}</td>
                <td style={{ fontSize: 12, color: "var(--muted)" }}>{new Date(o.created_at).toLocaleDateString()}</td>
              </tr>
            ))}
            {orgs.length === 0 && (
              <tr><td colSpan={8} className="empty-msg">No organizations.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
