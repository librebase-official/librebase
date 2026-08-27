import { PageHeader } from "@/components/studio/PageHeader";
import { PauseGate } from "@/components/studio/PauseGate";
import { ProjectShell } from "../_components/project-shell";
import { SqlEditor } from "./sql-editor";
import { requireProjectPage } from "@/lib/projects-store";

interface PageProps {
  params: Promise<{ projectId: string }>;
}

export default async function ProjectSqlPage({ params }: PageProps) {
  const { projectId } = await params;
  const project = await requireProjectPage(projectId);

  return (
    <ProjectShell projectId={projectId} projectName={project.name} active="sql">
      <PageHeader
        title="SQL editor"
        description="Postgres-compatible SQL against this project's runtime. Failures stay visible."
      />
      <PauseGate projectId={projectId} projectName={project.name}>
        <SqlEditor projectId={projectId} />
      </PauseGate>
    </ProjectShell>
  );
}
