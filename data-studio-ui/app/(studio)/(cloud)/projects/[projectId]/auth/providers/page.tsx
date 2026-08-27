import { PageHeader } from "@/components/studio/PageHeader";
import { PauseGate } from "@/components/studio/PauseGate";
import { ProjectShell } from "../../_components/project-shell";
import { ProvidersForm } from "./providers-form";
import { requireProjectPage } from "@/lib/projects-store";
import { adminApiEnabled, adminListProjectProviders } from "@/lib/librebase-admin-client";
import { SITE_URL } from "@/lib/site";

interface PageProps {
  params: Promise<{ projectId: string }>;
}

export default async function AuthProvidersPage({ params }: PageProps) {
  const { projectId } = await params;
  const project = await requireProjectPage(projectId);
  const callbackUrl = `${SITE_URL}/api/projects/${projectId}/auth/oauth/callback`;
  const initialProviders = adminApiEnabled()
    ? await adminListProjectProviders(project.orgId, projectId).catch(() => [])
    : [];

  return (
    <ProjectShell projectId={projectId} projectName={project.name}>
      <PageHeader
        title="Sign in / Providers"
        description="Configure GitHub and Google so your app’s users can sign in — not Studio operators."
      />
      <PauseGate projectId={projectId} projectName={project.name}>
        <ProvidersForm
          projectId={projectId}
          callbackUrl={callbackUrl}
          initialProviders={initialProviders}
        />
      </PauseGate>
    </ProjectShell>
  );
}
