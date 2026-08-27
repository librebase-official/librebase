"use client";

import { useState } from "react";

export function SqlEditor({ projectId }: { projectId: string }) {
  const [sql, setSql] = useState("select 1 as ok;");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [rows, setRows] = useState<Record<string, unknown>[] | null>(null);
  const [raw, setRaw] = useState<string | null>(null);

  async function run(e: React.FormEvent) {
    e.preventDefault();
    setPending(true);
    setError(null);
    setRows(null);
    setRaw(null);
    try {
      const res = await fetch(`/api/projects/${projectId}/sql`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sql }),
      });
      const body = (await res.json()) as { ok?: boolean; body?: unknown; error?: string };
      if (!res.ok || body.ok === false) {
        setError(body.error ?? "Query failed");
        if (body.body) setRaw(JSON.stringify(body.body, null, 2));
        return;
      }
      const payload = body.body;
      if (Array.isArray(payload)) {
        setRows(payload as Record<string, unknown>[]);
      } else if (payload && typeof payload === "object") {
        const rec = payload as Record<string, unknown>;
        const list = rec.rows ?? rec.data ?? rec.result;
        if (Array.isArray(list)) setRows(list as Record<string, unknown>[]);
        else setRaw(JSON.stringify(payload, null, 2));
      } else {
        setRaw(String(payload ?? ""));
      }
    } catch {
      setError("Request failed");
    } finally {
      setPending(false);
    }
  }

  const columns = rows && rows[0] ? Object.keys(rows[0]) : [];

  return (
    <form onSubmit={run}>
      <textarea
        className="input mono"
        style={{ minHeight: 180, fontSize: 13, lineHeight: 1.45 }}
        value={sql}
        onChange={(e) => setSql(e.target.value)}
        spellCheck={false}
      />
      <div className="action-row mt-3">
        <button type="submit" className="btn btn-sm btn-primary" disabled={pending || !sql.trim()}>
          {pending ? "Running…" : "Run"}
        </button>
      </div>
      {error ? <p className="auth-error mt-3">{error}</p> : null}
      {rows ? (
        <div className="st-panel mt-4" style={{ overflow: "auto" }}>
          {rows.length === 0 ? (
            <p className="muted" style={{ padding: 16 }}>
              0 rows
            </p>
          ) : (
            <table className="table">
              <thead>
                <tr>
                  {columns.map((c) => (
                    <th key={c}>{c}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, i) => (
                  <tr key={i}>
                    {columns.map((c) => (
                      <td key={c} className="mono">
                        {formatCell(row[c])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      ) : null}
      {raw ? (
        <pre className="st-panel mt-4" style={{ padding: 16, overflow: "auto", fontSize: 12 }}>
          {raw}
        </pre>
      ) : null}
    </form>
  );
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
