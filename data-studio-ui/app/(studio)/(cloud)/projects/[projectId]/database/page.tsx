import { PageHeader } from "@/components/studio/PageHeader";
import { PauseGate } from "@/components/studio/PauseGate";
import { ProjectShell } from "../_components/project-shell";
import { TablesBrowser } from "./tables-browser";
import { requireProjectPage } from "@/lib/projects-store";

interface PageProps {
  params: Promise<{ projectId: string }>;
}

export default async function ProjectDatabasePage({ params }: PageProps) {
  const { projectId } = await params;
  const project = await requireProjectPage(projectId);

  return (
    <ProjectShell projectId={projectId} projectName={project.name} active="database">
      <PageHeader
        title="Table editor"
        description="⌘C or right-click copies the table for an agent. Export CSV is in the toolbar."
      />
      <PauseGate projectId={projectId} projectName={project.name}>
        <TablesBrowser
          projectId={projectId}
          projectName={project.name}
        />
      </PauseGate>
    </ProjectShell>
  );
}
