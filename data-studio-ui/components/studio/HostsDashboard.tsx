"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import { DeleteButton } from "@/components/studio/DeleteButton";
import { EmptyState } from "@/components/studio/EmptyState";
import { LiveBadge } from "@/components/studio/LiveBadge";
import { PageHeader } from "@/components/studio/PageHeader";
import { IconPlus, IconServer } from "@/components/studio/icons";
import { hostIsProvisioning } from "@/lib/live-status";
import { useInterval } from "@/lib/use-interval";
import type { Host, Instance } from "@/lib/types";

export function HostsDashboard({
  initialHosts,
  initialInstances,
}: {
  initialHosts: Host[];
  initialInstances: Instance[];
}) {
  const [hosts, setHosts] = useState(initialHosts);
  const [instances, setInstances] = useState(initialInstances);

  const refresh = useCallback(async () => {
    try {
      const [hRes, iRes] = await Promise.all([fetch("/api/hosts"), fetch("/api/instances")]);
      if (hRes.ok) {
        const data = (await hRes.json()) as { hosts?: Host[] };
        setHosts(data.hosts ?? []);
      }
      if (iRes.ok) {
        const data = (await iRes.json()) as { instances?: Instance[] };
        setInstances(data.instances ?? []);
      }
    } catch {
      /* keep last good snapshot */
    }
  }, []);

  const busy = hosts.some((h) => hostIsProvisioning(h));
  useInterval(refresh, busy ? 3000 : null);

  const byHost = new Map<string, Instance[]>();
  for (const instance of instances) {
    if (!instance.hostId) continue;
    const bucket = byHost.get(instance.hostId) ?? [];
    bucket.push(instance);
    byHost.set(instance.hostId, bucket);
  }

  return (
    <>
      <PageHeader
        title="VMs / hosts"
        description="Rented machines. Launch multiple instances on one host and keep the memory budget honest."
        actions={
          <Link href="/hosts/new" className="btn btn-primary">
            <IconPlus width="14" height="14" />
            Rent a VM
          </Link>
        }
      />

      {hosts.length === 0 ? (
        <EmptyState
          icon={<IconServer />}
          title="No hosts yet"
          body="Rent a VM (512 MB is enough to start) and launch instances onto it."
          actions={
            <Link href="/hosts/new" className="btn btn-primary">
              Rent a VM
            </Link>
          }
        />
      ) : (
        <div className="card-grid">
          {hosts.map((host) => {
            const placed = byHost.get(host.id) ?? [];
            const used = host.memUsedMb;
            const total = host.memMb;
            const pct = total > 0 ? Math.round((used / total) * 100) : 0;
            const busyHost = hostIsProvisioning(host);
            const healthy = host.status === "running" && !!host.ip;
            const instanceWord = placed.length === 1 ? "instance" : "instances";

            return (
              <article key={host.id} className="card host-card">
                <div className="host-card-header">
                  <h2>{host.name}</h2>
                  <span className="flex-gap">
                    <LiveBadge
                      variant={healthy ? "running" : busyHost ? "starting" : host.status === "error" ? "error" : "stopped"}
                      label={host.status}
                      spinner={busyHost}
                    />
                    <DeleteButton
                      href={`/api/hosts/${host.id}`}
                      confirmTitle={`Delete “${host.name}”?`}
                      confirmBody={
                        placed.length > 0
                          ? `This destroys the VM and ${placed.length} ${instanceWord} on it. That cannot be undone.`
                          : "This destroys the rented VM. That cannot be undone."
                      }
                      label="Delete VM"
                      onSuccess={() => {
                        setHosts((prev) => prev.filter((h) => h.id !== host.id));
                        setInstances((prev) => prev.filter((i) => i.hostId !== host.id));
                      }}
                    />
                  </span>
                </div>

                <p className="muted text-sm">
                  {host.provider} · {host.region}
                  {host.serverId ? <span className="muted"> · Hetzner #{host.serverId}</span> : null}
                </p>

                {host.ip && <p className="muted text-sm mt-1">IP: {host.ip}</p>}

                {busyHost && (
                  <p className="muted text-sm mt-1">
                    The VM is booting from the golden image… instances can’t be launched yet.
                    This card updates on its own when the server is up.
                  </p>
                )}

                {healthy && (
                  <p className="muted text-sm mt-1">
                    VM is up. Instances on it stay stopped until you launch them.
                  </p>
                )}

                <div className="mt-3">
                  <div className="host-mem-row">
                    <span className="text-sm">Memory budget</span>
                    <span className="text-sm">
                      {used} / {total} MB ({pct}%)
                    </span>
                  </div>
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{
                        width: `${Math.min(pct, 100)}%`,
                        background:
                          pct > 90 ? "var(--danger)" : pct > 70 ? "var(--warn)" : "var(--accent)",
                      }}
                    />
                  </div>
                </div>

                <p className="text-sm mt-2">
                  {placed.length} {instanceWord} on this host
                </p>
                {placed.length > 0 && (
                  <ul className="muted text-sm" style={{ margin: "0 0 0.5rem 0", paddingLeft: "1rem" }}>
                    {placed.map((inst) => (
                      <li key={inst.id}>
                        {inst.name} · {inst.memLimitMb ?? "—"} MB ·{" "}
                        {busyHost ? "waiting for VM" : inst.status === "running" ? "running" : "stopped"}
                      </li>
                    ))}
                  </ul>
                )}

                <div className="mt-3">
                  {healthy ? (
                    <Link href={`/instances/new?hostId=${host.id}`}>Launch instance on this VM</Link>
                  ) : (
                    <span className="muted text-sm">Launch disabled until the VM is running</span>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      )}
    </>
  );
}
