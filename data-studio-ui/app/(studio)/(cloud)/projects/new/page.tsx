"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { Instance } from "@/lib/types";

type RuntimeChoice = "new" | "existing";

export default function NewProjectPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [region, setRegion] = useState("local");
  const [runtimeChoice, setRuntimeChoice] = useState<RuntimeChoice>("new");
  const [instanceId, setInstanceId] = useState("");
  const [instances, setInstances] = useState<Instance[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetch("/api/instances")
      .then((r) => r.json())
      .then((data: { instances?: Instance[] }) => setInstances(data.instances ?? []))
      .catch(() => setInstances([]));
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const res = await fetch("/api/projects", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          region,
          runtimeChoice,
          instanceId: runtimeChoice === "existing" ? instanceId : undefined,
        }),
      });
      const data = (await res.json()) as { project?: { id: string }; error?: string };
      if (!res.ok) {
        setError(data.error ?? "Failed to create project");
        return;
      }
      router.push(`/projects/${data.project!.id}`);
      router.refresh();
    } catch {
      setError("Request failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1>New project</h1>
          <p className="muted">Provision a dedicated runtime or attach to an existing instance</p>
        </div>
      </div>

      <form className="form" onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="name">Project name</label>
          <input
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="My app"
            required
          />
        </div>

        <div className="field">
          <label htmlFor="region">Region</label>
          <select id="region" value={region} onChange={(e) => setRegion(e.target.value)}>
            <option value="local">Local</option>
            <option value="us-east-1">US East</option>
            <option value="eu-west-1">EU West</option>
          </select>
        </div>

        <fieldset className="field" style={{ border: "none", padding: 0, margin: 0 }}>
          <legend style={{ fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.5rem" }}>
            Runtime
          </legend>
          <div className="radio-group">
            <label
              className={`radio-option${runtimeChoice === "new" ? " selected" : ""}`}
            >
              <input
                type="radio"
                name="runtime"
                value="new"
                checked={runtimeChoice === "new"}
                onChange={() => setRuntimeChoice("new")}
              />
              <div>
                <strong>New instance</strong>
                <p className="muted" style={{ margin: "0.25rem 0 0", fontSize: "0.85rem" }}>
                  Dedicated 1:1 — new data dir and port block (Supabase-like default)
                </p>
              </div>
            </label>

            <label
              className={`radio-option${runtimeChoice === "existing" ? " selected" : ""}`}
            >
              <input
                type="radio"
                name="runtime"
                value="existing"
                checked={runtimeChoice === "existing"}
                onChange={() => setRuntimeChoice("existing")}
              />
              <div style={{ flex: 1 }}>
                <strong>Add to existing instance</strong>
                <p className="muted" style={{ margin: "0.25rem 0 0.5rem", fontSize: "0.85rem" }}>
                  Shared runtime — multiple projects on one lidb embed
                </p>
                {runtimeChoice === "existing" && (
                  <select
                    value={instanceId}
                    onChange={(e) => setInstanceId(e.target.value)}
                    required
                  >
                    <option value="">Select instance…</option>
                    {instances.map((inst) => (
                      <option key={inst.id} value={inst.id}>
                        {inst.name} ({inst.status})
                      </option>
                    ))}
                  </select>
                )}
              </div>
            </label>
          </div>
        </fieldset>

        {error && <div className="alert warn">{error}</div>}

        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? "Creating…" : "Create project"}
        </button>
      </form>
    </>
  );
}
