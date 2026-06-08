import Link from "next/link";
import { notFound } from "next/navigation";
import { getProject } from "@/lib/projects-store";

interface PageProps {
  params: Promise<{ projectId: string }>;
}

export default async function ProjectDatabasePage({ params }: PageProps) {
  const { projectId } = await params;
  const project = getProject(projectId);
  if (!project) notFound();

  return (
    <>
      <div className="page-header">
        <h1>{project.name} — Database</h1>
      </div>
      <nav className="tabs">
        <Link href={`/projects/${projectId}`} className="tab">
          Home
        </Link>
        <Link href={`/projects/${projectId}/database`} className="tab active">
          Database
        </Link>
        <Link href={`/projects/${projectId}/sql`} className="tab">
          SQL
        </Link>
        <Link href={`/projects/${projectId}/settings`} className="tab">
          Settings
        </Link>
      </nav>
      <div className="empty">Table browser stub — launch database first.</div>
    </>
  );
}
