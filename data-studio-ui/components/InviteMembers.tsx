"use client";

import { useState, useTransition } from "react";
import { adminCreateInvite, AdminInvite } from "@/lib/librebase-admin-client";
import { copyText } from "@/lib/clipboard";

export function InviteMembers({ orgId }: { orgId: string }) {
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"developer" | "admin">("developer");
  const [pending, startTransition] = useTransition();
  const [sent, setSent] = useState<AdminInvite | null>(null);
  const [error, setError] = useState<string | null>(null);

  const submit = () =>
    startTransition(async () => {
      setError(null);
      try {
        const res = await adminCreateInvite(orgId, { email, role });
        setSent(res);
      } catch (e) {
        setError(e instanceof Error ? e.message : "invite failed");
      }
    });

  return (
    <section style={{ marginTop: "2rem" }}>
      <h2 style={{ fontSize: "1.1rem" }}>Invite members</h2>
      <p className="muted">
        Send the invite link below to add someone to this organization.
      </p>
      {!sent ? (
        <form
          className="form"
          onSubmit={(e) => {
            e.preventDefault();
            submit();
          }}
        >
          <div className="field">
            <label htmlFor="invite-email">Email</label>
            <input
              id="invite-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
              disabled={pending}
            />
          </div>
          <div className="field">
            <label htmlFor="invite-role">Role</label>
            <select
              id="invite-role"
              value={role}
              onChange={(e) => setRole(e.target.value as typeof role)}
              disabled={pending}
            >
              <option value="developer">Developer</option>
              <option value="admin">Admin</option>
            </select>
          </div>
          {error ? <p className="auth-error">{error}</p> : null}
          <button type="submit" className="btn btn-primary" disabled={pending}>
            {pending ? "Sending…" : "Create invite"}
          </button>
        </form>
      ) : (
        <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
          <code>{sent.role}</code>
          <span className="muted">invite created for {sent.email}</span>
          <a
            href={`/invite/${sent.token}`}
            className="btn"
            target="_blank"
            rel="noreferrer"
          >
            Copy link
          </a>
          <button
            className="btn btn-ghost"
            style={{ fontSize: "0.8rem" }}
            onClick={async () => {
              await copyText(`${window.location.origin}/invite/${sent.token}`);
              setSent(null);
              setEmail("");
            }}
          >
            Copy
          </button>
        </div>
      )}
    </section>
  );
}
