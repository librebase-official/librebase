"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { EmptyState } from "@/components/studio/EmptyState";
import { IconCheck, IconCopy, IconPlus, IconTable } from "@/components/studio/icons";
import { copyText } from "@/lib/clipboard";
import {
  cellToString,
  columnsFromRows,
  downloadText,
  rowToAgentPrompt,
  rowsToCsv,
  tableToAgentPrompt,
  type AgentTableContext,
} from "@/lib/table-export";

interface TableMeta {
  schema: string;
  name: string;
  kind: string;
}

interface RowSet {
  columns: string[];
  rows: Record<string, unknown>[];
}

function inEditable(target: EventTarget | null): boolean {
  if (!(target instanceof HTMLElement)) return false;
  const tag = target.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
  return target.isContentEditable;
}

export function TablesBrowser({
  projectId,
  projectName,
}: {
  projectId: string;
  projectName: string;
}) {
  const [schema, setSchema] = useState("public");
  const [q, setQ] = useState("");
  const [tables, setTables] = useState<TableMeta[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [data, setData] = useState<RowSet>({ columns: [], rows: [] });
  const [rowsLoading, setRowsLoading] = useState(false);
  const [rowsError, setRowsError] = useState<string | null>(null);
  const [rowIndex, setRowIndex] = useState<number | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  const visible = useMemo(() => {
    const n = q.trim().toLowerCase();
    return n ? tables.filter((t) => t.name.toLowerCase().includes(n)) : tables;
  }, [tables, q]);

  const selectedRow = rowIndex != null ? data.rows[rowIndex] ?? null : null;

  const agentCtx: AgentTableContext | null = selected
    ? {
        projectId,
        projectName,
        schema,
        table: selected,
        columns: data.columns,
        restPath: `/rest/v1/${selected}`,
        cappedAt: 200,
      }
    : null;

  async function flash(key: string) {
    setCopied(key);
    window.setTimeout(() => setCopied((cur) => (cur === key ? null : cur)), 1600);
  }

  const copyAgent = useCallback(
    async (kind: "table" | "row", index = rowIndex) => {
      if (!agentCtx) return false;
      const text =
        kind === "row" && index != null && data.rows[index]
          ? rowToAgentPrompt(agentCtx, data.rows[index], index, data.rows.length)
          : tableToAgentPrompt(agentCtx, data.rows);
      const ok = await copyText(text);
      if (ok) await flash(kind);
      return ok;
    },
    [agentCtx, data.rows, rowIndex],
  );

  async function loadTables(nextSchema = schema) {
    setLoading(true);
    try {
      const res = await fetch(
        `/api/projects/${projectId}/tables?schema=${encodeURIComponent(nextSchema)}`,
      );
      const body = (await res.json()) as {
        ok?: boolean;
        tables?: TableMeta[];
        message?: string;
      };
      const next = body.tables ?? [];
      setTables(next);
      setMessage(body.ok ? null : (body.message ?? "Could not list tables"));
      setSelected((cur) => {
        if (cur && next.some((t) => t.name === cur)) return cur;
        return next[0]?.name ?? null;
      });
    } finally {
      setLoading(false);
    }
  }

  const loadRows = useCallback(
    async (table: string) => {
      setRowsLoading(true);
      setRowsError(null);
      setRowIndex(null);
      try {
        const res = await fetch(
          `/api/projects/${projectId}/tables/${encodeURIComponent(table)}?limit=200`,
        );
        const body = (await res.json()) as {
          ok?: boolean;
          columns?: string[];
          rows?: Record<string, unknown>[];
          message?: string;
        };
        const rows = body.rows ?? [];
        const columns = body.columns?.length ? body.columns : columnsFromRows(rows);
        setData({ columns, rows });
        if (!body.ok) setRowsError(body.message ?? "Could not read rows");
      } finally {
        setRowsLoading(false);
      }
    },
    [projectId],
  );

  useEffect(() => {
    void loadTables();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  useEffect(() => {
    if (selected) void loadRows(selected);
    else setData({ columns: [], rows: [] });
  }, [selected, loadRows]);

  useEffect(() => {
    function onCopy(e: ClipboardEvent) {
      if (inEditable(e.target)) return;
      if (!agentCtx) return;
      e.preventDefault();
      const text =
        rowIndex != null && data.rows[rowIndex]
          ? rowToAgentPrompt(agentCtx, data.rows[rowIndex], rowIndex, data.rows.length)
          : tableToAgentPrompt(agentCtx, data.rows);
      e.clipboardData?.setData("text/plain", text);
      void flash(rowIndex != null ? "row" : "table");
    }

    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setRowIndex(null);
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key.toLowerCase() === "c") {
        if (inEditable(e.target) || !selected) return;
        e.preventDefault();
        downloadText(`${selected}.csv`, rowsToCsv(data.rows, data.columns), "text/csv");
        void flash("csv");
      }
    }

    function onContext(e: MouseEvent) {
      if (inEditable(e.target)) return;
      const el = e.target instanceof HTMLElement ? e.target : null;
      if (!el?.closest(".tbl-explorer")) return;
      if (!agentCtx) return;
      e.preventDefault();
      const tr = el.closest("tbody tr");
      if (tr?.parentElement) {
        const i = [...tr.parentElement.children].indexOf(tr);
        if (i >= 0) {
          setRowIndex(i);
          void copyAgent("row", i);
          return;
        }
      }
      void copyAgent("table");
    }

    document.addEventListener("copy", onCopy);
    window.addEventListener("keydown", onKey);
    window.addEventListener("contextmenu", onContext);
    return () => {
      document.removeEventListener("copy", onCopy);
      window.removeEventListener("keydown", onKey);
      window.removeEventListener("contextmenu", onContext);
    };
  }, [agentCtx, copyAgent, data.columns, data.rows, rowIndex, selected]);

  async function createTable(e: React.FormEvent) {
    e.preventDefault();
    if (!newName.trim()) return;
    setCreating(true);
    try {
      await fetch(`/api/projects/${projectId}/tables`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newName.trim(), schema, rls: true }),
      });
      const name = newName.trim();
      setNewName("");
      await loadTables();
      setSelected(name);
    } finally {
      setCreating(false);
    }
  }

  function exportCsv() {
    if (!selected) return;
    downloadText(`${selected}.csv`, rowsToCsv(data.rows, data.columns), "text/csv");
    void flash("csv");
  }

  const copiedLabel =
    copied === "row"
      ? "Copied row for agent"
      : copied === "table"
        ? "Copied table for agent"
        : copied === "csv"
          ? "CSV downloaded"
          : copied === "cell"
            ? "Copied"
            : null;

  return (
    <div className="tbl-explorer">
      <aside className="tbl-nav" aria-label="Tables">
        <div className="tbl-nav-tools">
          <select
            className="select"
            value={schema}
            onChange={(e) => {
              setSchema(e.target.value);
              void loadTables(e.target.value);
            }}
          >
            <option value="public">public</option>
            <option value="auth">auth</option>
          </select>
          <input
            className="input"
            placeholder="Filter"
            value={q}
            onChange={(e) => setQ(e.target.value)}
          />
        </div>
        <form className="tbl-new" onSubmit={createTable}>
          <input
            className="input"
            placeholder="new_table"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
          />
          <button type="submit" className="btn btn-sm btn-primary" disabled={creating || !newName.trim()}>
            <IconPlus width="14" height="14" />
          </button>
        </form>
        <nav className="tbl-nav-list">
          {loading ? (
            <p className="muted tbl-nav-empty">Loading…</p>
          ) : visible.length === 0 ? (
            <p className="muted tbl-nav-empty">{message ?? "No tables"}</p>
          ) : (
            visible.map((t) => (
              <button
                key={`${t.schema}.${t.name}`}
                type="button"
                className={`tbl-nav-item${selected === t.name ? " active" : ""}`}
                onClick={() => setSelected(t.name)}
                onContextMenu={(e) => {
                  if (selected !== t.name) return;
                  e.preventDefault();
                  void copyAgent("table");
                }}
              >
                <IconTable width="14" height="14" />
                <span>{t.name}</span>
              </button>
            ))
          )}
        </nav>
      </aside>

      <section className="tbl-stage" aria-label="Table data">
        {!selected ? (
          <EmptyState
            icon={<IconTable />}
            title="Select a table"
            body="Pick a table on the left. ⌘C or right-click copies it for an agent."
          />
        ) : (
          <>
            <div className="tbl-toolbar">
              <div>
                <h2>{selected}</h2>
                <p className="muted">
                  {copiedLabel ??
                    (rowsLoading
                      ? "Loading…"
                      : `${data.rows.length} row${data.rows.length === 1 ? "" : "s"} · ⌘C / right-click copies for an agent`)}
                  {!copiedLabel && data.rows.length === 200 ? " · first 200" : ""}
                </p>
              </div>
              <div className="tbl-toolbar-actions">
                <button
                  type="button"
                  className="btn btn-sm"
                  disabled={!agentCtx}
                  onClick={() => copyAgent(rowIndex != null ? "row" : "table")}
                >
                  {copied === "table" || copied === "row" ? (
                    <IconCheck width="14" height="14" />
                  ) : (
                    <IconCopy width="14" height="14" />
                  )}
                  Copy for agent
                </button>
                <button
                  type="button"
                  className="btn btn-sm"
                  disabled={!data.rows.length}
                  onClick={exportCsv}
                >
                  Export CSV
                </button>
              </div>
            </div>

            {rowsError ? <p className="agent-callout">{rowsError}</p> : null}

            {rowsLoading ? (
              <div className="tbl-grid-wrap">
                <div className="st-skel" />
                <div className="st-skel" style={{ width: "80%" }} />
              </div>
            ) : data.rows.length === 0 ? (
              <EmptyState
                icon={<IconTable />}
                title={`No rows in ${selected}`}
                body="Insert data via the API or SQL editor, then refresh."
              />
            ) : (
              <div className="tbl-grid-wrap">
                <table className="table tbl-grid">
                  <thead>
                    <tr>
                      {data.columns.map((col) => (
                        <th key={col}>{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.rows.map((row, i) => (
                      <tr
                        key={String(row.id ?? i)}
                        className={rowIndex === i ? "active" : undefined}
                        onClick={() => setRowIndex((cur) => (cur === i ? null : i))}
                      >
                        {data.columns.map((col) => {
                          const text = cellToString(row[col]);
                          return (
                            <td key={col} title={text}>
                              {text || <span className="muted">null</span>}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </section>

      {selectedRow && agentCtx ? (
        <aside className="tbl-drawer" aria-label="Row">
          <div className="tbl-drawer-head">
            <strong>Row</strong>
            <div className="tbl-toolbar-actions">
              <button
                type="button"
                className="btn btn-sm"
                onClick={() => copyAgent("row")}
              >
                {copied === "row" ? <IconCheck width="14" height="14" /> : <IconCopy width="14" height="14" />}
                Copy for agent
              </button>
              <button type="button" className="btn btn-ghost btn-sm" onClick={() => setRowIndex(null)}>
                Close
              </button>
            </div>
          </div>
          <dl className="tbl-fields">
            {data.columns.map((col) => {
              const text = cellToString(selectedRow[col]);
              return (
                <div key={col} className="tbl-field">
                  <dt>
                    <span>{col}</span>
                    <button
                      type="button"
                      className="btn btn-ghost btn-sm"
                      onClick={async () => {
                        const ok = await copyText(text);
                        if (ok) void flash("cell");
                      }}
                    >
                      {copied === "cell" ? "Copied" : "Copy"}
                    </button>
                  </dt>
                  <dd>
                    <code>{text || "null"}</code>
                  </dd>
                </div>
              );
            })}
          </dl>
        </aside>
      ) : null}
    </div>
  );
}
