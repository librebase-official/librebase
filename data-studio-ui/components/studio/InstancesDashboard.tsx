"use client";

import Link from "next/link";
import { useCallback, useRef, useState } from "react";
import { LaunchButton } from "@/components/LaunchButton";
import { DeleteButton } from "@/components/studio/DeleteButton";
import { EmptyState } from "@/components/studio/EmptyState";
import { LiveBadge } from "@/components/studio/LiveBadge";
import { PageHeader } from "@/components/studio/PageHeader";
import { PauseButton } from "@/components/studio/PauseButton";
import { IconDatabase, IconPlus } from "@/components/studio/icons";
import { hostIsProvisioning, liveInstanceView } from "@/lib/live-status";
import { useInterval } from "@/lib/use-interval";
import type { DbProbeResult, Host, Instance } from "@/lib/types";

export type InstanceRow = {
  instance: Instance;
  probe: DbProbeResult;
  linkedCount: number;
  backend: string;
  k8sLine?: string;
};

export function InstancesDashboard({
  initialRows,
  initialHosts,
  defaultRuntime,
}: {
  initialRows: InstanceRow[];
  initialHosts: Host[];
  defaultRuntime: string;
}) {
  const [rows, setRows] = useState(initialRows);
  const [hosts, setHosts] = useState(initialHosts);
  const rowsRef = useRef(rows);
  rowsRef.current = rows;

  const refresh = useCallback(async () => {
    try {
      const hRes = await fetch("/api/hosts");
      if (hRes.ok) {
        const data = (await hRes.json()) as { hosts?: Host[] };
        setHosts(data.hosts ?? []);
      }
      const updates = await Promise.all(
        rowsRef.current.map(async (row) => {
          const res = await fetch(`/api/instances/${row.instance.id}/status`);
          if (!res.ok) return row;
          const data = (await res.json()) as { instance?: Instance; probe?: DbProbeResult };
          return {
            ...row,
            instance: data.instance ?? row.instance,
            probe: data.probe ?? row.probe,
          };
        }),
      );
      setRows(updates);
    } catch {
      /* keep last good snapshot */
    }
  }, []);

  const hostById = new Map(hosts.map((h) => [h.id, h]));
  const waiting = rows.some((row) => hostIsProvisioning(hostById.get(row.instance.hostId ?? "")));
  const launching = rows.some((row) => row.instance.status === "starting");
  useInterval(refresh, waiting || launching ? 3000 : null);

  function patchRow(
    id: string,
    probe: Partial<DbProbeResult>,
    instanceStatus?: Instance["status"],
  ) {
    setRows((prev) =>
      prev.map((row) =>
        row.instance.id === id
          ? {
              ...row,
              probe: { ...row.probe, ...probe },
              instance: instanceStatus
                ? { ...row.instance, status: instanceStatus }
                : row.instance,
            }
          : row,
      ),
    );
  }

  return (
    <>
      <PageHeader
        title="Instances"
        description={
          <>
            Launchable runtimes. Health is a live probe — default target{" "}
            <strong>{defaultRuntime}</strong>.
          </>
        }
        actions={
          <Link href="/instances/new" className="btn btn-primary">
            <IconPlus width="14" height="14" />
            New instance
          </Link>
        }
      />

      {rows.length === 0 ? (
        <EmptyState
          icon={<IconDatabase />}
          title="No instances yet"
          body="Rent a VM, then launch an instance onto it. Status will stay muted until a probe succeeds."
          actions={
            <>
              <Link href="/hosts/new" className="btn">
                Rent a VM
              </Link>
              <Link href="/instances/new" className="btn btn-primary">
                Launch instance
              </Link>
            </>
          }
        />
      ) : (
        <div className="card-grid">
          {rows.map((row) => {
            const { instance, probe, linkedCount, backend, k8sLine } = row;
            const host = instance.hostId ? hostById.get(instance.hostId) : undefined;
            const view = liveInstanceView({
              host,
              reachable: probe.reachable,
              status: probe.status,
              persistedStatus: instance.status,
            });
            const hostBusy = hostIsProvisioning(host);

            return (
              <article key={instance.id} className="card instance-card">
                <div className="instance-card-header">
                  <h2>{instance.name}</h2>
                  <span className="flex-gap">
                    <LiveBadge variant={view.variant} label={view.label} spinner={view.spinner} />
                    <DeleteButton
                      href={`/api/instances/${instance.id}`}
                      confirmTitle={`Delete “${instance.name}”?`}
                      confirmBody="This permanently removes the runtime and any projects linked to it."
                      label="Delete instance"
                      onSuccess={() => setRows((prev) => prev.filter((r) => r.instance.id !== instance.id))}
                    />
                  </span>
                </div>

                <p className="muted text-sm">
                  {instance.deploymentMode} · backend {backend} · API {instance.ports.api} · PG{" "}
                  {instance.ports.postgres}
                </p>
                {k8sLine ? <p className="muted text-sm mt-1">{k8sLine}</p> : null}
                {host && (
                  <p className="muted text-sm mt-1">
                    Host: {host.name} · {instance.memLimitMb ?? "—"} MB reserved
                  </p>
                )}
                <p className="muted text-sm mt-2">
                  {hostBusy
                    ? `Waiting for VM ${host?.name ?? "host"} to finish booting. Status flips to Stopped when it’s up — no reload needed.`
                    : probe.message}
                </p>

                <p className="text-sm mt-2">
                  {linkedCount} linked project{linkedCount === 1 ? "" : "s"}
                </p>

                <div className="mt-3">
                  {hostBusy ? (
                    <span className="muted text-sm">Launch disabled until the VM is running</span>
                  ) : view.variant === "running" ? (
                    <PauseButton
                      href={`/api/instances/${instance.id}/pause`}
                      label="Pause instance"
                      onDone={(data) =>
                        patchRow(
                          instance.id,
                          {
                            reachable: false,
                            status: "stopped",
                            message: data.message ?? data.probe?.message ?? "Paused",
                          },
                          "stopped",
                        )
                      }
                    />
                  ) : (
                    <LaunchButton
                      href={`/api/instances/${instance.id}/launch`}
                      label="Launch instance"
                      className="btn btn-sm btn-primary"
                      onDone={(data) =>
                        patchRow(
                          instance.id,
                          {
                            reachable: Boolean(data.probe?.reachable),
                            status: (data.probe?.status as DbProbeResult["status"]) ?? "starting",
                            message: data.message ?? data.probe?.message,
                          },
                          data.probe?.reachable ? "running" : "starting",
                        )
                      }
                    />
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
