"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

export default function SetupPage() {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("Local Org");
  const [ownerEmail, setOwnerEmail] = useState("");
  const [password, setPassword] = useState("");

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    startTransition(async () => {
      const res = await fetch("/api/admin/setup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, ownerEmail, password }),
      });
      const body = (await res.json()) as { error?: string; orgId?: string };
      if (!res.ok) {
        setError(body.error ?? `Setup failed (${res.status})`);
        return;
      }
      router.push("/");
      router.refresh();
    });
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1>Librebase Admin setup</h1>
        <p className="muted">
          Create the first operator account for this console. Use the same email
          you sign in with via GitHub or Google.
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
