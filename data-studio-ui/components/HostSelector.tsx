"use client";

import { useEffect, useRef, useState } from "react";
import { Alert, Button, Dialog, DialogFooter, FormField, Input, Select } from "@/components/ui";
import type { Host } from "@/lib/types";

export interface SelectedHostInfo {
  hostId: string;
  memLimitMb: number;
}

export interface HostSelectorProps {
  open: boolean;
  onClose: () => void;
  onSelect: (info: SelectedHostInfo) => void;
  selectedHostId?: string;
  selectedMemLimitMb?: number;
}

const VM_SIZES = [
  { label: "512 MB", value: 512 },
  { label: "1 GB", value: 1024 },
  { label: "2 GB", value: 2048 },
];

const VM_REGIONS = [
  { value: "nbg1", label: "Nuremberg (nbg1)" },
  { value: "fsn1", label: "Falkenstein (fsn1)" },
  { value: "hel1", label: "Helsinki (hel1)" },
];

export function HostSelector({
  open,
  onClose,
  onSelect,
  selectedHostId,
  selectedMemLimitMb,
}: HostSelectorProps) {
  const [hosts, setHosts] = useState<Host[]>([]);
  const [canCreate, setCanCreate] = useState(true);
  const [loading, setLoading] = useState(false);
  const [hostId, setHostId] = useState(selectedHostId ?? "");
  const [memLimitMb, setMemLimitMb] = useState(selectedMemLimitMb ?? 256);
  const [error, setError] = useState<string | null>(null);

  // Inline "rent a new VM" state
  const [renting, setRenting] = useState(false);
  const [rentOpen, setRentOpen] = useState(false);
  const [vmName, setVmName] = useState("");
  const [vmRegion, setVmRegion] = useState("nbg1");
  const [vmMemMb, setVmMemMb] = useState(512);
  const [rentError, setRentError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  async function loadHosts(selectFirst = false) {
    try {
      const r = await fetch("/api/hosts");
      if (!r.ok) {
        // Stop polling on any error to avoid spamming the server (especially 401/500)
        if (pollRef.current) {
          clearInterval(pollRef.current);
          pollRef.current = null;
        }
        if (r.status === 401) {
          setHosts([]);
          return;
        }
        // For 500 or other errors, keep existing hosts but don't start new polling
        return;
      }
      const data = (await r.json()) as { hosts?: Host[]; canCreate?: boolean };
      const all = data.hosts ?? [];
      setCanCreate(data.canCreate !== false);
      const running = all.filter(
        (h) => h.status === "running" && h.ip && h.provider === "hetzner",
      );
      setHosts(all);
      if (selectFirst && running.length > 0) {
        setHostId((cur) => cur || running[0].id);
      }
      // Keep polling while any host is still provisioning/starting.
      const pending = all.some(
        (h) => h.status === "provisioning" || h.status === "starting",
      );
      if (pending && !pollRef.current) {
        pollRef.current = setInterval(() => loadHosts(false), 4000);
      } else if (!pending && pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    } catch {
      setHosts([]);
    }
  }

  useEffect(() => {
    if (!open) return;
    setLoading(true);
    loadHosts(true).finally(() => setLoading(false));
    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const runningHosts = hosts.filter(
    (h) => h.status === "running" && h.ip && h.provider === "hetzner",
  );
  const provisioningHosts = hosts.filter(
    (h) => h.status === "provisioning" || h.status === "starting",
  );
  const selectedHost = hosts.find((h) => h.id === hostId);
  const remainingMb = selectedHost
    ? selectedHost.memMb - selectedHost.memUsedMb
    : undefined;

  async function handleRent(e: React.FormEvent) {
    e.preventDefault();
    setRentError(null);
    setRenting(true);
    try {
      const res = await fetch("/api/hosts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: vmName.trim(),
          region: vmRegion,
          provider: "hetzner",
          memMb: vmMemMb,
        }),
      });
      const data = (await res.json()) as { host?: Host; error?: string; entitlement?: unknown };
      if (!res.ok) {
        const msg = data.error ?? "Failed to rent VM";
        // Surface entitlement upsell clearly
        if (msg.toLowerCase().includes("entitlement") || msg.toLowerCase().includes("paid plan")) {
          setCanCreate(false);
          setRentError("Renting a VM requires a paid plan. Open Admin to upgrade.");
        } else {
          setRentError(msg);
        }
        return;
      }
      const newHostId = data.host?.id;
      setVmName("");
      setRentOpen(false);
      if (newHostId) setHostId(newHostId);
      await loadHosts(false);
    } catch {
      setRentError("Request failed");
    } finally {
      setRenting(false);
    }
  }

  function handleSelect() {
    if (!hostId || !selectedHost || selectedHost.status !== "running") return;
    if (remainingMb !== undefined && memLimitMb > remainingMb) {
      setError(`Exceeds the ${remainingMb} MB free on ${selectedHost.name}.`);
      return;
    }
    setError(null);
    onSelect({ hostId, memLimitMb });
    onClose();
  }

  return (
    <Dialog
      open={open}
      onClose={() => {
        if (!loading) onClose();
      }}
      title="Provision a VM"
      description="Choose a running Hetzner VM, or rent a new one right here."
    >
      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        {loading ? (
          <p className="muted">Loading VMs…</p>
        ) : runningHosts.length === 0 && provisioningHosts.length === 0 ? (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            <p className="muted" style={{ margin: 0 }}>
              {canCreate
                ? "No VMs yet. Rent a Hetzner VM to place the project on real hardware."
                : "This organization can’t rent VMs yet. Upgrade the plan in Admin, then come back."}
            </p>
            <div>
              {canCreate ? (
                <Button variant="secondary" size="sm" onClick={() => setRentOpen(true)}>
                  Rent a VM…
                </Button>
              ) : (
                <a className="btn btn-primary btn-sm" href="/admin">
                  Upgrade in Admin
                </a>
              )}
            </div>
            {rentOpen && (
              <form
                className="st-panel"
                style={{ padding: 16, display: "flex", flexDirection: "column", gap: "0.75rem" }}
                onSubmit={handleRent}
              >
                <FormField label="VM name" htmlFor="vm-name-empty">
                  <Input
                    id="vm-name-empty"
                    value={vmName}
                    onChange={(e) => setVmName(e.target.value)}
                    placeholder="prod-vm-1"
                    required
                    disabled={renting}
                  />
                </FormField>
                <FormField label="Region" htmlFor="vm-region-empty">
                  <Select
                    id="vm-region-empty"
                    value={vmRegion}
                    onChange={(e) => setVmRegion(e.target.value)}
                    disabled={renting}
                  >
                    {VM_REGIONS.map((r) => (
                      <option key={r.value} value={r.value}>
                        {r.label}
                      </option>
                    ))}
                  </Select>
                </FormField>
                <FormField label="Memory budget" htmlFor="vm-mem-empty">
                  <Select
                    id="vm-mem-empty"
                    value={vmMemMb}
                    onChange={(e) => setVmMemMb(Number(e.target.value))}
                    disabled={renting}
                  >
                    {VM_SIZES.map((s) => (
                      <option key={s.value} value={s.value}>
                        {s.label}
                      </option>
                    ))}
                  </Select>
                </FormField>
                {rentError && <Alert variant="error">{rentError}</Alert>}
                <div style={{ display: "flex", gap: 8 }}>
                  <Button type="submit" variant="primary" size="sm" disabled={renting}>
                    {renting ? "Renting…" : "Rent VM"}
                  </Button>
                  <Button type="button" variant="ghost" size="sm" onClick={() => setRentOpen(false)} disabled={renting}>
                    Cancel
                  </Button>
                </div>
              </form>
            )}
          </div>
        ) : (
          <>
            <FormField label="Host VM" htmlFor="host-select">
              <Select
                id="host-select"
                value={hostId}
                onChange={(e) => setHostId(e.target.value)}
              >
                {runningHosts.map((h) => (
                  <option key={h.id} value={h.id}>
                    {h.name} · {h.memUsedMb}/{h.memMb} MB used · {h.ip}
                  </option>
                ))}
                {provisioningHosts.map((h) => (
                  <option key={h.id} value={h.id} disabled>
                    {h.name} · provisioning…
                  </option>
                ))}
              </Select>
            </FormField>

            {selectedHost && remainingMb !== undefined && (
              <>
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
                  />
                </FormField>
                <p className="muted" style={{ fontSize: "0.85rem" }}>
                  {remainingMb} MB free on {selectedHost.name}
                </p>
              </>
            )}

            {provisioningHosts.length > 0 && (
              <p className="muted" style={{ fontSize: "0.82rem" }}>
                {provisioningHosts.length} VM{provisioningHosts.length > 1 ? "s" : ""}{" "}
                still provisioning — this dialog refreshes automatically.
              </p>
            )}

            {canCreate ? (
            <div>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={() => setRentOpen((v) => !v)}
              >
                {rentOpen ? "Cancel" : "+ Rent a new VM"}
              </Button>
            </div>
            ) : (
              <p className="muted" style={{ fontSize: "0.82rem" }}>
                Renting another VM requires a paid plan.{" "}
                <a href="/admin">Upgrade in Admin</a>.
              </p>
            )}

            {rentOpen && (
              <form
                className="st-panel"
                style={{ padding: 16, display: "flex", flexDirection: "column", gap: "0.75rem" }}
                onSubmit={handleRent}
              >
                <FormField label="VM name" htmlFor="vm-name">
                  <Input
                    id="vm-name"
                    value={vmName}
                    onChange={(e) => setVmName(e.target.value)}
                    placeholder="prod-vm-1"
                    required
                    disabled={renting}
                  />
                </FormField>
                <FormField label="Region" htmlFor="vm-region">
                  <Select
                    id="vm-region"
                    value={vmRegion}
                    onChange={(e) => setVmRegion(e.target.value)}
                    disabled={renting}
                  >
                    {VM_REGIONS.map((r) => (
                      <option key={r.value} value={r.value}>
                        {r.label}
                      </option>
                    ))}
                  </Select>
                </FormField>
                <FormField label="Memory budget" htmlFor="vm-mem">
                  <Select
                    id="vm-mem"
                    value={vmMemMb}
                    onChange={(e) => setVmMemMb(Number(e.target.value))}
                    disabled={renting}
                  >
                    {VM_SIZES.map((s) => (
                      <option key={s.value} value={s.value}>
                        {s.label}
                      </option>
                    ))}
                  </Select>
                </FormField>
                {rentError && <Alert variant="error">{rentError}</Alert>}
                <div>
                  <Button type="submit" variant="primary" size="sm" disabled={renting}>
                    {renting ? "Renting…" : "Rent VM"}
                  </Button>
                </div>
              </form>
            )}

            {error && <p className="auth-error">{error}</p>}
          </>
        )}
      </div>
      <DialogFooter>
        <Button variant="ghost" size="sm" disabled={loading} onClick={onClose}>
          Cancel
        </Button>
        <Button
          variant="primary"
          size="sm"
          disabled={
            loading ||
            !hostId ||
            !selectedHost ||
            selectedHost.status !== "running" ||
            (remainingMb !== undefined && memLimitMb > remainingMb)
          }
          onClick={handleSelect}
        >
          Select VM
        </Button>
      </DialogFooter>
    </Dialog>
  );
}
