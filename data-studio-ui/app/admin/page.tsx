import Link from "next/link";
import {
  adminApiEnabled,
  adminGetBilling,
  adminHealth,
  adminListMcpKeys,
  adminListMembers,
  adminMe,
} from "@/lib/librebase-admin-client";
import { McpKeys } from "@/components/McpKeys";
import { ChangePassword } from "@/components/ChangePassword";
import { InviteMembers } from "@/components/InviteMembers";
import { OrgSettings } from "@/components/OrgSettings";
import { BillingPlans } from "@/components/BillingPlans";
import { Badge } from "@/components/ui/badge";
import { PageHeader } from "@/components/studio/PageHeader";
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
  let billing: Awaited<ReturnType<typeof adminGetBilling>> | null = null;
  if (enabled && healthy) {
    try {
      me = await adminMe();
      members = await adminListMembers(me.activeOrgId || orgId);
      mcpKeys = await adminListMcpKeys(me.activeOrgId || orgId);
      billing = await adminGetBilling(me.activeOrgId || orgId);
    } catch (e) {
      meError = e instanceof Error ? e.message : "Could not load /org/v1/me";
    }
  }

  return (
    <div className="st-settings">
      <PageHeader
        title="Admin"
        description="Operator panel — org metadata and entitlements. Product layer, not lidb."
        actions={
          <div className="flex-gap">
            <Link href="/login" className="btn">
              Login
            </Link>
            <Link href="/setup" className="btn">
              Setup
            </Link>
          </div>
        }
      />

      <dl className="admin-meta">
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
              <dt className="muted">Organization</dt>
              <dd className="flex-gap">
                <strong>{me.activeOrgName ?? me.activeOrgId}</strong>
                <OrgSettings
                  orgId={me.activeOrgId}
                  currentName={me.activeOrgName ?? me.activeOrgId}
                  role={
                    (me.role === "owner" || me.role === "admin")
                      ? me.role
                      : "developer"
                  }
                />
              </dd>
            </div>
            <div>
              <dt className="muted">Operator</dt>
              <dd>
                {me.user.email} · {me.role} · <Badge variant="info">{me.edition}</Badge>
              </dd>
            </div>
            <div>
              <dt className="muted">Memberships</dt>
              <dd>
                {me.memberships.length === 0
                  ? "—"
                  : me.memberships
                      .map((m) => `${m.name ?? m.orgId} (${m.role})`)
                      .join(", ")}
              </dd>
            </div>
          </>
        )}
        {meError && (
          <div>
            <dt className="muted">Session</dt>
            <dd className="auth-error">
              {meError} — <Link href="/login">sign in</Link>
            </dd>
          </div>
        )}
      </dl>

      {members.length > 0 && (
        <section className="admin-section">
          <h2 className="admin-section-title">Members</h2>
          <ul className="member-list">
            {members.map((m) => (
              <li key={m.userId}>
                <span>{m.email}</span>
                <Badge variant="info">{m.role}</Badge>
              </li>
            ))}
          </ul>
        </section>
      )}

      {billing && (
        <BillingPlans
          orgId={billing.orgId}
          plan={billing.plan}
          edition={billing.edition}
          stripeConfigured={billing.stripeConfigured}
          stripeStatus={billing.stripeStatus}
          instanceCount={billing.instanceCount}
          instanceLimit={billing.instanceLimit}
        />
      )}

      {me && me.role === "owner" && (
        <InviteMembers orgId={me.activeOrgId || orgId} />
      )}

      {me && <McpKeys orgId={me.activeOrgId || orgId} initial={mcpKeys} />}

      {me && <ChangePassword />}

      <p className="mt-4">
        <Link href="/">← Projects</Link>
      </p>
    </div>
  );
}
