import { getUsers, adminEnabled } from "@/lib/admin-client";
import { AutoRefresh } from "@/components/AutoRefresh";

export const dynamic = "force-dynamic";

export default async function UsersPage() {
  if (!adminEnabled()) return <div className="admin-header"><h1>Users</h1><p>Admin token not configured.</p></div>;

  let users;
  try { users = await getUsers(); } catch (e) {
    return <div className="admin-header"><h1>Users</h1><p style={{ color: "var(--danger)" }}>{e instanceof Error ? e.message : "error"}</p></div>;
  }

  return (
    <>
      <div className="admin-header">
        <div>
          <h1>Users</h1>
          <p>{users.length} user{users.length !== 1 ? "s" : ""} registered</p>
        </div>
        <AutoRefresh interval={30_000} />
      </div>

      <div className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Email</th>
              <th>MFA</th>
              <th>Organizations</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id}>
                <td>
                  <strong>{u.email}</strong>
                  <br/>
                  <code style={{ fontSize: 11 }}>{u.id}</code>
                </td>
                <td>
                  {u.mfa_enabled ? (
                    <span className="badge running">enabled</span>
                  ) : (
                    <span className="badge">off</span>
                  )}
                </td>
                <td>{u.org_names || "—"}</td>
                <td style={{ fontSize: 12, color: "var(--muted)" }}>
                  {new Date(u.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr><td colSpan={4} className="empty-msg">No users.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}
