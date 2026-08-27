import { PageHeader } from "@/components/studio/PageHeader";
import { PauseGate } from "@/components/studio/PauseGate";
import { ProjectShell } from "../_components/project-shell";
import { RealtimeChannels } from "./channels";
import { requireProjectPage } from "@/lib/projects-store";

interface PageProps {
  params: Promise<{ projectId: string }>;
}

export default async function RealtimePage({ params }: PageProps) {
  const { projectId } = await params;
  const project = await requireProjectPage(projectId);

  return (
    <ProjectShell projectId={projectId} projectName={project.name}>
      <PageHeader
        title="Realtime"
        description="Connected channels on this runtime. We do not invent a 404 as a product page."
      />
      <PauseGate projectId={projectId} projectName={project.name}>
        <RealtimeChannels projectId={projectId} />
      </PauseGate>
    </ProjectShell>
  );
}
