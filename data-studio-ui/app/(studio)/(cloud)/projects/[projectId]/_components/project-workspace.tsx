import Link from "next/link";
import { CopyField } from "@/components/CopyField";
import { LaunchButton } from "@/components/LaunchButton";
import { DeleteButton } from "@/components/studio/DeleteButton";
import { AgentChat } from "@/components/studio/AgentChat";
import { HandoffPrompt } from "@/components/studio/HandoffPrompt";
import { Badge } from "@/components/ui/badge";
import type { DbProbeResult, Instance, Project } from "@/lib/types";

export function ProjectWorkspace({
  project,
  instance,
  probe,
  urls,
}: {
  project: Project;
  instance?: Instance;
  probe: DbProbeResult;
  urls: { apiUrl: string; postgresUrl: string } | null;
}) {
  const healthy = probe.reachable;

  return (
    <div className="agent-view">
      <section className="agent-col agent-col-info" aria-label="Project">
        <header className="agent-info-head">
          <div>
            <div className="agent-info-title">
              <span className={`status-dot ${probe.status}`} />
              <h1>{project.name}</h1>
              <Badge
                variant={
                  healthy ? "running" : probe.status === "starting" ? "starting" : "stopped"
                }
              >
                {healthy ? "Healthy" : probe.status === "starting" ? "Starting" : "Paused"}
              </Badge>
            </div>
            <p>
              {project.region} · {project.deploymentMode}
              {instance?.hostId ? " · VM" : " · local"}
            </p>
          </div>
          <div className="agent-info-actions">
            {!healthy ? (
              <LaunchButton
                href={`/api/projects/${project.id}/launch`}
                label="Start"
                className="btn btn-primary btn-sm"
              />
            ) : null}
            <DeleteButton
              href={`/api/projects/${project.id}`}
              confirmTitle={`Delete “${project.name}”?`}
              confirmBody="This permanently removes the project workspace. Data is not recoverable."
              label="Delete project"
              redirectTo="/projects"
            />
          </div>
        </header>

        {!healthy && probe.message ? (
          <p className="agent-callout">{probe.message}</p>
        ) : null}

        <dl className="agent-meta">
          {urls ? (
            <>
              <div>
                <dt>API</dt>
                <dd>
                  <CopyField label="" value={urls.apiUrl} />
                </dd>
              </div>
              <div>
                <dt>Postgres</dt>
                <dd>
                  <CopyField label="" value={urls.postgresUrl} />
                </dd>
              </div>
            </>
          ) : (
            <div>
              <dt>Connect</dt>
              <dd className="muted">Start the project to get URLs.</dd>
            </div>
          )}
          {instance ? (
            <div>
              <dt>Instance</dt>
              <dd>
                {instance.name}
                <span className="muted">
                  {" "}
                  · API {instance.ports.api} · Postgres {instance.ports.postgres}
                </span>
              </dd>
            </div>
          ) : null}
        </dl>

        <nav className="agent-links" aria-label="Project shortcuts">
          <Link href={`/projects/${project.id}/sql`}>SQL</Link>
          <Link href={`/projects/${project.id}/database`}>Tables</Link>
          <Link href={`/projects/${project.id}/auth`}>Auth</Link>
          <Link href={`/analytics?projectId=${project.id}`}>Analytics</Link>
        </nav>

        <HandoffPrompt
          orgId={project.orgId}
          projectId={project.id}
          projectName={project.name}
          instanceId={project.instanceId}
          deploymentMode={project.deploymentMode}
          region={project.region}
          apiUrl={urls?.apiUrl ?? null}
          postgresUrl={urls?.postgresUrl ?? null}
        />
      </section>

      <section className="agent-col agent-col-chat" aria-label="Agent">
        <div className="agent-chat-head">Agent</div>
        <AgentChat projectId={project.id} className="agent-chat-column" />
      </section>
    </div>
  );
}
