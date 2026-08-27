"use client";

import { useState } from "react";

interface Props { hostId: string; status: string; }

export function HostActions({ hostId, status }: Props) {
  const [loading, setLoading] = useState(false);
  const [current, setCurrent] = useState(status);
  const [confirmDelete, setConfirmDelete] = useState(false);

  async function action(method: string, endpoint: string) {
    setLoading(true);
    try {
      const res = await fetch(`/api/hosts/${hostId}/${endpoint}`, { method });
      const data = await res.json();
      if (data.status) setCurrent(data.status);
      if (endpoint === "delete") window.location.reload();
    } catch { /* ignore */ }
    setLoading(false);
  }

  return (
    <div style={{ display: "flex", gap: 6 }}>
      {current === "running" ? (
        <button className="btn btn-sm btn-warn" disabled={loading} onClick={() => action("POST", "stop")}>
          {loading ? "…" : "Stop"}
        </button>
      ) : (
        <button className="btn btn-sm btn-success" disabled={loading} onClick={() => action("POST", "start")}>
          {loading ? "…" : "Start"}
        </button>
      )}
      {confirmDelete ? (
        <button className="btn btn-sm btn-danger" disabled={loading}
          onClick={() => action("DELETE", "delete")}>
          Confirm delete
        </button>
      ) : (
        <button className="btn btn-sm btn-danger" onClick={() => setConfirmDelete(true)}>
          Delete
        </button>
      )}
    </div>
  );
}
