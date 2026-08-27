import { redirect } from "next/navigation";
import { ProjectsDashboard, type ProjectRow } from "@/components/studio/ProjectsDashboard";
import { listHostsAsync } from "@/lib/hosts-store";
import { listInstancesAsync } from "@/lib/instances-store";
import { listProjectsAsync } from "@/lib/projects-store";
import { resolveStudioOrgId } from "@/lib/org-context";
import { probeInstanceDbSafe } from "@/lib/project-runtime";

export const dynamic = "force-dynamic";

export default async function ProjectsHomePage() {
  const orgId = await resolveStudioOrgId();
  let projects;
  let instances;
  let hosts;
  try {
    [projects, instances, hosts] = await Promise.all([
      listProjectsAsync(orgId),
      listInstancesAsync(orgId),
      listHostsAsync(orgId).catch(() => [] as never[]),
    ]);
  } catch {
    redirect("/login");
  }
  const instanceMap = new Map(instances.map((i) => [i.id, i]));

  const rows: ProjectRow[] = await Promise.all(
    projects.map(async (project) => {
      const instance = instanceMap.get(project.instanceId);
      const probe = instance
        ? await probeInstanceDbSafe(instance)
        : {
            reachable: false,
            status: "unknown" as const,
            degraded: true,
            message: "Instance missing",
          };
      return { project, instance, probe };
    }),
  );

  return <ProjectsDashboard initialRows={rows} initialHosts={hosts} />;
}
