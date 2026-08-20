import Link from "next/link";
import { listInstancesAsync } from "@/lib/instances-store";
import { listProjectsAsync } from "@/lib/projects-store";
import { resolveStudioOrgId } from "@/lib/org-context";
import { probeInstanceDb } from "@/lib/project-runtime";

export const dynamic = "force-dynamic";

export default async function ProjectsHomePage() {
  const orgId = await resolveStudioOrgId();
  const projects = await listProjectsAsync(orgId);
  const instances = await listInstancesAsync(orgId);
  const instanceMap = new Map(instances.map((i) => [i.id, i]));

  const rows = await Promise.all(
    projects.map(async (project) => {
      const instance = instanceMap.get(project.instanceId);
      const probe = instance
        ? await probeInstanceDb(instance)
        : {
            reachable: false,
            status: "unknown" as const,
            degraded: true,
            message: "Instance missing",
          };
      return { project, instance, probe };
    }),
  );

  return (
    <>
      <div className="page-header">
        <div>
          <h1>Projects</h1>
          <p className="muted">Name a project. Link an agent. That is the product.</p>
        </div>
        <Link href="/projects/new" className="btn btn-primary">
          New project
        </Link>
      </div>

      {rows.length === 0 ? (
        <div className="empty">
          <p>No projects yet. Name one and you can paste an agent snippet on the next screen.</p>
          <Link href="/projects/new" className="btn btn-primary">
            Create your first project
          </Link>
        </div>
      ) : (
        <div className="card-grid">
          {rows.map(({ project, instance, probe }) => (
            <Link
              key={project.id}
              href={`/projects/${project.id}`}
              className="card"
              style={{ textDecoration: "none", color: "inherit" }}
            >
              <h2>{project.name}</h2>
              <p className="muted" style={{ margin: "0.25rem 0 0.75rem", fontSize: "0.85rem" }}>
                {project.region} · {project.deploymentMode}
              </p>
              <span className={`badge ${probe.status}`}>
                {probe.reachable ? "Running" : probe.status}
              </span>
              {instance && (
                <p className="muted" style={{ marginTop: "0.75rem", fontSize: "0.8rem" }}>
                  Instance: {instance.name}
                </p>
              )}
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
