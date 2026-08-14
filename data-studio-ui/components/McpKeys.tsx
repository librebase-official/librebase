"use client";

import { useState } from "react";
import { adminListMcpKeys, adminRotateMcpKey, type McpKey } from "@/lib/librebase-admin-client";

export function McpKeys({ orgId, initial }: { orgId: string; initial: McpKey[] }) {
  const [keys, setKeys] = useState<McpKey[]>(initial);
  const [newKey, setNewKey] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function rotate() {
    setBusy(true);
    setError(null);
    setNewKey(null);
    setCopied(false);
    try {
      const result = await adminRotateMcpKey(orgId);
      setNewKey(result.mcpKey);
      setKeys(await adminListMcpKeys(orgId));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not rotate key");
    } finally {
      setBusy(false);
    }
  }

  async function copy() {
    if (!newKey) return;
    try {
      await navigator.clipboard.writeText(newKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* clipboard unavailable */
    }
  }

  return (
    <section className="card" style={{ marginTop: "1.5rem" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <h2 style={{ margin: 0 }}>MCP key</h2>
        <button className="btn" onClick={rotate} disabled={busy}>
          {busy ? "Generating…" : "Generate new key"}
        </button>
      </div>
      <p className="muted" style={{ margin: "0.4rem 0 0.75rem", fontSize: "0.88rem" }}>
        Used by AI tools to access this org. Shown once when generated.
      </p>

      {error ? <p style={{ color: "var(--danger)" }}>{error}</p> : null}

      {newKey ? (
        <div style={{ display: "grid", gap: "0.5rem" }}>
          <code
            style={{
              wordBreak: "break-all",
              padding: "0.6rem 0.75rem",
              background: "var(--bg)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius)",
              color: "var(--accent)",
            }}
          >
            {newKey}
          </code>
          <div>
            <button className="btn btn-primary" onClick={copy}>
              {copied ? "Copied" : "Copy key"}
            </button>
          </div>
        </div>
      ) : null}

      {keys.length > 0 ? (
        <ul style={{ listStyle: "none", padding: 0, margin: "1rem 0 0" }}>
          {keys.map((k) => (
            <li
              key={k.id}
              style={{
                display: "flex",
                justifyContent: "space-between",
                padding: "0.4rem 0",
                borderBottom: "1px solid var(--border)",
                fontSize: "0.85rem",
              }}
            >
              <span className="muted">
                {k.createdAt} · {k.id.slice(-6)}
              </span>
              <span className={k.revoked ? "badge" : "badge running"}>
                {k.revoked ? "revoked" : "active"}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted" style={{ margin: "0.5rem 0 0" }}>
          No keys yet.
        </p>
      )}
    </section>
  );
}
