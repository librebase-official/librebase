"use client";

import { useEffect, useState, useTransition } from "react";
import { Button, Dialog, DialogFooter, Input } from "@/components/ui";

interface Membership {
  orgId: string;
  role: string;
  name?: string;
}

interface OrgsState {
  activeOrgId: string;
  memberships: Membership[];
  role: string;
}

export function OrgsApi() {
  return {
    async load(): Promise<OrgsState> {
      const r = await fetch("/api/admin/orgs");
      if (!r.ok) throw new Error(`load orgs ${r.status}`);
      return r.json();
    },
    async switch(orgId: string) {
      const r = await fetch("/api/admin/orgs/switch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ orgId }),
      });
      if (!r.ok) {
        const { error } = await r.json().catch(() => ({}));
        throw new Error(error || `switch ${r.status}`);
      }
      return r.json();
    },
    async rename(orgId: string, name: string) {
      const r = await fetch("/api/admin/orgs", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ orgId, name }),
      });
      if (!r.ok) {
        const { error } = await r.json().catch(() => ({}));
        throw new Error(error || `rename ${r.status}`);
      }
      return r.json();
    },
    async create(name: string): Promise<OrgsState> {
      const r = await fetch("/api/admin/orgs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      if (!r.ok) {
        const { error } = await r.json().catch(() => ({}));
        throw new Error(error || `create ${r.status}`);
      }
      return r.json();
    },
  };
}

export default function OrgSwitcher({
  orgId,
  variant = "sidebar",
}: {
  orgId: string;
  variant?: "sidebar" | "crumb";
}) {
  const [state, setState] = useState<OrgsState | null>(null);
  const [open, setOpen] = useState(false);
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  // Rename dialog state
  const [renameOpen, setRenameOpen] = useState(false);
  const [renameName, setRenameName] = useState("");

  // Create dialog state
  const [createOpen, setCreateOpen] = useState(false);
  const [createName, setCreateName] = useState("");

  useEffect(() => {
    OrgsApi().load().then(setState).catch(() => setState(null));
  }, []);

  const current = state?.activeOrgId ?? orgId;
  const memberships = state?.memberships ?? [];
  const currentName =
    memberships.find((m) => m.orgId === current)?.name ?? current;
  const canRename = state?.role === "owner" && state?.memberships.length > 0;

  function go(orgId: string) {
    startTransition(async () => {
      setError(null);
      try {
        await OrgsApi().switch(orgId);
        window.location.href = "/projects";
      } catch (e) {
        setError(e instanceof Error ? e.message : "switch failed");
      }
    });
  }

  function startRename() {
    setRenameName(currentName);
    setRenameOpen(true);
  }

  function submitRename() {
    const trimmed = renameName.trim();
    if (!trimmed || trimmed === currentName) {
      setRenameOpen(false);
      return;
    }
    startTransition(async () => {
      setError(null);
      try {
        await OrgsApi().rename(current, trimmed);
        OrgsApi().load().then(setState).catch(() => setState(null));
        setRenameOpen(false);
      } catch (e) {
        setError(e instanceof Error ? e.message : "rename failed");
      }
    });
  }

  function submitCreate() {
    const trimmed = createName.trim();
    if (!trimmed) return;
    startTransition(async () => {
      setError(null);
      try {
        const result = await OrgsApi().create(trimmed);
        OrgsApi().load().then(setState).catch(() => setState(null));
        setCreateOpen(false);
        const newOrgId = result.memberships[0]?.orgId;
        if (newOrgId) go(newOrgId);
      } catch (e) {
        setError(e instanceof Error ? e.message : "create failed");
      }
    });
  }

  if (!state) {
    return variant === "crumb" ? (
      <span className="st-crumb">{orgId}</span>
    ) : (
      <span className="muted text-sm">Org: {orgId}</span>
    );
  }

  const toggleClass =
    variant === "crumb"
      ? "st-crumb"
      : "btn btn-ghost org-switcher-toggle";

  return (
    <>
      <button
        type="button"
        className={toggleClass}
        onClick={() => setOpen(!open)}
      >
        <span className="org-switcher-label" title={current}>
          {currentName}
        </span>
        <span aria-hidden>{open ? "▴" : "▾"}</span>
      </button>

      {open && (
        <div className="org-switcher">
          {memberships.map((m) => (
            <button
              key={m.orgId}
              type="button"
              className={`btn ${m.orgId === current ? "btn-primary" : "btn-ghost"} org-switcher-item`}
              onClick={() => {
                setOpen(false);
                go(m.orgId);
              }}
              disabled={pending}
            >
              <span className="org-switcher-label">
                {m.name ?? m.orgId} ({m.role})
              </span>
              {m.orgId === current && state.role === "owner" ? (
                <span className="org-switcher-active">· active</span>
              ) : null}
            </button>
          ))}
          {canRename && (
            <button
              type="button"
              className="btn btn-ghost org-switcher-item"
              onClick={() => {
                setOpen(false);
                startRename();
              }}
              disabled={pending}
            >
              Rename organization
            </button>
          )}
          <button
            type="button"
            className="btn btn-ghost org-switcher-item"
            onClick={() => {
              setOpen(false);
              setCreateName("");
              setCreateOpen(true);
            }}
            disabled={pending}
          >
            + Create organization
          </button>
          {error ? <span className="org-switcher-error">{error}</span> : null}
        </div>
      )}

      {/* Rename dialog */}
      <Dialog
        open={renameOpen}
        onClose={() => {
          if (!pending) setRenameOpen(false);
        }}
        title="Rename organization"
        description="Members see this name in the org switcher and admin panel."
      >
        <Input
          value={renameName}
          onChange={(e) => setRenameName(e.target.value)}
          placeholder="Acme Inc."
          autoFocus
          disabled={pending}
        />
        <DialogFooter>
          <Button
            variant="ghost"
            size="sm"
            disabled={pending}
            onClick={() => setRenameOpen(false)}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            disabled={
              pending ||
              !renameName.trim() ||
              renameName.trim() === currentName
            }
            onClick={submitRename}
          >
            {pending ? "Saving…" : "Save"}
          </Button>
        </DialogFooter>
      </Dialog>

      {/* Create dialog */}
      <Dialog
        open={createOpen}
        onClose={() => {
          if (!pending) setCreateOpen(false);
        }}
        title="New organization"
        description="Creates a new org you own. You’ll be switched to it automatically."
      >
        <Input
          value={createName}
          onChange={(e) => setCreateName(e.target.value)}
          placeholder="My new org"
          autoFocus
          disabled={pending}
        />
        <DialogFooter>
          <Button
            variant="ghost"
            size="sm"
            disabled={pending}
            onClick={() => setCreateOpen(false)}
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            size="sm"
            disabled={pending || !createName.trim()}
            onClick={submitCreate}
          >
            {pending ? "Creating…" : "Create"}
          </Button>
        </DialogFooter>
      </Dialog>
    </>
  );
}
