import { ProjectShell } from "../_components/project-shell";
import { ProjectWorkspace } from "../_components/project-workspace";
import { getInstanceAsync } from "@/lib/instances-store";
import { requireProjectPage } from "@/lib/projects-store";
import { getProjectUrlsAsync, probeProjectDb } from "@/lib/project-runtime";

export const dynamic = "force-dynamic";

interface Props {
  params: Promise<{ projectId: string }>;
}

export default async function ProjectAgentPage({ params }: Props) {
  const { projectId } = await params;
  const project = await requireProjectPage(projectId);

  const instance = await getInstanceAsync(project.instanceId, project.orgId);
  const probe = await probeProjectDb(projectId);
  const urls = await getProjectUrlsAsync(project);

  return (
    <ProjectShell projectId={projectId} projectName={project.name} active="home">
      <ProjectWorkspace
        project={project}
        instance={instance}
        probe={probe}
        urls={urls}
      />
    </ProjectShell>
  );
}
