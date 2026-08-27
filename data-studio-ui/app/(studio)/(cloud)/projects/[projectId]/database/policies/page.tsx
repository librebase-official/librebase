import { PageHeader } from "@/components/studio/PageHeader";
import { PauseGate } from "@/components/studio/PauseGate";
import { ProjectShell } from "../../_components/project-shell";
import { PoliciesTable } from "./policies-table";
import { requireProjectPage } from "@/lib/projects-store";

interface PageProps {
  params: Promise<{ projectId: string }>;
}

export default async function PoliciesPage({ params }: PageProps) {
  const { projectId } = await params;
  const project = await requireProjectPage(projectId);

  return (
    <ProjectShell projectId={projectId} projectName={project.name}>
      <PageHeader
        title="Policies"
        description="Row-level security policies read from pg_policies. This page is read-only."
      />
      <PauseGate projectId={projectId} projectName={project.name}>
        <PoliciesTable projectId={projectId} />
      </PauseGate>
    </ProjectShell>
  );
}
