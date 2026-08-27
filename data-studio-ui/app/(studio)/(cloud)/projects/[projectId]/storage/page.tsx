import { EmptyState } from "@/components/studio/EmptyState";
import { PageHeader } from "@/components/studio/PageHeader";
import { PauseGate } from "@/components/studio/PauseGate";
import { IconStorage } from "@/components/studio/icons";
import { ProjectShell } from "../_components/project-shell";
import { probeNamedSurface } from "@/lib/runtime-client";
import { requireProjectPage } from "@/lib/projects-store";

interface PageProps {
  params: Promise<{ projectId: string }>;
}

export default async function StoragePage({ params }: PageProps) {
  const { projectId } = await params;
  const project = await requireProjectPage(projectId);
  const probe = await probeNamedSurface(projectId, ["/storage/v1/bucket", "/storage/v1"]);

  return (
    <ProjectShell projectId={projectId} projectName={project.name}>
      <PageHeader
        title="Storage"
        description="Object buckets on this project's runtime."
      />
      <PauseGate projectId={projectId} projectName={project.name}>
        <EmptyState
          icon={<IconStorage />}
          title={probe.ok ? "Storage is reachable" : "Storage is not on this runtime yet"}
          body={
            probe.ok
              ? "Bucket listing will appear here as the S3-compatible API fills in."
              : probe.message
          }
        />
      </PauseGate>
    </ProjectShell>
  );
}
