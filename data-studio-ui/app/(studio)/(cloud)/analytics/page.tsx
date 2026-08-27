import { PageHeader } from "@/components/studio/PageHeader";
import { AnalyticsDashboard } from "@/components/studio/AnalyticsDashboard";

export const dynamic = "force-dynamic";

export default async function AnalyticsPage({
  searchParams,
}: {
  searchParams?: Promise<{ projectId?: string }>;
}) {
  const params = searchParams ? await searchParams : {};
  const projectId = params?.projectId ?? undefined;
  return (
    <>
      <PageHeader
        title="Analytics"
        description={
          projectId
            ? `Project analytics for ${projectId} — aggregate stats from the access-log JSONL and Librebase runtime.`
            : "Aggregate stats derived from the access-log JSONL sink plus Librebase runtime events."
        }
      />
      <AnalyticsDashboard projectId={projectId} />
    </>
  );
}
