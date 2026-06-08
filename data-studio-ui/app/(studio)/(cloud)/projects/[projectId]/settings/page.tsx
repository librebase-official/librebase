import Link from "next/link";
import { notFound } from "next/navigation";
import { getInstance } from "@/lib/instances-store";
import { getProject } from "@/lib/projects-store";

interface PageProps {
  params: Promise<{ projectId: string }>;
}

export default async function ProjectSettingsPage({ params }: PageProps) {
  const { projectId } = await params;
  const project = getProject(projectId);
  if (!project) notFound();
  const instance = getInstance(project.instanceId);

  return (
    <>
      <div className="page-header">
        <h1>{project.name} — Settings</h1>
      </div>
      <nav className="tabs">
        <Link href={`/projects/${projectId}`} className="tab">
          Home
        </Link>
        <Link href={`/projects/${projectId}/database`} className="tab">
          Database
        </Link>
        <Link href={`/projects/${projectId}/sql`} className="tab">
          SQL
        </Link>
        <Link href={`/projects/${projectId}/settings`} className="tab active">
          Settings
        </Link>
      </nav>
      <div className="card">
        <dl>
          <dt className="muted">Project ID</dt>
          <dd>{project.id}</dd>
          <dt className="muted">Deployment mode</dt>
          <dd>{project.deploymentMode}</dd>
          <dt className="muted">Region</dt>
          <dd>{project.region}</dd>
          <dt className="muted">Instance</dt>
          <dd>{instance?.name ?? project.instanceId}</dd>
        </dl>
      </div>
    </>
  );
}
