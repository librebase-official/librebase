"use client";

import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import type { Host, Instance } from "@/lib/types";

function NewInstancePageInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [name, setName] = useState("");
  const [hostId, setHostId] = useState(searchParams.get("hostId") ?? "");
  const [memLimitMb, setMemLimitMb] = useState(256);
  const [hosts, setHosts] = useState<Host[]>([]);
  const [instances, setInstances] = useState<Instance[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch("/api/hosts").then((r) => r.json()),
      fetch("/api/instances").then((r) => r.json()),
    ])
      .then(([hostData, instData]) => {
        setHosts((hostData as { hosts?: Host[] }).hosts ?? []);
        setInstances((instData as { instances?: Instance[] }).instances ?? []);
      })
      .catch(() => {
        setHosts([]);
        setInstances([]);
      });
  }, []);

  const selectedHost = hosts.find((h) => h.id === hostId);
  const remainingMb = selectedHost ? selectedHost.memMb - selectedHost.memUsedMb : undefined;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const res = await fetch("/api/instances", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, hostId, memLimitMb }),
      });
      const data = (await res.json()) as { instance?: { id: string }; error?: string };
      if (!res.ok) {
        setError(data.error ?? "Failed to create instance");
        return;
      }
      router.push("/instances");
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
          <h1>New instance</h1>
          <p className="muted">
            Launch a Librebase instance — place it on a rented VM and reserve its memory limit.
          </p>
        </div>
      </div>

      <form className="form" onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="name">Instance name</label>
          <input
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="app-runtime"
            required
          />
        </div>

        <div className="field">
          <label htmlFor="hostId">Host VM</label>
          <select id="hostId" value={hostId} onChange={(e) => setHostId(e.target.value)} required>
            <option value="">Select a VM…</option>
            {hosts.map((host) => (
              <option key={host.id} value={host.id}>
                {host.name} · {host.memUsedMb}/{host.memMb} MB used
              </option>
            ))}
          </select>
          {selectedHost && remainingMb !== undefined && (
            <p className="muted" style={{ fontSize: "0.85rem", marginTop: "0.25rem" }}>
              {remainingMb} MB free on {selectedHost.name}
            </p>
          )}
        </div>

        <div className="field">
          <label htmlFor="memLimitMb">Memory limit (MB)</label>
          <input
            id="memLimitMb"
            type="number"
            min={64}
            max={remainingMb ?? 2048}
            step={64}
            value={memLimitMb}
            onChange={(e) => setMemLimitMb(Number(e.target.value))}
            required
          />
          {remainingMb !== undefined && memLimitMb > remainingMb && (
            <p className="alert warn" style={{ fontSize: "0.85rem", marginTop: "0.25rem" }}>
              Exceeds the {remainingMb} MB free on this VM.
            </p>
          )}
        </div>

        <div className="field">
          <label>Existing instances on this host</label>
          <ul style={{ fontSize: "0.85rem", margin: 0, paddingLeft: "1rem" }}>
            {instances.filter((i) => i.hostId === hostId).length === 0 ? (
              <li>None yet — this is the first instance on this VM.</li>
            ) : (
              instances
                .filter((i) => i.hostId === hostId)
                .map((inst) => (
                  <li key={inst.id}>
                    {inst.name} · {inst.memLimitMb ?? "—"} MB · {inst.status}
                  </li>
                ))
            )}
          </ul>
        </div>

        {error && <div className="alert warn">{error}</div>}

        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? "Launching…" : "Launch instance"}
        </button>
      </form>
    </>
  );
}

export default function NewInstancePage() {
  return (
    <Suspense fallback={null}>
      <NewInstancePageInner />
    </Suspense>
  );
}
