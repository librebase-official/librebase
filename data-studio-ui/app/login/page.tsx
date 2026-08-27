"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition, useCallback } from "react";

function GitHubIcon() {
  return (
    <svg viewBox="0 0 16 16" aria-hidden="true" fill="currentColor">
      <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27s1.36.09 2 .27c1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.01 8.01 0 0 0 16 8c0-4.42-3.58-8-8-8z" />
    </svg>
  );
}

function GoogleIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M23.49 12.27c0-.79-.07-1.54-.19-2.27H12v4.51h6.47c-.29 1.48-1.14 2.73-2.4 3.58v3h3.86c2.26-2.09 3.56-5.17 3.56-8.82z"
      />
      <path
        fill="#34A853"
        d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.86-3c-1.08.72-2.45 1.16-4.07 1.16-3.13 0-5.78-2.11-6.73-4.96H1.29v3.09C3.26 21.3 7.31 24 12 24z"
      />
      <path
        fill="#FBBC05"
        d="M5.27 14.29c-.25-.72-.38-1.49-.38-2.29s.14-1.57.38-2.29V6.62H1.29C.47 8.24 0 10.06 0 12s.47 3.76 1.29 5.38l3.98-3.09z"
      />
      <path
        fill="#EA4335"
        d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.31 0 3.26 2.7 1.29 6.62l3.98 3.09C6.22 6.86 8.87 4.75 12 4.75z"
      />
    </svg>
  );
}

function GrokIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" fill="currentColor">
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  );
}

type GrokStep = "idle" | "showing_code" | "polling" | "success" | "error";

export default function LoginPage() {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // Grok device code flow state
  const [grokStep, setGrokStep] = useState<string>("idle");
  const [grokUserCode, setGrokUserCode] = useState("");
  const [grokVerificationUri, setGrokVerificationUri] = useState("");
  const [grokError, setGrokError] = useState<string | null>(null);

  const pollGrok = useCallback(
    async (deviceCode: string, interval: number) => {
      setGrokStep("polling");
      const maxAttempts = 120; // ~10 minutes at 5s intervals
      for (let i = 0; i < maxAttempts; i++) {
        await new Promise((r) => setTimeout(r, interval * 1000));
        try {
          const res = await fetch(
            `/api/admin/grok/poll?deviceCode=${encodeURIComponent(deviceCode)}`,
          );
          const body = await res.json();
          if (body.token) {
            // Success — set session cookies and redirect
            setGrokStep("success");
            document.cookie = `lb_session=${body.token}; path=/; max-age=${15 * 60}; SameSite=Lax`;
            document.cookie = `lb_refresh=${body.refreshToken}; path=/; max-age=${30 * 24 * 60 * 60}; SameSite=Lax`;
            router.push("/projects");
            router.refresh();
            return;
          }
          if (body.status === "pending") {
            // Continue polling
            if (body.slowDown) {
              interval = Math.min(interval + 2, 15);
            }
            continue;
          }
          // Error
          setGrokError(body.error || "Grok login failed");
          setGrokStep("error");
          return;
        } catch {
          // Network error, keep trying
          continue;
        }
      }
      setGrokError("Timed out waiting for Grok approval");
      setGrokStep("error");
    },
    [router],
  );

  async function startGrokLogin() {
    setGrokError(null);
    setGrokStep("showing_code");
    try {
      const res = await fetch("/api/admin/grok/start");
      const body = await res.json();
      if (!res.ok) {
        setGrokError(body.error || "Failed to start Grok login");
        setGrokStep("error");
        return;
      }
      setGrokUserCode(body.userCode || "");
      setGrokVerificationUri(body.verificationUri || "https://accounts.x.ai/oauth2/device");  // user visits this URL to enter the code
      pollGrok(body.deviceCode, body.interval || 5);
    } catch {
      setGrokError("Failed to connect to server");
      setGrokStep("error");
    }
  }

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
    <div className="auth-page">
      <div className="auth-card">
        <p className="st-wordmark" style={{ border: 0, padding: 0, height: "auto", marginBottom: 16 }}>
          Libre<em>base</em>
        </p>
        <h1>Operator login</h1>
        <p className="muted">Sign in to the console. Status inside stays honest.</p>

        {/* Grok device code flow — show code when active */}
        {grokStep === "showing_code" || grokStep === "polling" ? (
          <div className="grok-device-flow">
            <div className="grok-code-box">
              <p className="grok-label">Sign in with Grok at:</p>
              <a
                className="grok-verification-url"
                href={grokVerificationUri}
                target="_blank"
                rel="noopener noreferrer"
              >
                {grokVerificationUri}
              </a>
              <p className="grok-code-label">Enter this code:</p>
              <p className="grok-user-code">{grokUserCode}</p>
              <p className="muted grok-status">
                {grokStep === "polling"
                  ? "Waiting for approval…"
                  : "Open the URL and enter the code"}
              </p>
            </div>
            {grokStep === "polling" && (
              <button
                className="btn btn-secondary"
                type="button"
                onClick={() => {
                  setGrokStep("idle");
                }}
              >
                Cancel
              </button>
            )}
          </div>
        ) : (
          <div className="auth-oauth">
            <a className="btn oauth-btn" href="/api/admin/oauth/start?provider=github">
              <GitHubIcon /> Continue with GitHub
            </a>
            <a className="btn oauth-btn" href="/api/admin/oauth/start?provider=google">
              <GoogleIcon /> Continue with Google
            </a>
            <button
              className="btn oauth-btn grok-btn"
              type="button"
              onClick={startGrokLogin}
              disabled={grokStep === "showing_code" || grokStep === "polling"}
            >
              <GrokIcon /> Continue with Grok
            </button>
          </div>
        )}

        {grokError && <p className="auth-error">{grokError}</p>}

        <div className="auth-divider">or with email</div>

        <form className="form" onSubmit={onSubmit}>
          <div className="field">
            <label htmlFor="login-email">Email</label>
            <input
              id="login-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />
          </div>
          <div className="field">
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
              required
            />
          </div>
          {error ? <p className="auth-error">{error}</p> : null}
          <button type="submit" className="btn btn-primary" disabled={pending}>
            {pending ? "Signing in…" : "Sign in"}
          </button>
        </form>

        <p className="muted auth-foot">
          First run? <Link href="/setup">Create organization</Link>
        </p>
      </div>
    </div>
  );
}
