import Link from "next/link";
import { notFound } from "next/navigation";
import { LaunchButton } from "@/components/LaunchButton";
import { getInstanceAsync } from "@/lib/instances-store";
import { getProjectAsync } from "@/lib/projects-store";
import { getProjectUrlsAsync, probeProjectDb } from "@/lib/project-runtime";

export const dynamic = "force-dynamic";

interface PageProps {
  params: Promise<{ projectId: string }>;
}

export default async function ProjectHomePage({ params }: PageProps) {
  const { projectId } = await params;
  const project = await getProjectAsync(projectId);
  if (!project) notFound();

  const instance = await getInstanceAsync(project.instanceId, project.orgId);
  const probe = await probeProjectDb(projectId);
  const urls = await getProjectUrlsAsync(project);

  return (
    <>
      <div className="page-header">
        <div>
          <h1>{project.name}</h1>
          <p className="muted">
            {project.deploymentMode} · {project.region}
          </p>
        </div>
      </div>

      <nav className="tabs">
        <Link href={`/projects/${projectId}`} className="tab active">
          Home
        </Link>
        <Link href={`/projects/${projectId}/database`} className="tab">
          Database
        </Link>
        <Link href={`/projects/${projectId}/sql`} className="tab">
          SQL
        </Link>
        <Link href={`/projects/${projectId}/settings`} className="tab">
          Settings
        </Link>
      </nav>

      <div className="card" style={{ marginBottom: "1rem" }}>
        <h3>Database runtime</h3>
        <p style={{ margin: "0.5rem 0" }}>
          <span className={`badge ${probe.status}`}>
            {probe.reachable ? "Running" : probe.status}
          </span>
          {probe.degraded && (
            <span className="badge" style={{ marginLeft: "0.5rem" }}>
              degraded
            </span>
          )}
        </p>
        <p className="muted" style={{ fontSize: "0.85rem" }}>{probe.message}</p>

        {!probe.reachable && (
          <div style={{ marginTop: "1rem" }}>
            <LaunchButton href={`/api/projects/${projectId}/launch`} />
          </div>
        )}

        {urls && probe.reachable && (
          <dl style={{ marginTop: "1rem", fontSize: "0.85rem" }}>
            <dt className="muted">API</dt>
            <dd>{urls.apiUrl}</dd>
            <dt className="muted">Postgres</dt>
            <dd>{urls.postgresUrl}</dd>
          </dl>
        )}
      </div>

      {instance && (
        <div className="card">
          <h3>Linked instance</h3>
          <p className="muted" style={{ fontSize: "0.85rem" }}>
            {instance.name} · ports {instance.ports.api}/{instance.ports.postgres}
          </p>
          <p style={{ fontSize: "0.85rem" }}>
            Data dir: <code>{instance.dataDir}</code>
          </p>
        </div>
      )}
    </>
  );
}
