"use client";

import { useCallback, useState, useTransition } from "react";
import { Button, Badge, Input, Select } from "@/components/ui";
import { copyText } from "@/lib/clipboard";
import type { KmsKey, KmsKeyInput } from "@/lib/librebase-admin-client";

function decodeB64url(data: string): string {
  const pad = data + "=".repeat((4 - (data.length % 4)) % 4);
  const bytes = Uint8Array.from(atob(pad.replace(/-/g, "+").replace(/_/g, "/")), (c) =>
    c.charCodeAt(0),
  );
  return new TextDecoder().decode(bytes);
}

function scopeBadge(key: KmsKey) {
  if (key.scope === "cross_org")
    return <Badge variant="info">personal</Badge>;
  if (key.scope === "project")
    return <Badge variant="warning">project</Badge>;
  return <Badge variant="default">org</Badge>;
}

export function KeysManager({
  projectId,
  initialKeys,
  initialMyKeys,
}: {
  projectId: string;
  initialKeys: KmsKey[];
  initialMyKeys: KmsKey[];
}) {
  const [keys, setKeys] = useState<KmsKey[]>(initialKeys);
  const [myKeys, setMyKeys] = useState<KmsKey[]>(initialMyKeys);

  const refresh = useCallback(async () => {
    const [orgRes, myRes] = await Promise.all([
      fetch(`/api/projects/${projectId}/keys`),
      fetch(`/api/me/keys`),
    ]);
    if (orgRes.ok) setKeys((await orgRes.json()).keys ?? []);
    if (myRes.ok) setMyKeys((await myRes.json()).keys ?? []);
  }, [projectId]);

  return (
    <div className="st-settings">
      <NewKeyForm
        projectId={projectId}
        scope="org"
        onCreated={() => void refresh()}
      />

      <h2 className="section-title">Org & project keys</h2>
      <KeyList
        keys={keys}
        onChanged={() => void refresh()}
        empty="No keys yet. Add one above — it is sealed in the KMS."
      />

      <h2 className="section-title" style={{ marginTop: 8 }}>
        My keys
      </h2>
      <p className="muted text-sm" style={{ marginBottom: 12 }}>
        Personal keys scoped to you — usable across every org you belong to.
      </p>
      <NewKeyForm scope="cross_org" onCreated={() => void refresh()} />
      <KeyList
        keys={myKeys}
        onChanged={() => void refresh()}
        empty="No personal keys yet."
      />
    </div>
  );
}

function NewKeyForm({
  projectId,
  scope,
  onCreated,
}: {
  projectId?: string;
  scope: "org" | "cross_org";
  onCreated: () => void;
}) {
  const [name, setName] = useState("");
  const [plaintext, setPlaintext] = useState("");
  const [keyScope, setKeyScope] = useState<"org" | "project">(
    scope === "cross_org" ? "org" : "org",
  );
  const [rateLimit, setRateLimit] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function create() {
    startTransition(async () => {
      setError(null);
      const input: KmsKeyInput = {
        name: name.trim(),
        plaintext,
        rateLimit: rateLimit ? Number(rateLimit) : undefined,
      };
      const url =
        scope === "cross_org"
          ? "/api/me/keys"
          : `/api/projects/${projectId}/keys`;
      if (scope !== "cross_org") {
        input.scope = keyScope;
      }
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      });
      const body = (await res.json().catch(() => ({}))) as {
        key?: KmsKey;
        error?: string;
      };
      if (!res.ok || !body.key) {
        setError(body.error ?? `Failed to create key (${res.status})`);
        return;
      }
      setName("");
      setPlaintext("");
      setRateLimit("");
      onCreated();
    });
  }

  return (
    <section className="st-panel" style={{ marginTop: 16 }}>
      <div className="form" style={{ padding: "12px 16px 16px" }}>
        <div className="field">
          <label>Name</label>
          <Input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={scope === "cross_org" ? "e.g. github-token" : "e.g. stripe-secret"}
            autoComplete="off"
          />
        </div>
        {scope !== "cross_org" ? (
          <div className="field">
            <label>Scope</label>
            <Select
              value={keyScope}
              onChange={(e) => setKeyScope(e.target.value as "org" | "project")}
            >
              <option value="org">Org (all projects)</option>
              <option value="project">This project only</option>
            </Select>
          </div>
        ) : null}
        <div className="field">
          <label>Value</label>
          <Input
            type="password"
            value={plaintext}
            onChange={(e) => setPlaintext(e.target.value)}
            placeholder="Paste the secret once"
            autoComplete="new-password"
          />
          <p className="muted text-sm">
            Stored once, sealed in the KMS. Never shown again except when you
            reveal it (each reveal is audited).
          </p>
        </div>
        <div className="field">
          <label>Rate limit (decrypts/min, optional)</label>
          <Input
            type="number"
            min={1}
            value={rateLimit}
            onChange={(e) => setRateLimit(e.target.value)}
            placeholder="60"
          />
        </div>
        {error ? <p className="auth-error">{error}</p> : null}
        <div style={{ display: "flex", gap: 8 }}>
          <Button
            variant="primary"
            size="sm"
            onClick={create}
            disabled={pending || !name.trim() || !plaintext}
          >
            {pending ? "Storing…" : "Store key"}
          </Button>
        </div>
      </div>
    </section>
  );
}

function KeyList({
  keys,
  onChanged,
  empty,
}: {
  keys: KmsKey[];
  onChanged: () => void;
  empty: string;
}) {
  if (!keys.length) {
    return <p className="muted text-sm" style={{ marginTop: 8 }}>{empty}</p>;
  }
  return (
    <div className="st-panel" style={{ marginTop: 8 }}>
      {keys.map((key) => (
        <KeyRow key={key.keyId} keyData={key} onChanged={onChanged} />
      ))}
    </div>
  );
}

function KeyRow({
  keyData,
  onChanged,
}: {
  keyData: KmsKey;
  onChanged: () => void;
}) {
  const [revealed, setRevealed] = useState<string | null>(null);
  const [newRate, setNewRate] = useState("");
  const [rotating, setRotating] = useState(false);
  const [newPlaintext, setNewPlaintext] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  function reveal() {
    startTransition(async () => {
      setError(null);
      const res = await fetch(`/api/keys/${keyData.keyId}/decrypt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: "{}",
      });
      const body = (await res.json().catch(() => ({}))) as {
        data?: string;
        error?: string;
      };
      if (!res.ok || !body.data) {
        setError(body.error ?? `Reveal failed (${res.status})`);
        return;
      }
      setRevealed(decodeB64url(body.data));
    });
  }

  function rotate() {
    startTransition(async () => {
      setError(null);
      const res = await fetch(`/api/keys/${keyData.keyId}/rotate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(newPlaintext ? { plaintext: newPlaintext } : {}),
      });
      const body = (await res.json().catch(() => ({}))) as {
        error?: string;
      };
      if (!res.ok) {
        setError(body.error ?? `Rotate failed (${res.status})`);
        return;
      }
      setRotating(false);
      setNewPlaintext("");
      setRevealed(null);
      onChanged();
    });
  }

  function saveRate() {
    startTransition(async () => {
      setError(null);
      const res = await fetch(`/api/keys/${keyData.keyId}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rateLimit: Number(newRate) }),
      });
      const body = (await res.json().catch(() => ({}))) as { error?: string };
      if (!res.ok) {
        setError(body.error ?? `Update failed (${res.status})`);
        return;
      }
      setNewRate("");
      onChanged();
    });
  }

  function remove() {
    if (!confirm(`Delete key "${keyData.name}"? This cannot be undone.`)) return;
    startTransition(async () => {
      setError(null);
      const res = await fetch(`/api/keys/${keyData.keyId}`, { method: "DELETE" });
      if (!res.ok) {
        const body = (await res.json().catch(() => ({}))) as { error?: string };
        setError(body.error ?? `Delete failed (${res.status})`);
        return;
      }
      onChanged();
    });
  }

  return (
    <div className="st-row" style={{ alignItems: "flex-start" }}>
      <div className="st-row-copy" style={{ flex: 1 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <strong>{keyData.name}</strong>
          {scopeBadge(keyData)}
          {keyData.expiresAt ? (
            <Badge variant="warning">expires {keyData.expiresAt}</Badge>
          ) : null}
        </div>
        <p className="muted text-sm">
          v{keyData.version} · {keyData.rateLimit}/min · updated{" "}
          {keyData.updatedAt}
        </p>
        {revealed ? (
          <div className="field" style={{ marginTop: 8, maxWidth: 420 }}>
            <Input
              readOnly
              value={revealed}
              onFocus={(e) => e.currentTarget.select()}
            />
            <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => void copyText(revealed)}
              >
                Copy
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setRevealed(null)}
              >
                Hide
              </Button>
            </div>
            <p className="muted text-sm" style={{ marginTop: 6 }}>
              This reveal was logged. The value is shown once — copy it now.
            </p>
          </div>
        ) : null}
        {rotating ? (
          <div className="field" style={{ marginTop: 8, maxWidth: 420 }}>
            <Input
              type="password"
              value={newPlaintext}
              onChange={(e) => setNewPlaintext(e.target.value)}
              placeholder="New value (blank = re-seal current)"
              autoComplete="new-password"
            />
            <div style={{ display: "flex", gap: 8, marginTop: 6 }}>
              <Button size="sm" variant="primary" onClick={rotate} disabled={pending}>
                {pending ? "Rotating…" : "Confirm rotate"}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setRotating(false)}
              >
                Cancel
              </Button>
            </div>
          </div>
        ) : null}
        {error ? <p className="auth-error">{error}</p> : null}
      </div>
      <div style={{ display: "flex", gap: 6, flexWrap: "wrap", justifyContent: "flex-end" }}>
        {!revealed ? (
          <Button size="sm" variant="secondary" onClick={reveal} disabled={pending}>
            Reveal
          </Button>
        ) : null}
        <Button
          size="sm"
          variant="secondary"
          onClick={() => setRotating(true)}
          disabled={pending || rotating}
        >
          Rotate
        </Button>
        <span style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
          <Input
            type="number"
            min={1}
            value={newRate}
            onChange={(e) => setNewRate(e.target.value)}
            placeholder={`${keyData.rateLimit}`}
            style={{ width: 72 }}
          />
          <Button
            size="sm"
            variant="ghost"
            onClick={saveRate}
            disabled={pending || !newRate}
          >
            Set
          </Button>
        </span>
        <Button size="sm" variant="destructive" onClick={remove} disabled={pending}>
          Delete
        </Button>
      </div>
    </div>
  );
}