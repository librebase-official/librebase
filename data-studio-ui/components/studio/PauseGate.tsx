import { LaunchButton } from "@/components/LaunchButton";
import { EmptyState } from "@/components/studio/EmptyState";
import { probeProjectDb } from "@/lib/project-runtime";

export async function PauseGate({
  projectId,
  projectName,
  children,
}: {
  projectId: string;
  projectName: string;
  children: React.ReactNode;
}) {
  const probe = await probeProjectDb(projectId);
  if (probe.reachable) return <>{children}</>;

  return (
    <EmptyState
      title={`Project “${projectName}” is paused`}
      facts={[
        "Data on disk is untouched.",
        probe.message || "The runtime did not answer a health probe.",
        "Start the project to query tables, run SQL, and serve the API.",
      ]}
      actions={
        <LaunchButton
          href={`/api/projects/${projectId}/launch`}
          label="Start project"
        />
      }
    />
  );
}
