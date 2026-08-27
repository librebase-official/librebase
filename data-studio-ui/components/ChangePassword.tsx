"use client";

import { useState } from "react";
import { Button, FormField, Input } from "@/components/ui";

export function ChangePassword() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    setDone(false);
    try {
      const res = await fetch("/api/admin/password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ currentPassword: current, newPassword: next }),
      });
      const data = (await res.json().catch(() => ({}))) as { error?: string };
      if (!res.ok) {
        throw new Error(data.error ?? `Failed (${res.status})`);
      }
      setDone(true);
      setCurrent("");
      setNext("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not change password");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="card admin-section">
      <h2 className="admin-section-title">Change password</h2>
      <form className="form" onSubmit={onSubmit} style={{ maxWidth: 360 }}>
        <FormField label="Current password" htmlFor="pw-current">
          <Input
            id="pw-current"
            type="password"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            autoComplete="current-password"
            required
            disabled={busy}
          />
        </FormField>
        <FormField label="New password" htmlFor="pw-next">
          <Input
            id="pw-next"
            type="password"
            value={next}
            onChange={(e) => setNext(e.target.value)}
            autoComplete="new-password"
            required
            minLength={6}
            disabled={busy}
          />
        </FormField>
        {error ? <p className="auth-error text-sm">{error}</p> : null}
        {done ? <p className="muted text-sm" style={{ color: "var(--accent)" }}>Password updated.</p> : null}
        <Button type="submit" variant="primary" disabled={busy}>
          {busy ? "Updating…" : "Update password"}
        </Button>
      </form>
    </section>
  );
}
