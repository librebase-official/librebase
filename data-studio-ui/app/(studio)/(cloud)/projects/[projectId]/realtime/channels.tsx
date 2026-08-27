"use client";

import { useEffect, useState } from "react";
import { EmptyState } from "@/components/studio/EmptyState";
import { IconRealtime } from "@/components/studio/icons";

export function RealtimeChannels({ projectId }: { projectId: string }) {
  const [channels, setChannels] = useState<unknown[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/projects/${projectId}/realtime`)
      .then((r) => r.json())
      .then((body: { ok?: boolean; channels?: unknown[]; message?: string }) => {
        setChannels(body.channels ?? []);
        setMessage(body.ok ? null : (body.message ?? null));
      })
      .finally(() => setLoading(false));
  }, [projectId]);

  if (loading) {
    return (
      <div className="st-panel" style={{ padding: 16 }}>
        <div className="st-skel" />
      </div>
    );
  }
  if (channels.length === 0) {
    return (
      <EmptyState
        icon={<IconRealtime />}
        title="No open channels"
        body={message ?? "When clients subscribe, they will list here."}
      />
    );
  }
  return (
    <div className="st-panel" style={{ overflow: "auto" }}>
      <table className="table">
        <thead>
          <tr>
            <th>Channel</th>
          </tr>
        </thead>
        <tbody>
          {channels.map((c, i) => (
            <tr key={i}>
              <td className="mono">{typeof c === "string" ? c : JSON.stringify(c)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
