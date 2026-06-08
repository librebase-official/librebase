import Link from "next/link";
import { notFound } from "next/navigation";
import { getProject } from "@/lib/projects-store";

interface PageProps {
  params: Promise<{ projectId: string }>;
}

export default async function ProjectSqlPage({ params }: PageProps) {
  const { projectId } = await params;
  const project = getProject(projectId);
  if (!project) notFound();

  return (
    <>
      <div className="page-header">
        <h1>{project.name} — SQL</h1>
      </div>
      <nav className="tabs">
        <Link href={`/projects/${projectId}`} className="tab">
          Home
        </Link>
        <Link href={`/projects/${projectId}/database`} className="tab">
          Database
        </Link>
        <Link href={`/projects/${projectId}/sql`} className="tab active">
          SQL
        </Link>
        <Link href={`/projects/${projectId}/settings`} className="tab">
          Settings
        </Link>
      </nav>
      <div className="empty">SQL editor stub — coming in a later phase.</div>
    </>
  );
}
