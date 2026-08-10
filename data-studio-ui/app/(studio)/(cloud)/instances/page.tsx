import Link from "next/link";
import { LaunchButton } from "@/components/LaunchButton";
import { getInstanceStatus } from "@/lib/k8s-provisioner";
import { listInstancesAsync } from "@/lib/instances-store";
import { listHostsAsync } from "@/lib/hosts-store";
import { listProjectsByInstanceAsync } from "@/lib/projects-store";
import { resolveStudioOrgId } from "@/lib/org-context";
import { probeInstanceDb } from "@/lib/project-runtime";
import { getLibrebaseRuntime, getK8sContainerRuntime, runtimeBackendLabel } from "@/lib/runtime-env";

export const dynamic = "force-dynamic";

export default async function InstancesPage() {
  const orgId = await resolveStudioOrgId();
  const instances = await listInstancesAsync(orgId);
  const defaultRuntime = getLibrebaseRuntime();
  const k8sRuntime = getK8sContainerRuntime();

  const hosts = await listHostsAsync(orgId).catch(() => [] as never[]);
  const hostById = new Map(hosts.map((h) => [h.id, h]));

  const rows = await Promise.all(
    instances.map(async (instance) => {
      const probe = await probeInstanceDb(instance);
      const linked = await listProjectsByInstanceAsync(instance.id, orgId);
      const backend = runtimeBackendLabel(instance.runtimeTarget, k8sRuntime);
      const k8s =
        instance.runtimeTarget === "kubernetes"
          ? getInstanceStatus(instance.id)
          : undefined;
      return { instance, probe, linked, k8s, backend };
    }),
  );

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Instances</h1>
          <p className="muted">
            Launchable runtimes — health reflects actual probes (no fake green). Default target:{" "}
            <strong>{defaultRuntime}</strong>
          </p>
        </div>
      </div>

      {rows.length === 0 ? (
        <div className="empty">
          <p>No instances yet. Rent a VM, then launch an instance onto it.</p>
          <Link href="/hosts/new">Rent a VM</Link> · <Link href="/instances/new">Launch instance</Link>
        </div>
      ) : (
        <div className="card-grid">
          {rows.map(({ instance, probe, linked, k8s, backend }) => (
            <article key={instance.id} className="card">
              <h2>{instance.name}</h2>
              <p className="muted" style={{ fontSize: "0.85rem" }}>
                {instance.deploymentMode} · backend {backend} · API {instance.ports.api} · PG{" "}
                {instance.ports.postgres}
              </p>
              {instance.runtimeTarget === "kubernetes" && (
                <p className="muted" style={{ fontSize: "0.8rem", marginTop: "0.25rem" }}>
                  K8s: {instance.k8sNamespace ?? k8s?.namespace ?? "—"}
                  {k8s?.podPhase ? ` · pod ${k8s.podPhase}` : ""}
                  {instance.k8sDegraded || k8s?.degraded ? " · degraded" : ""}
                </p>
              )}
              {instance.hostId && (
                <p className="muted" style={{ fontSize: "0.8rem", marginTop: "0.25rem" }}>
                  Host: {hostById.get(instance.hostId)?.name ?? instance.hostId} ·{" "}
                  {instance.memLimitMb ?? "—"} MB reserved
                </p>
              )}
              <p style={{ margin: "0.75rem 0" }}>
                <span className={`badge ${probe.status}`}>
                  {probe.reachable ? "Running" : probe.status}
                </span>
                {probe.runtimeMode === "dev" && (
                  <span className="badge" style={{ marginLeft: "0.5rem" }}>
                    dev runtime
                  </span>
                )}
                {probe.runtimeMode === "production" && (
                  <span className="badge" style={{ marginLeft: "0.5rem" }}>
                    production
                  </span>
                )}
                {probe.degraded && (
                  <span className="badge" style={{ marginLeft: "0.5rem" }}>
                    degraded
                  </span>
                )}
              </p>
              <p className="muted" style={{ fontSize: "0.8rem" }}>{probe.message}</p>
              <p style={{ fontSize: "0.85rem", marginTop: "0.75rem" }}>
                {linked.length} linked project{linked.length === 1 ? "" : "s"}
              </p>
              <div style={{ marginTop: "0.75rem" }}>
                <LaunchButton
                  href={`/api/instances/${instance.id}/launch`}
                  label="Launch instance"
                />
              </div>
            </article>
          ))}
        </div>
      )}
    </>
  );
}
