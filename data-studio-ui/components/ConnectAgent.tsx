"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { agentSnippets, type AgentSnippetId } from "@/lib/agent-snippets";
import type { McpKey } from "@/lib/librebase-admin-client";

type Tab = AgentSnippetId;

export function ConnectAgent({
  orgId,
  projectName,
  siteUrl,
}: {
  orgId: string;
  projectName: string;
  siteUrl: string;
}) {
  const [keys, setKeys] = useState<McpKey[]>([]);
  const [plaintext, setPlaintext] = useState<string | null>(null);
  const [label, setLabel] = useState("Cursor");
  const [tab, setTab] = useState<Tab>("cursor");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);
  const booted = useRef(false);

  const listKeys = useCallback(async () => {
    const res = await fetch(`/api/admin/mcp-keys?orgId=${encodeURIComponent(orgId)}`);
    const data = (await res.json().catch(() => ({}))) as McpKey[] | { error?: string };
    if (!res.ok) {
      throw new Error((data as { error?: string }).error ?? `Failed (${res.status})`);
    }
    return data as McpKey[];
  }, [orgId]);

  const issue = useCallback(
    async (opts: { rotate: boolean; label?: string }) => {
      setBusy(true);
      setError(null);
      try {
        const res = await fetch("/api/admin/mcp-keys", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            orgId,
            rotate: opts.rotate,
            label: opts.label ?? label,
          }),
        });
        const data = (await res.json().catch(() => ({}))) as {
          mcpKey?: string;
          error?: string;
        };
        if (!res.ok || !data.mcpKey) {
          throw new Error(data.error ?? `Failed (${res.status})`);
        }
        setPlaintext(data.mcpKey);
        setKeys(await listKeys());
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not issue key");
      } finally {
        setBusy(false);
      }
    },
    [orgId, label, listKeys],
  );

  useEffect(() => {
    if (booted.current) return;
    booted.current = true;
    let cancelled = false;
    (async () => {
      try {
        const listed = await listKeys();
        if (cancelled) return;
        setKeys(listed);
        const active = listed.filter((k) => !k.revoked);
        if (active.length === 0) {
          await issue({ rotate: false, label: "first-agent" });
        }
      } catch (e) {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Could not load keys");
        }
      } finally {
        if (!cancelled) setLoaded(true);
      }
    })();
    return () => {
      cancelled = true;
    };
    // First visit only — mint a key if the org has none.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [orgId]);

  async function copy(text: string, id: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(id);
      setTimeout(() => setCopied(null), 1600);
    } catch {
      /* clipboard unavailable */
    }
  }

  const snippets = agentSnippets({
    siteUrl,
    mcpKey: plaintext ?? "lb_mcp_YOUR_KEY",
  });
  const current = snippets.find((s) => s.id === tab) ?? snippets[0];
  const active = keys.filter((k) => !k.revoked);

  return (
    <section className="card connect-agent">
      <div className="connect-agent-head">
        <div>
          <h2>Connect an agent</h2>
          <p className="muted" style={{ margin: "0.25rem 0 0", fontSize: "0.85rem" }}>
            Paste a snippet into Cursor, Claude, or Grok. First prompt: “what’s in{" "}
            {projectName}?”
          </p>
        </div>
      </div>

      {error ? <p className="auth-error">{error}</p> : null}

      {plaintext ? (
        <div className="connect-row" style={{ marginTop: "0.75rem" }}>
          <div className="connect-label">MCP key (shown once)</div>
          <div className="connect-value">
            <code className="mcp-key-display">{plaintext}</code>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => copy(plaintext, "key")}
            >
              {copied === "key" ? "Copied" : "Copy key"}
            </button>
          </div>
        </div>
      ) : loaded && active.length > 0 ? (
        <p className="muted" style={{ fontSize: "0.85rem", marginTop: "0.75rem" }}>
          A key is already active. Rotate to mint a new one (the old key dies).
        </p>
      ) : null}

      <div className="agent-tabs" role="tablist">
        {snippets.map((s) => (
          <button
            key={s.id}
            type="button"
            role="tab"
            aria-selected={tab === s.id}
            className={`agent-tab${tab === s.id ? " active" : ""}`}
            onClick={() => setTab(s.id)}
          >
            {s.label}
          </button>
        ))}
      </div>

      <p className="muted" style={{ fontSize: "0.8rem", margin: "0.5rem 0" }}>
        {current.hint}
        {!plaintext ? " — generate a key to fill the snippet." : ""}
      </p>

      <pre className="agent-snippet">
        <code>{current.text}</code>
      </pre>
      <button
        type="button"
        className="btn btn-primary"
        onClick={() => copy(current.text, current.id)}
        disabled={!plaintext}
        style={{ marginTop: "0.6rem" }}
      >
        {copied === current.id ? "Copied" : `Copy ${current.label} snippet`}
      </button>

      <div className="connect-agent-foot">
        <label className="field" style={{ margin: 0, flex: 1 }}>
          <span className="muted" style={{ fontSize: "0.75rem" }}>
            Label
          </span>
          <input
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            placeholder="Cursor"
            disabled={busy}
          />
        </label>
        <button
          type="button"
          className="btn"
          onClick={() => issue({ rotate: false, label })}
          disabled={busy || !label.trim()}
        >
          {busy ? "Working…" : "Add another key"}
        </button>
        <button
          type="button"
          className="btn"
          onClick={() => issue({ rotate: true, label })}
          disabled={busy}
        >
          Rotate key
        </button>
      </div>

      {keys.length > 0 ? (
        <ul className="key-list">
          {keys.map((k) => (
            <li key={k.id}>
              <span>
                {k.label || "unlabeled"} · {k.id.slice(-6)}
              </span>
              <span className={`badge ${k.revoked ? "stopped" : "running"}`}>
                {k.revoked ? "revoked" : "active"}
              </span>
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
