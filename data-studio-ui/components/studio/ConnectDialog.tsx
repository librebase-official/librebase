"use client";

import { useEffect, useState } from "react";
import { CopyField } from "@/components/CopyField";
import { IconConnect } from "./icons";

interface ConnectInfo {
  apiUrl: string;
  postgresUrl: string;
  anonKey: string | null;
  serviceRoleKey: string | null;
}

export function ConnectDialog({ projectId }: { projectId: string }) {
  const [open, setOpen] = useState(false);
  const [info, setInfo] = useState<ConnectInfo | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;
    fetch(`/api/projects/${projectId}/connect`)
      .then(async (r) => {
        const body = await r.json();
        if (!r.ok) throw new Error(body.error ?? "Failed to load");
        if (!cancelled) setInfo(body);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed");
      });
    return () => {
      cancelled = true;
    };
  }, [open, projectId]);

  return (
    <>
      <button
        type="button"
        className="btn btn-ghost btn-sm st-connect-btn"
        aria-label="Connect"
        onClick={() => setOpen(true)}
      >
        <IconConnect width="14" height="14" />
        <span className="st-connect-label">Connect</span>
      </button>
      {open ? (
        <div className="st-cmd" role="presentation" onClick={() => setOpen(false)}>
          <div
            className="st-cmd-panel"
            role="dialog"
            aria-label="Connect"
            onClick={(e) => e.stopPropagation()}
            style={{ padding: "16px 18px 18px" }}
          >
            <div className="flex-between mb-3">
              <strong>Connect</strong>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setOpen(false)}>
                Close
              </button>
            </div>
            {error ? <p className="auth-error">{error}</p> : null}
            {!info && !error ? <p className="muted">Loading…</p> : null}
            {info ? (
              <div className="stack">
                <CopyField label="API URL" value={info.apiUrl} />
                <CopyField label="Postgres" value={info.postgresUrl} />
                <CopyField
                  label="Anon key"
                  value={info.anonKey ?? "unset — set LIBREBASE_ANON_KEY"}
                />
                <CopyField
                  label="Service role"
                  value={info.serviceRoleKey ?? "unset — set LIBREBASE_SERVICE_ROLE_KEY"}
                />
              </div>
            ) : null}
          </div>
        </div>
      ) : null}
    </>
  );
}
