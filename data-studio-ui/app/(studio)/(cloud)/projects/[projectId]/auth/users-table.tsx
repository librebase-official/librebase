"use client";

import { useEffect, useState } from "react";
import { EmptyState } from "@/components/studio/EmptyState";
import { IconAuth, IconPlus } from "@/components/studio/icons";

interface AuthUser {
  id?: string;
  email?: string;
  phone?: string;
  created_at?: string;
  app_metadata?: { providers?: string[] };
  user_metadata?: { display_name?: string };
}

export function UsersTable({ projectId }: { projectId: string }) {
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [creating, setCreating] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const res = await fetch(`/api/projects/${projectId}/auth/users`);
      const body = (await res.json()) as {
        users?: AuthUser[];
        message?: string;
        ok?: boolean;
      };
      setUsers(Array.isArray(body.users) ? body.users : []);
      setMessage(body.ok ? null : (body.message ?? null));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  async function addUser(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    try {
      await fetch(`/api/projects/${projectId}/auth/users`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      setEmail("");
      setPassword("");
      await load();
    } finally {
      setCreating(false);
    }
  }

  const visible = users.filter((u) =>
    q.trim() ? (u.email ?? "").toLowerCase().includes(q.toLowerCase()) : true,
  );

  return (
    <>
      <div className="st-toolbar">
        <input
          className="input"
          style={{ maxWidth: 280 }}
          placeholder="Search by email"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <span className="st-grow" />
        <form className="flex-gap" onSubmit={addUser}>
          <input
            className="input"
            type="email"
            placeholder="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            className="input"
            type="password"
            placeholder="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button type="submit" className="btn btn-sm btn-primary" disabled={creating}>
            <IconPlus width="14" height="14" />
            Add user
          </button>
        </form>
      </div>

      {loading ? (
        <div className="st-panel" style={{ padding: 16 }}>
          <div className="st-skel" />
          <div className="st-skel" style={{ width: "75%" }} />
        </div>
      ) : visible.length === 0 ? (
        <EmptyState
          icon={<IconAuth />}
          title="No users"
          body={message ?? "Add a user or wait for signups."}
        />
      ) : (
        <div className="st-panel" style={{ overflow: "auto" }}>
          <table className="table">
            <thead>
              <tr>
                <th>UID</th>
                <th>Display name</th>
                <th>Email</th>
                <th>Phone</th>
                <th>Providers</th>
              </tr>
            </thead>
            <tbody>
              {visible.map((u, i) => (
                <tr key={u.id ?? i}>
                  <td className="mono">{u.id ?? "—"}</td>
                  <td>{u.user_metadata?.display_name ?? "—"}</td>
                  <td>{u.email ?? "—"}</td>
                  <td>{u.phone ?? "—"}</td>
                  <td className="muted">
                    {(u.app_metadata?.providers ?? []).join(", ") || "email"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
