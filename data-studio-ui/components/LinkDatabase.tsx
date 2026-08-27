"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button, FormField, Select } from "@/components/ui";
import type { Instance } from "@/lib/types";

export function LinkDatabase({
  projectId,
  currentInstanceId,
  currentInstanceName,
}: {
  projectId: string;
  currentInstanceId?: string;
  currentInstanceName?: string;
}) {
  const router = useRouter();
  const [instances, setInstances] = useState<Instance[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selected, setSelected] = useState(currentInstanceId ?? "");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/instances")
      .then(async (r) => {
        if (!r.ok) throw new Error("Failed to load databases");
        const data = (await r.json()) as { instances?: Instance[] };
        setInstances(data.instances ?? []);
        if (data.instances?.length === 1 && !currentInstanceId) {
          setSelected(data.instances[0].id);
        }
      })
      .catch((e: Error) => setLoadError(e.message));
  }, [currentInstanceId]);

  async function link() {
    if (!selected) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const res = await fetch(`/api/projects/${projectId}/link`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ instanceId: selected }),
      });
      const data = (await res.json()) as { error?: string };
      if (!res.ok) {
        setError(data.error ?? "Failed to link database");
        return;
      }
      setMessage("Database linked");
      router.refresh();
    } catch {
      setError("Request failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card">
      <p style={{ margin: "0 0 0.5rem" }}>
        <strong>{currentInstanceName ?? "No database linked"}</strong>
      </p>
      <p className="muted text-sm" style={{ margin: "0 0 0.75rem" }}>
        Link this project to one of your databases. A project uses one database at a time.
      </p>

      {loadError ? (
        <p className="auth-error text-sm">{loadError}</p>
      ) : instances.length === 0 ? (
        <p className="muted text-sm">
          No databases yet.{" "}
          <Link href="/instances/new">Create a database</Link> first, then link it here.
        </p>
      ) : (
        <>
          <FormField label="Database" htmlFor="db-select">
            <Select
              id="db-select"
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
            >
              <option value="">Select a database…</option>
              {instances.map((inst) => (
                <option key={inst.id} value={inst.id}>
                  {inst.name} ({inst.status})
                  {inst.id === currentInstanceId ? " · linked" : ""}
                </option>
              ))}
            </Select>
          </FormField>
          <div className="mt-3">
            <Button
              variant="primary"
              size="sm"
              onClick={link}
              disabled={busy || !selected || selected === currentInstanceId}
            >
              {busy ? "Linking…" : "Link database"}
            </Button>
            {message && (
              <span className="muted text-sm" style={{ marginLeft: "0.75rem" }}>
                {message}
              </span>
            )}
            {error && (
              <span
                className="auth-error text-sm"
                style={{ display: "inline-block", marginLeft: "0.75rem" }}
              >
                {error}
              </span>
            )}
          </div>
        </>
      )}
    </div>
  );
}
