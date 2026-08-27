"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { copyText } from "@/lib/clipboard";

export default function SetupPage() {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("Local Org");
  const [ownerEmail, setOwnerEmail] = useState("");
  const [password, setPassword] = useState("");
  const [done, setDone] = useState<{ orgId: string; mcpKey: string } | null>(null);
  const [copied, setCopied] = useState(false);

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    startTransition(async () => {
      const res = await fetch("/api/admin/setup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, ownerEmail, password }),
      });
      const body = (await res.json()) as {
        error?: string;
        orgId?: string;
        mcpKey?: string;
      };
      if (!res.ok) {
        setError(body.error ?? `Setup failed (${res.status})`);
        return;
      }
      setDone({ orgId: body.orgId ?? "", mcpKey: body.mcpKey ?? "" });
    });
  }

  async function copyKey() {
    if (!done?.mcpKey) return;
    const ok = await copyText(done.mcpKey);
    setCopied(ok);
    setTimeout(() => setCopied(false), 2000);
  }

  if (done) {
    return (
      <div className="auth-page">
        <div className="auth-card">
          <h1>Organization created</h1>
          <p className="muted">
            Save your MCP key now — it is shown only once.
          </p>
          <code
            style={{
              display: "block",
              wordBreak: "break-all",
              padding: "0.7rem",
              margin: "1rem 0",
              background: "var(--bg)",
              border: "1px solid var(--border)",
              borderRadius: "var(--radius)",
              color: "var(--accent)",
            }}
          >
            {done.mcpKey}
          </code>
          <div style={{ display: "flex", gap: "0.6rem" }}>
            <button className="btn btn-primary" onClick={copyKey}>
              {copied ? "Copied" : "Copy key"}
            </button>
            <button className="btn" onClick={() => router.push("/")}>
              Go to console
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Librebase Admin setup</h1>
        <p className="muted">
          Create the first operator account. You&apos;ll get an MCP key for AI
          tool access.
        </p>

        <form className="form" onSubmit={onSubmit}>
          <div className="field">
            <label htmlFor="setup-name">Organization name</label>
            <input
              id="setup-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <div className="field">
            <label htmlFor="setup-email">Owner email</label>
            <input
              id="setup-email"
              type="email"
              value={ownerEmail}
              onChange={(e) => setOwnerEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </div>
          <div className="field">
            <label htmlFor="setup-password">Password</label>
            <input
              id="setup-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
              required
              minLength={6}
            />
          </div>
          {error ? <p className="auth-error">{error}</p> : null}
          <button type="submit" className="btn btn-primary" disabled={pending}>
            {pending ? "Creating…" : "Create organization"}
          </button>
        </form>
      </div>
    </div>
  );
}

