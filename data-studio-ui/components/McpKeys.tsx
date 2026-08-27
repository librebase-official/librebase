"use client";

import { useState } from "react";
import { Button, Badge } from "@/components/ui";
import { copyText } from "@/lib/clipboard";
import type { McpKey } from "@/lib/librebase-admin-client";

export function McpKeys({ orgId, initial }: { orgId: string; initial: McpKey[] }) {
  const [keys, setKeys] = useState<McpKey[]>(initial);
  const [newKey, setNewKey] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function listKeys(): Promise<McpKey[]> {
    const res = await fetch(`/api/admin/mcp-keys?orgId=${encodeURIComponent(orgId)}`);
    const data = (await res.json().catch(() => ({}))) as McpKey[] | { error?: string };
    if (!res.ok) {
      throw new Error((data as { error?: string }).error ?? `Failed (${res.status})`);
    }
    return data as McpKey[];
  }

  async function rotate() {
    setBusy(true);
    setError(null);
    setNewKey(null);
    setCopied(false);
    try {
      const res = await fetch("/api/admin/mcp-keys", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ orgId }),
      });
      const data = (await res.json().catch(() => ({}))) as { mcpKey?: string; error?: string };
      if (!res.ok || !data.mcpKey) {
        throw new Error(data.error ?? `Failed (${res.status})`);
      }
      setNewKey(data.mcpKey);
      setKeys(await listKeys());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not rotate key");
    } finally {
      setBusy(false);
    }
  }

  async function copy() {
    if (!newKey) return;
    const ok = await copyText(newKey);
    setCopied(ok);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <section className="card admin-section">
      <div className="flex-between">
        <h2 className="admin-section-title">MCP key</h2>
        <Button variant="secondary" size="sm" onClick={rotate} disabled={busy}>
          {busy ? "Generating…" : "Generate new key"}
        </Button>
      </div>
      <p className="muted text-sm mt-1">
        Console keys are for CI. Agents should call <code>auth_login</code> so
        you approve in the browser; the token is stored in the OS keychain and
        never belongs in a prompt.
      </p>

      {error ? <p className="auth-error text-sm">{error}</p> : null}

      {newKey ? (
        <div className="mt-3">
          <code className="mcp-key-display">{newKey}</code>
          <div className="mt-2">
            <Button variant="primary" size="sm" onClick={copy}>
              {copied ? "Copied" : "Copy key"}
            </Button>
          </div>
        </div>
      ) : null}

      {keys.length > 0 ? (
        <ul className="member-list mt-3">
          {keys.map((k) => (
            <li key={k.id}>
              <span className="muted text-sm">
                {k.createdAt} · {k.id.slice(-6)}
              </span>
              <Badge variant={k.revoked ? "error" : "running"}>
                {k.revoked ? "revoked" : "active"}
              </Badge>
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted text-sm mt-2">No keys yet.</p>
      )}
    </section>
  );
}
