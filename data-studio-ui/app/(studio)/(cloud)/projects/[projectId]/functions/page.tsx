import { EmptyState } from "@/components/studio/EmptyState";
import { PageHeader } from "@/components/studio/PageHeader";
import { PauseGate } from "@/components/studio/PauseGate";
import { IconEdge } from "@/components/studio/icons";
import { ProjectShell } from "../_components/project-shell";
import { probeNamedSurface } from "@/lib/runtime-client";
import { requireProjectPage } from "@/lib/projects-store";

interface PageProps {
  params: Promise<{ projectId: string }>;
}

export default async function FunctionsPage({ params }: PageProps) {
  const { projectId } = await params;
  const project = await requireProjectPage(projectId);
  const probe = await probeNamedSurface(projectId, ["/functions/v1", "/edge/v1"]);

  return (
    <ProjectShell projectId={projectId} projectName={project.name}>
      <PageHeader
        title="Edge functions"
        description="Run server-side logic next to the data. Editor and CLI come after the runtime."
        actions={
          <button type="button" className="btn btn-primary" disabled>
            Deploy a function
          </button>
        }
      />
      <PauseGate projectId={projectId} projectName={project.name}>
        <EmptyState
          icon={<IconEdge />}
          title={probe.ok ? "Functions endpoint is up" : "Edge functions are not shipped yet"}
          body={
            probe.ok
              ? "The /functions/v1 probe succeeded. Deploy from the CLI when li-edge is on this instance."
              : "The rail is here so the IA matches. We will not fake a WASM runtime."
          }
          facts={[
            "Deploy via CLI when li-edge is installed.",
            "Secrets will live next to functions, not in a vault theater.",
          ]}
        />
      </PauseGate>
    </ProjectShell>
  );
}
