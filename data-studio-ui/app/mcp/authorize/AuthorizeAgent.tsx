"use client";

import Link from "next/link";
import { useEffect, useMemo, useState, useTransition } from "react";
import { Button } from "@/components/ui";
import type { McpDeviceView } from "@/lib/librebase-admin-client";
import type { Project } from "@/lib/types";

function formatCode(raw: string): string {
  const compact = raw.replace(/[^A-Za-z0-9]/g, "").toUpperCase();
  if (compact.length === 8) return `${compact.slice(0, 4)}-${compact.slice(4)}`;
  return raw.toUpperCase();
}

export function AuthorizeAgent({ userCode }: { userCode: string }) {
  const formatted = useMemo(() => formatCode(userCode), [userCode]);
  const loginHref = `/login?next=${encodeURIComponent(`/mcp/authorize?user_code=${formatted}`)}`;
  const [device, setDevice] = useState<McpDeviceView | null>(null);
  const [orgId, setOrgId] = useState("");
  const [scope, setScope] = useState<"user" | "project">("user");
  const [projectId, setProjectId] = useState("");
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [projectsError, setProjectsError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [unauthenticated, setUnauthenticated] = useState(false);
  const [done, setDone] = useState<"approved" | "denied" | null>(null);
  const [pending, startTransition] = useTransition();

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const res = await fetch(
        `/api/mcp/device?user_code=${encodeURIComponent(formatted)}`,
      );
      if (cancelled) return;
      if (res.status === 401) {
        setUnauthenticated(true);
        return;
      }
      const body = (await res.json().catch(() => ({}))) as McpDeviceView & {
        error?: string;
      };
      if (!res.ok) {
        setError(body.error ?? `Could not load request (${res.status})`);
        return;
      }
      setDevice(body);
      setOrgId(body.activeOrgId || body.memberships?.[0]?.orgId || "");
    })();
    return () => {
      cancelled = true;
    };
  }, [formatted]);

  // When the user opts down to a single project, load that org's projects so
  // they can pick one. Re-runs when the chosen org changes.
  useEffect(() => {
    if (scope !== "project" || !orgId) {
      setProjects(null);
      setProjectId("");
      setProjectsError(null);
      return;
    }
    let cancelled = false;
    setProjects(null);
    setProjectId("");
    setProjectsError(null);
    (async () => {
      const res = await fetch(
        `/api/mcp/device/projects?orgId=${encodeURIComponent(orgId)}`,
      );
      if (cancelled) return;
      const body = (await res.json().catch(() => ({}))) as {
        projects?: Project[];
        error?: string;
      };
      if (!res.ok) {
        setProjectsError(body.error ?? `Could not load projects (${res.status})`);
        return;
      }
      setProjects(body.projects ?? []);
    })();
    return () => {
      cancelled = true;
    };
  }, [scope, orgId]);

  function act(path: "approve" | "deny") {
    startTransition(async () => {
      setError(null);
      const reqBody: Record<string, unknown> = { userCode: formatted, orgId };
      if (path === "approve") {
        reqBody.scope = scope;
        if (scope === "project" && projectId) reqBody.projectId = projectId;
      }
      const res = await fetch(`/api/mcp/device/${path}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(reqBody),
      });
      const body = (await res.json().catch(() => ({}))) as { error?: string };
      if (!res.ok) {
        setError(body.error ?? `${path} failed (${res.status})`);
        return;
      }
      setDone(path === "approve" ? "approved" : "denied");
    });
  }

  if (unauthenticated) {
    return (
      <div className="auth-card">
        <h1>Authorize agent</h1>
        <p className="muted">Sign in to approve this agent’s access to your org.</p>
        <p className="mcp-user-code" aria-label="Device code">
          {formatted || "————————"}
        </p>
        <Link className="btn btn-primary" href={loginHref}>
          Sign in to continue
        </Link>
      </div>
    );
  }

  if (done === "approved") {
    return (
      <div className="auth-card">
        <h1>Agent approved</h1>
        <p className="muted">
          You can close this tab. The agent stored the credential in the OS
          keychain — it was never shown in the chat.
        </p>
      </div>
    );
  }

  if (done === "denied") {
    return (
      <div className="auth-card">
        <h1>Request denied</h1>
        <p className="muted">The agent will not receive access.</p>
      </div>
    );
  }

  if (error && !device) {
    return (
      <div className="auth-card">
        <h1>Authorize agent</h1>
        <p className="auth-error">{error}</p>
        <p className="muted auth-foot">
          <Link href={loginHref}>Sign in</Link> if this code belongs to you.
        </p>
      </div>
    );
  }

  if (!device) {
    return (
      <div className="auth-card">
        <h1>Authorize agent</h1>
        <p className="muted">Checking the request…</p>
      </div>
    );
  }

  if (device.status !== "pending") {
    return (
      <div className="auth-card">
        <h1>Authorize agent</h1>
        <p className="muted">This request is {device.status}.</p>
        <p className="mcp-user-code">{device.userCode}</p>
      </div>
    );
  }

  return (
    <div className="auth-card">
      <h1>Authorize agent</h1>
      <p className="muted">
        <strong>{device.clientName}</strong> wants to manage this Librebase org
        on your behalf. Confirm the code matches what the agent showed you.
      </p>
      <p className="mcp-user-code" aria-label="Device code">
        {device.userCode}
      </p>
      {device.memberships?.length > 1 ? (
        <div className="field">
          <label htmlFor="mcp-org">Organization</label>
          <select
            id="mcp-org"
            value={orgId}
            onChange={(e) => setOrgId(e.target.value)}
          >
            {device.memberships.map((m) => (
              <option key={m.orgId} value={m.orgId}>
                {m.name || m.orgId} ({m.role})
              </option>
            ))}
          </select>
        </div>
      ) : null}
      <div className="mcp-scope" style={{ margin: "12px 0" }}>
        <label
          className="mcp-scope-option"
          style={{ display: "block", cursor: "pointer", marginBottom: 10 }}
        >
          <input
            type="radio"
            name="mcp-scope"
            checked={scope === "user"}
            onChange={() => setScope("user")}
            style={{ marginRight: 8 }}
          />
          <strong>User-level access</strong>
          <span className="muted text-sm" style={{ display: "block", marginTop: 2 }}>
            The agent can work across every org you belong to and all of your
            projects, at your role in each. It can never exceed your
            permissions, every action is audited, and you can revoke it
            instantly.
          </span>
        </label>
        <label
          className="mcp-scope-option"
          style={{ display: "block", cursor: "pointer" }}
        >
          <input
            type="radio"
            name="mcp-scope"
            checked={scope === "project"}
            onChange={() => setScope("project")}
            style={{ marginRight: 8 }}
          />
          <strong>Single project</strong>
          <span className="muted text-sm" style={{ display: "block", marginTop: 2 }}>
            Lock the agent to one project in the selected org.
          </span>
        </label>
        {scope === "project" ? (
          <div className="field" style={{ marginTop: 10 }}>
            <label htmlFor="mcp-project">Project</label>
            <select
              id="mcp-project"
              value={projectId}
              onChange={(e) => setProjectId(e.target.value)}
              disabled={projects === null}
            >
              <option value="">
                {projects === null
                  ? "Loading projects…"
                  : projects.length === 0
                    ? "No projects in this org"
                    : "Select a project"}
              </option>
              {projects?.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
            {projectsError ? (
              <p className="auth-error">{projectsError}</p>
            ) : null}
          </div>
        ) : null}
      </div>
      {error ? <p className="auth-error">{error}</p> : null}
      <div className="mcp-authorize-actions">
        <Button
          variant="primary"
          onClick={() => act("approve")}
          disabled={pending || !orgId || (scope === "project" && !projectId)}
        >
          {pending ? "Authorizing…" : "Approve"}
        </Button>
        <Button variant="secondary" onClick={() => act("deny")} disabled={pending}>
          Deny
        </Button>
      </div>
    </div>
  );
}
