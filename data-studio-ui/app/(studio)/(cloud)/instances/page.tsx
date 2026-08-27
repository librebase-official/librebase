import { redirect } from "next/navigation";
import { InstancesDashboard, type InstanceRow } from "@/components/studio/InstancesDashboard";
import { getInstanceStatus } from "@/lib/k8s-provisioner";
import { listInstancesAsync } from "@/lib/instances-store";
import { listHostsAsync } from "@/lib/hosts-store";
import { listProjectsByInstanceAsync } from "@/lib/projects-store";
import { resolveStudioOrgId } from "@/lib/org-context";
import { probeInstanceDbSafe } from "@/lib/project-runtime";
import { getLibrebaseRuntime, getK8sContainerRuntime, runtimeBackendLabel } from "@/lib/runtime-env";

export const dynamic = "force-dynamic";

export default async function InstancesPage() {
  const orgId = await resolveStudioOrgId();
  let instances;
  try {
    instances = await listInstancesAsync(orgId);
  } catch {
    redirect("/login");
  }
  const defaultRuntime = getLibrebaseRuntime();
  const k8sRuntime = getK8sContainerRuntime();
  const hosts = await listHostsAsync(orgId).catch(() => [] as never[]);

  const rows: InstanceRow[] = await Promise.all(
    instances.map(async (instance) => {
      const probe = await probeInstanceDbSafe(instance);
      const linked = await listProjectsByInstanceAsync(instance.id, orgId);
      const backend = runtimeBackendLabel(instance.runtimeTarget, k8sRuntime);
      const k8s =
        instance.runtimeTarget === "kubernetes" ? getInstanceStatus(instance.id) : undefined;
      const k8sLine =
        instance.runtimeTarget === "kubernetes"
          ? `K8s: ${instance.k8sNamespace ?? k8s?.namespace ?? "—"}${k8s?.podPhase ? ` · pod ${k8s.podPhase}` : ""}${instance.k8sDegraded || k8s?.degraded ? " · degraded" : ""}`
          : undefined;
      return { instance, probe, linkedCount: linked.length, backend, k8sLine };
    }),
  );

  return (
    <InstancesDashboard
      initialRows={rows}
      initialHosts={hosts}
      defaultRuntime={defaultRuntime}
    />
  );
}
