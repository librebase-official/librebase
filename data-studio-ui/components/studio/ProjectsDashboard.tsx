"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import { DeleteButton } from "@/components/studio/DeleteButton";
import { EmptyState } from "@/components/studio/EmptyState";
import { LiveBadge } from "@/components/studio/LiveBadge";
import { PageHeader } from "@/components/studio/PageHeader";
import { IconPlus } from "@/components/studio/icons";
import { hostIsProvisioning, liveInstanceView } from "@/lib/live-status";
import { useInterval } from "@/lib/use-interval";
import type { DbProbeResult, Host, Instance, Project } from "@/lib/types";

export type ProjectRow = {
  project: Project;
  instance?: Instance;
  probe: DbProbeResult;
};

export function ProjectsDashboard({
  initialRows,
  initialHosts,
}: {
  initialRows: ProjectRow[];
  initialHosts: Host[];
}) {
  const [rows, setRows] = useState(initialRows);
  const [hosts, setHosts] = useState(initialHosts);

  const refresh = useCallback(async () => {
    try {
      const hRes = await fetch("/api/hosts");
      if (hRes.ok) {
        const data = (await hRes.json()) as { hosts?: Host[] };
        setHosts(data.hosts ?? []);
      }
    } catch {
      /* keep last good snapshot */
    }
  }, []);

  const hostById = new Map(hosts.map((h) => [h.id, h]));
  const waiting = rows.some((row) => hostIsProvisioning(hostById.get(row.instance?.hostId ?? "")));
  useInterval(refresh, waiting ? 3000 : null);

  return (
    <>
      <PageHeader
        title="Projects"
        description="Dedicated or shared runtimes for this organization. Status is a live probe — not a painted badge."
        actions={
          <Link href="/projects/new" className="btn btn-primary">
            <IconPlus width="14" height="14" />
            New project
          </Link>
        }
      />

      {rows.length === 0 ? (
        <EmptyState
          title="No projects yet"
          body="Create a project to get an API URL, a Postgres connection, and a table editor."
          facts={[
            "A project is a named workspace on a runtime.",
            "You can dedicate a new instance or share an existing database.",
          ]}
          actions={
            <Link href="/projects/new" className="btn btn-primary">
              Create your first project
            </Link>
          }
        />
      ) : (
        <div className="card-grid">
          {rows.map(({ project, instance, probe }) => {
            const host = instance?.hostId ? hostById.get(instance.hostId) : undefined;
            const view = liveInstanceView({
              host,
              reachable: probe.reachable,
              status: probe.status,
              persistedStatus: instance?.status,
            });
            return (
              <article key={project.id} className="card project-card">
                <div className="instance-card-header">
                  <Link href={`/projects/${project.id}`} className="project-card-link">
                    <h2>{project.name}</h2>
                  </Link>
                  <DeleteButton
                    href={`/api/projects/${project.id}`}
                    confirmTitle={`Delete “${project.name}”?`}
                    confirmBody="This permanently removes the project workspace. Data is not recoverable."
                    label="Delete project"
                    onSuccess={() => setRows((prev) => prev.filter((r) => r.project.id !== project.id))}
                  />
                </div>
                <Link href={`/projects/${project.id}`} className="project-card-link">
                  <p className="muted text-sm mt-1">
                    {project.region} · {project.deploymentMode}
                  </p>
                  <LiveBadge
                    variant={view.variant}
                    label={view.label}
                    spinner={view.spinner}
                    className="mt-2"
                  />
                  {instance && <p className="muted text-sm mt-2">{instance.name}</p>}
                </Link>
              </article>
            );
          })}
        </div>
      )}
    </>
  );
}
