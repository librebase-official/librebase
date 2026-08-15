import Link from "next/link";
import {
  adminApiEnabled,
  adminHealth,
  adminListMcpKeys,
  adminListMembers,
  adminMe,
} from "@/lib/librebase-admin-client";
import { McpKeys } from "@/components/McpKeys";
import { ChangePassword } from "@/components/ChangePassword";
import { resolveStudioOrgId } from "@/lib/org-context";

export const dynamic = "force-dynamic";

export default async function AdminPage() {
  const orgId = await resolveStudioOrgId();
  const enabled = adminApiEnabled();
  const healthy = enabled ? await adminHealth() : false;

  let me: Awaited<ReturnType<typeof adminMe>> | null = null;
  let meError: string | null = null;
  let members: Awaited<ReturnType<typeof adminListMembers>> = [];
  let mcpKeys: Awaited<ReturnType<typeof adminListMcpKeys>> = [];
  if (enabled && healthy) {
    try {
      me = await adminMe();
      members = await adminListMembers(me.activeOrgId || orgId);
      mcpKeys = await adminListMcpKeys(me.activeOrgId || orgId);
    } catch (e) {
      meError = e instanceof Error ? e.message : "Could not load /org/v1/me";
    }
  }

  return (
    <div className="main" style={{ maxWidth: 720, margin: "2rem auto" }}>
      <div className="page-header">
        <div>
          <h1>Librebase Admin</h1>
          <p className="muted">
            Operator panel — org metadata and entitlements (product layer, not lidb).
          </p>
        </div>
        <div style={{ display: "flex", gap: "0.5rem" }}>
          <Link href="/login" className="btn">
            Login
          </Link>
          <Link href="/setup" className="btn">
            Setup
          </Link>
        </div>
      </div>

      <dl style={{ display: "grid", gap: "0.75rem" }}>
        <div>
          <dt className="muted">Admin API</dt>
          <dd>
            {enabled ? (healthy ? "reachable" : "unreachable") : "disabled (JSON stores)"}
          </dd>
        </div>
        <div>
          <dt className="muted">Active org</dt>
          <dd>
            <code>{orgId}</code>
          </dd>
        </div>
        {me && (
          <>
            <div>
              <dt className="muted">Operator</dt>
              <dd>
                {me.user.email} · {me.role} · {me.edition}
              </dd>
            </div>
            <div>
              <dt className="muted">Memberships</dt>
              <dd>
                {me.memberships.length === 0
                  ? "—"
                  : me.memberships.map((m) => `${m.orgId} (${m.role})`).join(", ")}
              </dd>
            </div>
          </>
        )}
        {meError && (
          <div>
            <dt className="muted">Session</dt>
            <dd style={{ color: "var(--warn)" }}>
              {meError} — <Link href="/login">sign in</Link>
            </dd>
          </div>
        )}
      </dl>

      {members.length > 0 && (
        <section style={{ marginTop: "2rem" }}>
          <h2 style={{ fontSize: "1.1rem" }}>Members</h2>
          <ul style={{ listStyle: "none", padding: 0, marginTop: "0.75rem" }}>
            {members.map((m) => (
              <li
                key={m.userId}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  padding: "0.4rem 0",
                  borderBottom: "1px solid var(--border, #3333)",
                }}
              >
                <span>{m.email}</span>
                <span className="muted">{m.role}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {me && <McpKeys orgId={me.activeOrgId || orgId} initial={mcpKeys} />}

      {me && <ChangePassword />}

      <p style={{ marginTop: "2rem" }}>
        <Link href="/">← Projects</Link>
      </p>
    </div>
  );
}
