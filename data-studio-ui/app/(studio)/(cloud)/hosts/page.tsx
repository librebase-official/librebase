import Link from "next/link";
import { listHostsAsync } from "@/lib/hosts-store";
import { listInstancesAsync } from "@/lib/instances-store";
import { resolveStudioOrgId } from "@/lib/org-context";

export const dynamic = "force-dynamic";

export default async function HostsPage() {
  const orgId = await resolveStudioOrgId();
  const [hosts, instances] = await Promise.all([
    listHostsAsync(orgId),
    listInstancesAsync(orgId),
  ]);

  const byHost = new Map<string, typeof instances>();
  for (const instance of instances) {
    if (!instance.hostId) continue;
    const bucket = byHost.get(instance.hostId) ?? [];
    bucket.push(instance);
    byHost.set(instance.hostId, bucket);
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1>VMs / hosts</h1>
          <p className="muted">
            Rented VMs — launch multiple Librebase instances on a single host and manage its
            memory budget from here.
          </p>
        </div>
      </div>

      {hosts.length === 0 ? (
        <div className="empty">
          <p>No hosts yet. Rent a VM (e.g. 512 MB) and launch instances onto it.</p>
          <Link href="/hosts/new">Rent a VM</Link>
        </div>
      ) : (
        <div className="card-grid">
          {hosts.map((host) => {
            const placed = byHost.get(host.id) ?? [];
            const used = host.memUsedMb;
            const total = host.memMb;
            const pct = total > 0 ? Math.round((used / total) * 100) : 0;
            return (
              <article key={host.id} className="card">
                <h2>{host.name}</h2>
                <p className="muted" style={{ fontSize: "0.85rem" }}>
                  {host.provider} · {host.region} · {host.status}
                </p>
                <div style={{ margin: "0.75rem 0" }}>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      fontSize: "0.85rem",
                      marginBottom: "0.25rem",
                    }}
                  >
                    <span>Memory budget</span>
                    <span>
                      {used} / {total} MB ({pct}%)
                    </span>
                  </div>
                  <div
                    style={{
                      background: "var(--border)",
                      borderRadius: "4px",
                      height: "8px",
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        width: `${Math.min(pct, 100)}%`,
                        height: "100%",
                        background: pct > 90 ? "#d33" : pct > 70 ? "#c90" : "#1a7f4b",
                      }}
                    />
                  </div>
                </div>
                <p style={{ fontSize: "0.85rem", margin: "0.5rem 0" }}>
                  {placed.length} instance{placed.length === 1 ? "" : "s"} on this host
                </p>
                {placed.length > 0 && (
                  <ul style={{ fontSize: "0.85rem", margin: "0 0 0.5rem 0", paddingLeft: "1rem" }}>
                    {placed.map((inst) => (
                      <li key={inst.id}>
                        {inst.name} · {inst.memLimitMb ?? "—"} MB · {inst.status}
                      </li>
                    ))}
                  </ul>
                )}
                <div style={{ marginTop: "0.75rem" }}>
                  <Link href={`/instances/new?hostId=${host.id}`}>Launch instance on this VM</Link>
                </div>
              </article>
            );
          })}
        </div>
      )}
    </>
  );
}
