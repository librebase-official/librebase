import { PageHeader } from "@/components/studio/PageHeader";
import { PauseGate } from "@/components/studio/PauseGate";
import { ProjectShell } from "../_components/project-shell";
import { KeysManager } from "./keys-manager";
import { requireProjectPage } from "@/lib/projects-store";
import {
  adminApiEnabled,
  adminListMyKeys,
  adminListOrgKeys,
} from "@/lib/librebase-admin-client";

interface PageProps {
  params: Promise<{ projectId: string }>;
}

export default async function KeysPage({ params }: PageProps) {
  const { projectId } = await params;
  const project = await requireProjectPage(projectId);

  const [initialKeys, myKeys] = adminApiEnabled()
    ? await Promise.all([
        adminListOrgKeys(project.orgId)
          .then((r) => r.keys)
          .catch(() => []),
        adminListMyKeys().then((r) => r.keys).catch(() => []),
      ])
    : [[], []];

  return (
    <ProjectShell projectId={projectId} projectName={project.name}>
      <PageHeader
        title="Keys"
        description="Store secrets with a scope. Paste a value once — it is sealed in the KMS and never shown again except when you reveal it."
      />
      <PauseGate projectId={projectId} projectName={project.name}>
        <KeysManager
          projectId={projectId}
          initialKeys={initialKeys}
          initialMyKeys={myKeys}
        />
      </PauseGate>
    </ProjectShell>
  );
}