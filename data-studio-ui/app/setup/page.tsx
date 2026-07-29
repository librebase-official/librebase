"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

export default function SetupPage() {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [name, setName] = useState("Local Org");
  const [ownerEmail, setOwnerEmail] = useState("owner@localhost");
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
    <div className="main" style={{ maxWidth: 420, margin: "4rem auto" }}>
      <h1>Librebase Admin setup</h1>
      <p className="muted">
        First-run operator account for this Studio. Requires Admin API (
        <code>LIBREBASE_ADMIN_URL</code>).
      </p>
      <form onSubmit={onSubmit} style={{ display: "grid", gap: "0.75rem", marginTop: "1.5rem" }}>
        <label>
          Organization name
          <input value={name} onChange={(e) => setName(e.target.value)} required />
        </label>
        <label>
          Owner email
          <input
            type="email"
            value={ownerEmail}
            onChange={(e) => setOwnerEmail(e.target.value)}
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
          />
        </label>
        {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
        <button type="submit" className="btn btn-primary" disabled={pending}>
          {pending ? "Creating…" : "Create organization"}
        </button>
      </form>
    </div>
  );
}
