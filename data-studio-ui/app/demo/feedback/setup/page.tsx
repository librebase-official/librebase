import { redirect } from "next/navigation";
import {
  adminApiEnabled,
  adminListProjectProviders,
  adminMe,
} from "@/lib/librebase-admin-client";
import { SITE_URL } from "@/lib/site";
import { DEMO_PROJECT_ID } from "@/lib/demo";
import { SetupKeys } from "./SetupKeys";

export const dynamic = "force-dynamic";

export default async function FeedbackSetupPage({
  searchParams,
}: {
  searchParams: Promise<{ project?: string }>;
}) {
  const { project: projectParam } = await searchParams;
  const projectId = projectParam?.trim() || DEMO_PROJECT_ID;
  const next = `/demo/feedback/setup?project=${encodeURIComponent(projectId)}`;

  if (!adminApiEnabled()) {
    redirect(`/login?next=${encodeURIComponent(next)}`);
  }
  let me;
  try {
    me = await adminMe();
  } catch {
    redirect(`/login?next=${encodeURIComponent(next)}`);
  }

  const callbackUrl = `${SITE_URL}/api/projects/${projectId}/auth/oauth/callback`;
  const providers = await adminListProjectProviders(me.activeOrgId, projectId).catch(
    () => [],
  );

  return (
    <SetupKeys
      projectId={projectId}
      callbackUrl={callbackUrl}
      initialProviders={providers}
      wallUrl="https://feedback.librebase.xyz"
    />
  );
}
