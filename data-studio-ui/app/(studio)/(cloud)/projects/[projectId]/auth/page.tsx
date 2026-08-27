import { PageHeader } from "@/components/studio/PageHeader";
import { PauseGate } from "@/components/studio/PauseGate";
import { ProjectShell } from "../_components/project-shell";
import { UsersTable } from "./users-table";
import { requireProjectPage } from "@/lib/projects-store";

interface PageProps {
  params: Promise<{ projectId: string }>;
}

export default async function AuthUsersPage({ params }: PageProps) {
  const { projectId } = await params;
  const project = await requireProjectPage(projectId);

  return (
    <ProjectShell projectId={projectId} projectName={project.name}>
      <PageHeader
        title="Users"
        description="End-user accounts on this project's auth API."
      />
      <PauseGate projectId={projectId} projectName={project.name}>
        <UsersTable projectId={projectId} />
      </PauseGate>
    </ProjectShell>
  );
}
