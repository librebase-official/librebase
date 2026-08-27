"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Button, FormField, Input, Select, Alert } from "@/components/ui";
import { HostSelector } from "@/components/HostSelector";
import { PageHeader } from "@/components/studio/PageHeader";
import type { Host, Instance } from "@/lib/types";

type RuntimeChoice = "new" | "existing" | "vm";

export default function NewProjectPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [region, setRegion] = useState("local");
  const [runtimeChoice, setRuntimeChoice] = useState<RuntimeChoice>("new");
  const [instanceId, setInstanceId] = useState("");
  const [instances, setInstances] = useState<Instance[]>([]);
  const [hosts, setHosts] = useState<Host[]>([]);
  const [vmDialogOpen, setVmDialogOpen] = useState(false);
  const [selectedHostId, setSelectedHostId] = useState<string | null>(null);
  const [selectedMemLimit, setSelectedMemLimit] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetch("/api/instances")
      .then((r) => r.json())
      .then((data: { instances?: Instance[] }) => {
        setInstances(data.instances ?? []);
      })
      .catch(() => setInstances([]));
  }, []);

  useEffect(() => {
    fetch("/api/hosts")
      .then((r) => r.json())
      .then((data: { hosts?: Host[] }) => {
        setHosts(
          (data.hosts ?? []).filter(
            (h) => h.status === "running" && h.ip && h.provider === "hetzner",
          ),
        );
      })
      .catch(() => setHosts([]));
  }, []);

  function pickVms() {
    setVmDialogOpen(true);
  }

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
          runtime: "local",
          hostId: runtimeChoice === "vm" ? selectedHostId : undefined,
          memLimitMb: runtimeChoice === "vm" ? selectedMemLimit : undefined,
        }),
      });
      const data = (await res.json()) as {
        project?: { id: string };
        error?: string;
      };
      if (!res.ok) {
        setError(data.error ?? "Failed to create project");
        return;
      }
      router.push(`/projects/${data.project!.id}?onboarded=1`);
      router.refresh();
    } catch {
      setError("Request failed");
    } finally {
      setSubmitting(false);
    }
  }

  const canSubmit =
    name.trim().length > 0 &&
    !(runtimeChoice === "existing" && !instanceId) &&
    !(runtimeChoice === "vm" && !selectedHostId);

  return (
    <>
      <PageHeader
        title="New project"
        description="Provision a dedicated runtime or attach to an existing instance."
      />

      <form className="form" onSubmit={handleSubmit}>
        <FormField label="Project name" htmlFor="name">
          <Input
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="My app"
            required
            disabled={submitting}
          />
        </FormField>

        <FormField label="Region" htmlFor="region">
          <Select
            id="region"
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            disabled={submitting}
          >
            <option value="local">Local</option>
            <option value="us-east-1">US East</option>
            <option value="eu-west-1">EU West</option>
          </Select>
        </FormField>

        <fieldset
          className="field"
          style={{ border: "none", padding: 0, margin: 0 }}
        >
          <legend
            style={{ fontSize: "0.85rem", color: "var(--muted)", marginBottom: "0.5rem" }}
          >
            Runtime
          </legend>
          <p
            className="muted"
            style={{ margin: "0 0 0.5rem", fontSize: "0.82rem" }}
          >
            Default: a dedicated local runtime (no VM needed). Rent a Hetzner VM or
            link an existing database only if you want to.
          </p>
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
                <p
                  className="muted"
                  style={{ margin: "0.25rem 0 0", fontSize: "0.85rem" }}
                >
                  Dedicated 1:1 — new data dir and port block
                </p>
              </div>
            </label>

            <label
              className={`radio-option${runtimeChoice === "vm" ? " selected" : ""}`}
            >
              <input
                type="radio"
                name="runtime"
                value="vm"
                checked={runtimeChoice === "vm"}
                onChange={() => setRuntimeChoice("vm")}
              />
              <div style={{ flex: 1 }}>
                <strong>Provision on a VM</strong>
                <p
                  className="muted"
                  style={{ margin: "0.25rem 0 0.5rem", fontSize: "0.85rem" }}
                >
                  Dedicated instance placed on a rented VM (Hetzner)
                </p>
                {runtimeChoice === "vm" && (
                  <div style={{ marginTop: "0.5rem" }}>
                    <Button
                      type="button"
                      variant={selectedHostId ? "primary" : "secondary"}
                      size="sm"
                      onClick={pickVms}
                    >
                      {selectedHostId
                        ? `${hosts.find((h) => h.id === selectedHostId)?.name ?? "VM selected"}`
                        : "Select a VM…"}
                    </Button>
                    {selectedHostId && (
                      <p
                        className="muted"
                        style={{ marginTop: "0.25rem", fontSize: "0.82rem" }}
                      >
                        {selectedMemLimit} MB reserved
                      </p>
                    )}
                  </div>
                )}
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
                <strong>Link to existing database</strong>
                <p
                  className="muted"
                  style={{ margin: "0.25rem 0 0.5rem", fontSize: "0.85rem" }}
                >
                  Shared runtime — multiple projects on one database
                </p>
                {runtimeChoice === "existing" && (
                  <>
                    {instances.length === 0 ? (
                      <p className="muted" style={{ fontSize: "0.85rem" }}>
                        No databases yet.{" "}
                        <Link href="/instances/new">Create a database</Link> first.
                      </p>
                    ) : (
                      <Select
                        value={instanceId}
                        onChange={(e) => setInstanceId(e.target.value)}
                        required
                      >
                        <option value="">Select a database…</option>
                        {instances.map((inst) => (
                          <option key={inst.id} value={inst.id}>
                            {inst.name} ({inst.status})
                          </option>
                        ))}
                      </Select>
                    )}
                  </>
                )}
              </div>
            </label>
          </div>
        </fieldset>

        {error && <Alert variant="error">{error}</Alert>}

        <Button
          type="submit"
          variant="primary"
          disabled={submitting || !canSubmit}
        >
          {submitting ? "Creating…" : "Create project"}
        </Button>
      </form>

      <HostSelector
        open={vmDialogOpen}
        onClose={() => setVmDialogOpen(false)}
        onSelect={(info) => {
          setSelectedHostId(info.hostId);
          setSelectedMemLimit(info.memLimitMb);
        }}
        selectedHostId={selectedHostId ?? undefined}
        selectedMemLimitMb={selectedMemLimit ?? undefined}
      />
    </>
  );
}
