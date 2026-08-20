"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

const VM_SIZES = [
  { label: "512 MB (small)", value: 512 },
  { label: "1 GB", value: 1024 },
  { label: "2 GB", value: 2048 },
];

export default function NewHostPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [region, setRegion] = useState("eu-west-1");
  const [provider, setProvider] = useState("linative-cloud");
  const [memMb, setMemMb] = useState(512);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const res = await fetch("/api/hosts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, region, provider, memMb }),
      });
      const data = (await res.json()) as { host?: { id: string }; error?: string };
      if (!res.ok) {
        setError(data.error ?? "Failed to rent VM");
        return;
      }
      router.push("/hosts");
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
          <h1>Rent a VM</h1>
          <p className="muted">
            Rent a VM from us, then launch multiple Librebase instances onto it and manage its
            memory budget from the dashboard.
          </p>
        </div>
      </div>

      <form className="form" onSubmit={handleSubmit}>
        <div className="field">
          <label htmlFor="name">VM name</label>
          <input
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="prod-vm-1"
            required
          />
        </div>

        <div className="field">
          <label htmlFor="memMb">Memory budget</label>
          <select id="memMb" value={memMb} onChange={(e) => setMemMb(Number(e.target.value))}>
            {VM_SIZES.map((size) => (
              <option key={size.value} value={size.value}>
                {size.label}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="provider">Provider</label>
          <select id="provider" value={provider} onChange={(e) => setProvider(e.target.value)}>
            <option value="linative-cloud">Linative Cloud</option>
            <option value="sail">Sail</option>
            <option value="self-host">Self-hosted</option>
          </select>
        </div>

        <div className="field">
          <label htmlFor="region">Region</label>
          <select id="region" value={region} onChange={(e) => setRegion(e.target.value)}>
            <option value="eu-west-1">EU West</option>
            <option value="us-east-1">US East</option>
          </select>
        </div>

        {error && <div className="alert warn">{error}</div>}

        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? "Renting…" : "Rent VM"}
        </button>
      </form>
    </>
  );
}
