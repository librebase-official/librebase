"use client";

import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Button, FormField, Input, Select, Alert } from "@/components/ui";
import { PageHeader } from "@/components/studio/PageHeader";
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
  const runningHosts = hosts.filter(
    (h) => h.status === "running" && h.ip && h.provider === "hetzner",
  );

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
        setError(
          data.error ??
            (res.status === 409
              ? "Host memory budget exceeded. Choose a smaller instance or a bigger VM."
              : "Failed to create instance"),
        );
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
      <PageHeader
        title="New instance"
        description="Place a runtime on a rented VM and reserve its memory limit."
      />

      {runningHosts.length > 0 && (
        <Alert variant="info" className="mb-3">
          <p style={{ margin: 0 }}>
            {runningHosts.length} running {runningHosts.length === 1 ? "VM" : "VMs"} available. Select one
            below to place this instance on it.
          </p>
        </Alert>
      )}

      <form className="form" onSubmit={handleSubmit}>
        <FormField label="Instance name" htmlFor="name">
          <Input
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="app-runtime"
            required
            disabled={submitting}
          />
        </FormField>

        <FormField label="Host VM" htmlFor="hostId" hint={
          !hostId
            ? "Leave empty for a local runtime."
            : undefined
        }>
          <Select
            id="hostId"
            value={hostId}
            onChange={(e) => setHostId(e.target.value)}
          >
            <option value="">Local runtime (no VM)</option>
            {hosts.map((host) => {
              const busy = host.status === "provisioning" || host.status === "starting";
              return (
                <option key={host.id} value={host.id} disabled={busy}>
                  {host.name} · {host.memUsedMb}/{host.memMb} MB used · {host.status}
                </option>
              );
            })}
          </Select>
          {selectedHost && remainingMb !== undefined && (
            <p className="muted" style={{ fontSize: "0.85rem", marginTop: "0.25rem" }}>
              {remainingMb} MB free on {selectedHost.name}
            </p>
          )}
        </FormField>

        {selectedHost && remainingMb !== undefined && (
          <FormField
            label="Memory limit (MB)"
            htmlFor="memLimitMb"
            error={
              memLimitMb > remainingMb
                ? `Exceeds the ${remainingMb} MB free on ${selectedHost.name}.`
                : undefined
            }
          >
            <Input
              id="memLimitMb"
              type="number"
              min={64}
              max={remainingMb}
              step={64}
              value={memLimitMb}
              onChange={(e) => setMemLimitMb(Number(e.target.value))}
              disabled={submitting}
            />
          </FormField>
        )}

        {hostId && (
          <FormField label="Existing instances on this host" htmlFor="host-instances">
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
          </FormField>
        )}

        {error && <Alert variant="error">{error}</Alert>}

        <Button
          type="submit"
          variant="primary"
          disabled={submitting || (memLimitMb > (remainingMb ?? Infinity))}
        >
          {submitting ? "Launching…" : "Launch instance"}
        </Button>
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
