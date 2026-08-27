"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button, FormField, Input, Select } from "@/components/ui";
import { PageHeader } from "@/components/studio/PageHeader";

const VM_SIZES = [
  { label: "512 MB (small)", value: 512 },
  { label: "1 GB", value: 1024 },
  { label: "2 GB", value: 2048 },
];

const PROVIDERS: { value: string; label: string }[] =
  // SaaS harness is Hetzner-only (upsell). OSS can use local/k8s via LIBREBASE_HARNESS=oss.
  (process.env.NEXT_PUBLIC_HARNESS === "oss" ||
  process.env.NEXT_PUBLIC_HARNESS === "local" ||
  process.env.NEXT_PUBLIC_HARNESS === "k8s"
    ? [
        { value: "hetzner", label: "Hetzner Cloud (provisioned VM)" },
        { value: "linative-cloud", label: "Linative Cloud (bookkeeping)" },
        { value: "sail", label: "Sail (bookkeeping)" },
        { value: "self-host", label: "Self-hosted (bookkeeping)" },
      ]
    : [{ value: "hetzner", label: "Hetzner Cloud (provisioned VM)" }]);

export default function NewHostPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [region, setRegion] = useState("nbg1");
  const [provider, setProvider] = useState("hetzner");
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
      const data = (await res.json()) as { host?: { id: string; status: string }; error?: string };
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

  const isHetzner = provider === "hetzner";

  return (
    <>
      <PageHeader
        title="Rent a VM"
        description="Reserve a machine, then launch multiple instances onto it and manage the memory budget from the dashboard."
      />

      <form className="form" onSubmit={handleSubmit}>
        <FormField label="VM name" htmlFor="name">
          <Input
            id="name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="prod-vm-1"
            required
            disabled={submitting}
          />
        </FormField>

        <FormField label="Memory budget" htmlFor="memMb">
          <Select
            id="memMb"
            value={memMb}
            onChange={(e) => setMemMb(Number(e.target.value))}
            disabled={submitting}
          >
            {VM_SIZES.map((size) => (
              <option key={size.value} value={size.value}>
                {size.label}
              </option>
            ))}
          </Select>
        </FormField>

        <FormField label="Provider" htmlFor="provider" hint={isHetzner ? "Hetzner VMs are provisioned on real cloud hardware; the host agent registers automatically when booted." : "Bookkeeping-only — no VM is provisioned. Use for local development."}>
          <Select
            id="provider"
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            disabled={submitting}
          >
            {PROVIDERS.map((p) => (
              <option key={p.value} value={p.value}>
                {p.label}
              </option>
            ))}
          </Select>
        </FormField>

        {isHetzner ? (
          <FormField label="Region" htmlFor="region">
            <Select
              id="region"
              value={region}
              onChange={(e) => setRegion(e.target.value)}
              disabled={submitting}
            >
              <option value="nbg1">Nuremberg (nbg1)</option>
              <option value="fsn1">Falkenstein (fsn1)</option>
              <option value="hel1">Helsinki (hel1)</option>
            </Select>
          </FormField>
        ) : (
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
        )}

        {error && <p className="auth-error">{error}</p>}

        <Button type="submit" variant="primary" disabled={submitting}>
          {submitting ? "Renting…" : "Rent VM"}
        </Button>
      </form>
    </>
  );
}
