"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

export default function LoginPage() {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState("owner@localhost");
  const [password, setPassword] = useState("");

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    startTransition(async () => {
      const res = await fetch("/api/admin/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const body = (await res.json()) as { error?: string };
      if (!res.ok) {
        setError(body.error ?? `Login failed (${res.status})`);
        return;
      }
      router.push("/admin");
      router.refresh();
    });
  }

  return (
    <div className="main" style={{ maxWidth: 420, margin: "4rem auto" }}>
      <h1>Operator login</h1>
      <p className="muted">
        Sign in to Librebase Admin. Requires{" "}
        <code>LIBREBASE_ADMIN_URL</code>.
      </p>
      <form
        onSubmit={onSubmit}
        style={{ display: "grid", gap: "0.75rem", marginTop: "1.5rem" }}
      >
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
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
          />
        </label>
        {error && <p style={{ color: "var(--danger)" }}>{error}</p>}
        <button type="submit" className="btn btn-primary" disabled={pending}>
          {pending ? "Signing in…" : "Sign in"}
        </button>
      </form>
      <p className="muted" style={{ marginTop: "1.5rem" }}>
        First run? <Link href="/setup">Create organization</Link>
      </p>
    </div>
  );
}
