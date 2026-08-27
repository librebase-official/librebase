import { PageHeader } from "@/components/studio/PageHeader";
import { ProjectShell } from "../_components/project-shell";
import { SettingsForm } from "./settings-form";
import { getInstanceAsync } from "@/lib/instances-store";
import { requireProjectPage } from "@/lib/projects-store";
import { getProjectUrlsAsync, probeProjectDb } from "@/lib/project-runtime";
import { getConnectInfo } from "@/lib/runtime-client";

interface PageProps {
  params: Promise<{ projectId: string }>;
}

export default async function ProjectSettingsPage({ params }: PageProps) {
  const { projectId } = await params;
  const project = await requireProjectPage(projectId);
  const instance = await getInstanceAsync(project.instanceId, project.orgId);
  const probe = await probeProjectDb(projectId);
  const urls = await getProjectUrlsAsync(project);
  let keys = { anonKey: null as string | null, serviceRoleKey: null as string | null };
  try {
    const info = await getConnectInfo(projectId);
    keys = { anonKey: info.anonKey, serviceRoleKey: info.serviceRoleKey };
  } catch {
    /* keys stay unset */
  }

  return (
    <ProjectShell projectId={projectId} projectName={project.name} active="settings">
      <PageHeader
        title="Project settings"
        description="General configuration, API keys, linked database, and lifecycle."
      />
      <SettingsForm
        projectId={project.id}
        name={project.name}
        region={project.region}
        deploymentMode={project.deploymentMode}
        instanceId={project.instanceId}
        instanceName={instance?.name ?? project.instanceId}
        reachable={probe.reachable}
        apiUrl={urls?.apiUrl}
        postgresUrl={urls?.postgresUrl}
        anonKey={keys.anonKey}
        serviceRoleKey={keys.serviceRoleKey}
      />
    </ProjectShell>
  );
}
