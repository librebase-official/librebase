"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

export default function NewProjectPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

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
          region: "eu-west-1",
          runtimeChoice: "new",
          runtime: "kubernetes",
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
          <p className="muted">Name it. We provision in the background. Then link an agent.</p>
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
            autoFocus
            disabled={submitting}
          />
        </div>

        {error && <div className="alert warn">{error}</div>}

        <button
          type="submit"
          className="btn btn-primary"
          disabled={submitting || name.trim().length === 0}
        >
          {submitting ? "Creating…" : "Create project"}
        </button>
      </form>
    </>
  );
}
