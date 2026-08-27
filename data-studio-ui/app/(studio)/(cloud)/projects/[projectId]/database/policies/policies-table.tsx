"use client";

import { useEffect, useState } from "react";
import { EmptyState } from "@/components/studio/EmptyState";
import { IconShield } from "@/components/studio/icons";

interface PolicyRow {
  schema?: string;
  table?: string;
  name?: string;
  cmd?: string;
}

export function PoliciesTable({ projectId }: { projectId: string }) {
  const [rows, setRows] = useState<PolicyRow[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/projects/${projectId}/policies`)
      .then((r) => r.json())
      .then((body: { ok?: boolean; policies?: PolicyRow[]; message?: string }) => {
        setRows(body.policies ?? []);
        setMessage(body.ok ? null : (body.message ?? null));
      })
      .finally(() => setLoading(false));
  }, [projectId]);

  if (loading) {
    return (
      <div className="st-panel" style={{ padding: 16 }}>
        <div className="st-skel" />
        <div className="st-skel" style={{ width: "70%" }} />
      </div>
    );
  }
  if (rows.length === 0) {
    return (
      <EmptyState
        icon={<IconShield />}
        title="No policies to show"
        body={message ?? "When tables enable RLS, policies will list here."}
      />
    );
  }
  return (
    <div className="st-panel" style={{ overflow: "auto" }}>
      <table className="table">
        <thead>
          <tr>
            <th>Schema</th>
            <th>Table</th>
            <th>Policy</th>
            <th>Command</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((p, i) => (
            <tr key={`${p.name}-${i}`}>
              <td className="mono">{String(p.schema ?? "")}</td>
              <td>{String(p.table ?? "")}</td>
              <td>{String(p.name ?? "")}</td>
              <td className="muted">{String(p.cmd ?? "")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
