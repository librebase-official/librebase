"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { CopyField } from "@/components/CopyField";
import { LaunchButton } from "@/components/LaunchButton";
import { DeleteButton } from "@/components/studio/DeleteButton";
import { PauseButton } from "@/components/studio/PauseButton";
import { LinkDatabase } from "@/components/LinkDatabase";

export function SettingsForm({
  projectId,
  name,
  region,
  deploymentMode,
  instanceId,
  instanceName,
  reachable,
  apiUrl,
  postgresUrl,
  anonKey,
  serviceRoleKey,
}: {
  projectId: string;
  name: string;
  region: string;
  deploymentMode: string;
  instanceId: string;
  instanceName: string;
  reachable: boolean;
  apiUrl?: string;
  postgresUrl?: string;
  anonKey: string | null;
  serviceRoleKey: string | null;
}) {
  const router = useRouter();
  const [value, setValue] = useState(name);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const res = await fetch(`/api/projects/${projectId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: value }),
      });
      const body = (await res.json()) as { error?: string };
      if (!res.ok) {
        setError(body.error ?? "Save failed");
        return;
      }
      router.refresh();
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="st-settings">
      <h2 className="section-title">General</h2>
      <form className="st-panel" onSubmit={save}>
        <div className="st-row">
          <div className="st-row-copy">
            <strong>Project name</strong>
            <p>Displayed throughout the console.</p>
          </div>
          <input
            className="input"
            style={{ maxWidth: 280 }}
            value={value}
            onChange={(e) => setValue(e.target.value)}
          />
        </div>
        <div className="st-row">
          <div className="st-row-copy">
            <strong>Project ID</strong>
            <p>Stable identifier used in URLs and the API.</p>
          </div>
          <code className="mono text-sm">{projectId}</code>
        </div>
        <div className="st-row">
          <div className="st-row-copy">
            <strong>Region</strong>
            <p>Where the runtime is scheduled.</p>
          </div>
          <span>{region}</span>
        </div>
        <div className="st-row">
          <div className="st-row-copy">
            <strong>Deployment mode</strong>
            <p>Dedicated instance or shared runtime.</p>
          </div>
          <span>{deploymentMode}</span>
        </div>
        <div className="st-row">
          <button type="submit" className="btn btn-primary" disabled={saving || value.trim() === name}>
            {saving ? "Saving…" : "Save"}
          </button>
          {error ? <span className="auth-error">{error}</span> : null}
        </div>
      </form>

      <h2 className="section-title">API keys</h2>
      <div className="st-panel" style={{ padding: "8px 0" }}>
        {apiUrl ? <CopyField label="API URL" value={apiUrl} /> : null}
        {postgresUrl ? <CopyField label="Postgres" value={postgresUrl} /> : null}
        <CopyField label="Anon key" value={anonKey ?? "unset — set LIBREBASE_ANON_KEY"} />
        <CopyField
          label="Service role"
          value={serviceRoleKey ?? "unset — set LIBREBASE_SERVICE_ROLE_KEY"}
        />
      </div>

      <h2 className="section-title">Linked database</h2>
      <div className="st-panel" style={{ padding: 16 }}>
        <LinkDatabase
          projectId={projectId}
          currentInstanceId={instanceId}
          currentInstanceName={instanceName}
        />
      </div>

      <h2 className="section-title">Project availability</h2>
      <div className="st-panel">
        <div className="st-row">
          <div className="st-row-copy">
            <strong>{reachable ? "Running" : "Paused"}</strong>
            <p>Restart or pause this project when you do maintenance.</p>
          </div>
          {reachable ? (
            <PauseButton href={`/api/projects/${projectId}/pause`} label="Pause project" />
          ) : (
            <LaunchButton href={`/api/projects/${projectId}/launch`} label="Start project" className="btn btn-sm btn-primary" />
          )}
        </div>
      </div>

      <h2 className="section-title">Danger zone</h2>
      <div className="st-panel">
        <div className="st-row">
          <div className="st-row-copy">
            <strong>Delete project</strong>
            <p>Removes the project workspace. Data is not recoverable.</p>
          </div>
          <DeleteButton
            href={`/api/projects/${projectId}`}
            confirmTitle={`Delete “${name}”?`}
            confirmBody="This permanently removes the project workspace."
            label="Delete project"
            redirectTo="/projects"
          />
        </div>
      </div>
    </div>
  );
}
