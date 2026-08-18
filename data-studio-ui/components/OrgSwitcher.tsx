"use client";

import { useEffect, useState, useTransition } from "react";

interface Membership {
  orgId: string;
  role: string;
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
  };
}

export default function OrgSwitcher({ orgId }: { orgId: string }) {
  const [state, setState] = useState<OrgsState | null>(null);
  const [open, setOpen] = useState(false);
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    OrgsApi().load().then(setState).catch(() => setState(null));
  }, []);

  const current = state?.activeOrgId ?? orgId;
  const memberships = state?.memberships ?? [];

  function go(orgId: string) {
    startTransition(async () => {
      setError(null);
      try {
        await OrgsApi().switch(orgId);
        window.location.href = "/admin";
      } catch (e) {
        setError(e instanceof Error ? e.message : "switch failed");
      }
    });
  }

  function create() {
    const name = window.prompt("New organization name");
    if (!name) return;
    startTransition(async () => {
      setError(null);
      try {
        const r = await fetch("/api/admin/orgs", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name }),
        });
        const data: { orgId?: string; error?: string } = (await r.json().catch(() => ({}))) as { orgId?: string };
        if (!r.ok || !data.orgId) {
          setError(data?.error || `create ${r.status}`);
          return;
        }
        OrgsApi().load().then(setState).catch(() => setState(null));
        go(data.orgId);
      } catch (e) {
        setError(e instanceof Error ? e.message : "create failed");
      }
    });
  }

  if (!state) return <div className="muted" style={{ fontSize: "0.8rem" }}>Org: {orgId}</div>;
  return (
    <div style={{ width: "100%" }}>
      <button
        type="button"
        className="btn btn-ghost"
        onClick={() => setOpen(!open)}
        style={{ width: "100%", justifyContent: "space-between" }}
      >
        <span style={{ overflow: "hidden", textOverflow: "ellipsis" }} title={current}>
          Org: {current}
        </span>
        <span>{open ? "▲" : "▼"}</span>
      </button>
      {open && (
        <div
          className="org-switcher"
          style={{
            marginTop: "0.4rem",
            border: "1px solid var(--border, #3333)",
            borderRadius: 6,
            padding: "0.4rem",
          }}
        >
          {memberships.map((m) => (
            <button
              key={m.orgId}
              type="button"
              className={`btn ${m.orgId === current ? "btn-primary" : "btn-ghost"}`}
              style={{ width: "100%", marginBottom: "0.25rem" }}
              onClick={() => {
                setOpen(false);
                go(m.orgId);
              }}
              disabled={pending}
            >
              {m.orgId} ({m.role}){" "}
              {m.orgId === current && state.role === "owner" ? "· active" : ""}
            </button>
          ))}
          <button
            type="button"
            className="btn btn-ghost"
            style={{ width: "100%", marginTop: "0.3rem", fontSize: "0.8rem" }}
            onClick={create}
          >
            + Create organization
          </button>
          {error ? <span className="auth-error" style={{ fontSize: "0.75rem" }}>{error}</span> : null}
        </div>
      )}
    </div>
  );
}
