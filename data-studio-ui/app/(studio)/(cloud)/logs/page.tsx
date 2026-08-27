import { readAccessLogTail, resolveAccessLogPath } from "@/lib/access-log";
import { PageHeader } from "@/components/studio/PageHeader";
import { LogsTable } from "./logs-table";

export const dynamic = "force-dynamic";

export default async function LogsPage() {
  const filePath = resolveAccessLogPath();
  const lines = filePath ? readAccessLogTail(filePath, 200) : [];

  return (
    <>
      <PageHeader
        title="Logs"
        description="Access-log tail from the file sink. Filter by type and time. Not a fake live stream."
      />
      <LogsTable lines={lines} source={filePath} />
    </>
  );
}
