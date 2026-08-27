"use client";

import { useCallback, useEffect, useState } from "react";
import { DEMO_API_URL, DEMO_PROJECT_ID, FEEDBACK_ORIGIN } from "@/lib/demo";
import { SITE_URL } from "@/lib/site";

type Note = {
  id: string;
  body: string;
  author?: string;
  email?: string;
  created_at?: string;
  owner_id?: string;
};

const TOKEN_KEY = "lb_feedback_token";

function oauthStart(provider: "github" | "google") {
  // Same-origin on the wall so a missing provider never dumps people on Studio /login.
  return `/api/projects/${DEMO_PROJECT_ID}/auth/oauth/start?provider=${provider}&redirect_to=${encodeURIComponent(FEEDBACK_ORIGIN)}`;
}

function readUser(token: string): { email?: string; sub?: string } {
  try {
    const payload = token.split(".")[1];
    const json = JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
    return { email: json.email, sub: json.sub };
  } catch {
    return {};
  }
}

function sessionToken(payload: unknown): string | null {
  if (!payload || typeof payload !== "object") return null;
  const rec = payload as Record<string, unknown>;
  const nested = rec.data && typeof rec.data === "object" ? (rec.data as Record<string, unknown>) : rec;
  const token = nested.access_token ?? nested.accessToken;
  return typeof token === "string" && token ? token : null;
}

export function FeedbackWall() {
  const [token, setToken] = useState<string | null>(null);
  const [notes, setNotes] = useState<Note[]>([]);
  const [body, setBody] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const user = token ? readUser(token) : {};

  const load = useCallback(async (access: string | null) => {
    setLoading(true);
    try {
      const headers: Record<string, string> = { apikey: "anon" };
      if (access) headers.Authorization = `Bearer ${access}`;
      const res = await fetch(`${DEMO_API_URL}/rest/v1/notes?limit=50`, { headers });
      if (res.status === 404) {
        setNotes([]);
        return;
      }
      const data = await res.json();
      setNotes(Array.isArray(data) ? data : []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load notes");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.hash.replace(/^#/, ""));
    const fromHash = params.get("access_token");
    const oauthErr = new URLSearchParams(window.location.search).get("oauth_error");
    if (oauthErr) {
      setError(
        oauthErr === "provider not configured"
          ? "OAuth is not configured yet. Open Setup and paste GitHub/Google keys in the browser — not in chat."
          : oauthErr,
      );
    }
    if (fromHash) {
      localStorage.setItem(TOKEN_KEY, fromHash);
      setToken(fromHash);
      history.replaceState(null, "", window.location.pathname);
      void load(fromHash);
      return;
    }
    const stored = localStorage.getItem(TOKEN_KEY);
    setToken(stored);
    void load(stored);
  }, [load]);

  async function publish(e: React.FormEvent) {
    e.preventDefault();
    if (!token || !body.trim()) return;
    setError(null);
    const res = await fetch(`${DEMO_API_URL}/rest/v1/notes`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        apikey: "anon",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        body: body.trim(),
        email: user.email ?? "",
        author: user.email ?? "someone",
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      setError(
        typeof data === "object" && data && "error" in data
          ? String((data as { error: string }).error)
          : `Post failed (${res.status})`,
      );
      return;
    }
    setBody("");
    await load(token);
  }

  async function passwordAuth(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const path = mode === "signup" ? "/v1/auth/signup" : "/v1/auth/login";
      const res = await fetch(`${DEMO_API_URL}${path}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          apikey: "anon",
        },
        body: JSON.stringify({ email: email.trim(), password }),
      });
      const data = await res.json().catch(() => ({}));
      const access = sessionToken(data);
      if (!res.ok || !access) {
        setError(
          typeof data === "object" && data && "error" in data
            ? String((data as { error: string; message?: string }).message || (data as { error: string }).error)
            : `${mode} failed (${res.status})`,
        );
        return;
      }
      localStorage.setItem(TOKEN_KEY, access);
      setToken(access);
      setPassword("");
      await load(access);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Auth failed");
    } finally {
      setBusy(false);
    }
  }

  function signOut() {
    localStorage.removeItem(TOKEN_KEY);
    setToken(null);
  }

  async function beginOAuth(provider: "github" | "google") {
    setError(null);
    setBusy(true);
    try {
      const res = await fetch(oauthStart(provider), {
        headers: { Accept: "application/json" },
        cache: "no-store",
      });
      const data = (await res.json().catch(() => ({}))) as { url?: string; error?: string };
      if (!res.ok || !data.url) {
        const reason = data.error ?? `oauth (${res.status})`;
        setError(
          reason === "provider not configured"
            ? "OAuth is not configured yet. Open Setup and paste GitHub/Google keys in the browser — not in chat."
            : reason,
        );
        return;
      }
      window.location.assign(data.url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "OAuth failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fb-page">
      <header className="fb-bar">
        <a className="fb-wordmark" href={FEEDBACK_ORIGIN}>
          Libre<span>base</span>
          <em> / feedback</em>
        </a>
        <div className="fb-bar-right">
          {token ? (
            <>
              <span className="fb-who">{user.email || "signed in"}</span>
              <button type="button" className="fb-btn ghost" onClick={signOut}>
                Sign out
              </button>
            </>
          ) : (
            <a className="fb-btn ghost" href={`${SITE_URL}/demo/feedback/setup`}>
              Operator setup
            </a>
          )}
        </div>
      </header>

      <main className="fb-main">
        <p className="fb-kicker">Same auth your app would use</p>
        <h1>Feedback wall</h1>
        <p className="fb-sub">
          Email/password is on by default. GitHub and Google use the <strong>project</strong>{" "}
          OAuth apps from setup — not Studio operator login.
        </p>

        {error ? <p className="fb-error">{error}</p> : null}

        {!token ? (
          <div className="fb-card">
            <p className="fb-card-title">Sign in to post</p>
            <div className="fb-tabs">
              <button
                type="button"
                className={mode === "signin" ? "active" : ""}
                onClick={() => setMode("signin")}
              >
                Sign in
              </button>
              <button
                type="button"
                className={mode === "signup" ? "active" : ""}
                onClick={() => setMode("signup")}
              >
                Create account
              </button>
            </div>
            <form className="fb-auth-form" onSubmit={passwordAuth}>
              <label htmlFor="fb-email">Email</label>
              <input
                id="fb-email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
              <label htmlFor="fb-password">Password</label>
              <input
                id="fb-password"
                type="password"
                autoComplete={mode === "signup" ? "new-password" : "current-password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                minLength={6}
                required
              />
              <button type="submit" className="fb-btn primary" disabled={busy}>
                {busy ? "Please wait…" : mode === "signup" ? "Create account" : "Sign in"}
              </button>
            </form>
            <p className="fb-divider">or</p>
            <div className="fb-oauth">
              <button
                type="button"
                className="fb-btn"
                disabled={busy}
                onClick={() => void beginOAuth("github")}
              >
                Continue with GitHub
              </button>
              <button
                type="button"
                className="fb-btn"
                disabled={busy}
                onClick={() => void beginOAuth("google")}
              >
                Continue with Google
              </button>
            </div>
            <p className="fb-hint">
              Operators: paste GitHub/Google client ID/secret at{" "}
              <a href={`${SITE_URL}/demo/feedback/setup`}>setup</a>. Never in chat.
            </p>
          </div>
        ) : (
          <form className="fb-card" onSubmit={publish}>
            <label htmlFor="fb-body">Your note</label>
            <textarea
              id="fb-body"
              rows={4}
              value={body}
              onChange={(e) => setBody(e.target.value)}
              placeholder="What should we build next?"
              required
            />
            <button type="submit" className="fb-btn primary" disabled={!body.trim()}>
              Post
            </button>
          </form>
        )}

        <section className="fb-list">
          <h2>Wall</h2>
          {loading ? <p className="fb-hint">Loading…</p> : null}
          {!loading && notes.length === 0 ? (
            <p className="fb-hint">No notes yet. Sign in and be the first.</p>
          ) : null}
          {notes.map((n) => (
            <article key={n.id} className="fb-note">
              <p>{n.body}</p>
              <footer>
                {n.email || n.author || "anonymous"}
                {n.created_at ? ` · ${n.created_at}` : ""}
              </footer>
            </article>
          ))}
        </section>
      </main>
    </div>
  );
}
