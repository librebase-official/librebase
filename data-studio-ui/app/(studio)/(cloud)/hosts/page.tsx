import { redirect } from "next/navigation";
import { HostsDashboard } from "@/components/studio/HostsDashboard";
import { listHostsAsync } from "@/lib/hosts-store";
import { listInstancesAsync } from "@/lib/instances-store";
import { resolveStudioOrgId } from "@/lib/org-context";

export const dynamic = "force-dynamic";

export default async function HostsPage() {
  const orgId = await resolveStudioOrgId();
  let hosts;
  let instances;
  try {
    [hosts, instances] = await Promise.all([
      listHostsAsync(orgId),
      listInstancesAsync(orgId),
    ]);
  } catch {
    redirect("/login");
  }

  return <HostsDashboard initialHosts={hosts} initialInstances={instances} />;
}
