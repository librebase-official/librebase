import Link from "next/link";
import { adminApiEnabled, adminHealth, adminMe } from "@/lib/librebase-admin-client";
import { resolveStudioOrgId } from "@/lib/org-context";

export const dynamic = "force-dynamic";

export default async function AdminPage() {
  const orgId = await resolveStudioOrgId();
  const enabled = adminApiEnabled();
  const healthy = enabled ? await adminHealth() : false;

  let me: Awaited<ReturnType<typeof adminMe>> | null = null;
  let meError: string | null = null;
  if (enabled && healthy) {
    try {
      me = await adminMe();
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
        <Link href="/setup" className="btn">
          Setup
        </Link>
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
            <dd style={{ color: "var(--warn)" }}>{meError}</dd>
          </div>
        )}
      </dl>

      <p style={{ marginTop: "2rem" }}>
        <Link href="/">← Projects</Link>
      </p>
    </div>
  );
}
