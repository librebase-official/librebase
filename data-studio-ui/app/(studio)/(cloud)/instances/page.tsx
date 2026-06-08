import Link from "next/link";
import { LaunchButton } from "@/components/LaunchButton";
import { listInstances } from "@/lib/instances-store";
import { listProjectsByInstance } from "@/lib/projects-store";
import { probeInstanceDb } from "@/lib/project-runtime";

export const dynamic = "force-dynamic";

export default async function InstancesPage() {
  const instances = listInstances("default");

  const rows = await Promise.all(
    instances.map(async (instance) => {
      const probe = await probeInstanceDb(instance);
      const linked = listProjectsByInstance(instance.id);
      return { instance, probe, linked };
    }),
  );

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Instances</h1>
          <p className="muted">Launchable runtimes — health reflects actual probes (no fake green)</p>
        </div>
      </div>

      {rows.length === 0 ? (
        <div className="empty">
          <p>No instances yet. Create a project to provision a dedicated runtime.</p>
          <Link href="/projects/new">New project</Link>
        </div>
      ) : (
        <div className="card-grid">
          {rows.map(({ instance, probe, linked }) => (
            <article key={instance.id} className="card">
              <h2>{instance.name}</h2>
              <p className="muted" style={{ fontSize: "0.85rem" }}>
                {instance.deploymentMode} · API {instance.ports.api} · PG {instance.ports.postgres}
              </p>
              <p style={{ margin: "0.75rem 0" }}>
                <span className={`badge ${probe.status}`}>
                  {probe.reachable ? "Running" : probe.status}
                </span>
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
