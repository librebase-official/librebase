"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

export function LandingPage() {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) {
      setReady(true);
      return;
    }
    const id = requestAnimationFrame(() => setReady(true));
    return () => cancelAnimationFrame(id);
  }, []);

  return (
    <div className={`lb-landing${ready ? " is-ready" : ""}`}>
      <header className="lb-nav">
        <Link href="/" className="lb-wordmark" aria-label="Librebase home">
          Libre<span>base</span>
        </Link>
        <div className="lb-nav-actions">
          <a className="lb-link-quiet" href="#faq">
            FAQ
          </a>
          <a className="lb-btn lb-btn-primary" href="#waitlist">
            Join the waitlist
          </a>
        </div>
      </header>

      <section className="lb-hero" aria-label="Hero">
        <div className="lb-hero-copy">
          <p className="lb-brand-signal">Librebase</p>
          <h1 className="lb-hero-title">High-performance Postgres, written in Li.</h1>
          <p className="lb-hero-sub">
            Low memory. Strong security defaults. Auth, REST, and Realtime for teams and agents
            building on a Postgres-compatible stack.
          </p>
          <div className="lb-cta-row">
            <a className="lb-btn lb-btn-primary lb-btn-lg" href="#waitlist">
              Join the waitlist for early access
            </a>
            <Link className="lb-btn lb-btn-ghost lb-btn-lg" href="/projects">
              Open Studio
            </Link>
          </div>
        </div>
        <div className="lb-hero-visual" aria-hidden="true">
          <ProductMesh />
        </div>
      </section>

      <section className="lb-proof" aria-label="Proof">
        <p>
          Native Li runtime — small footprint, no GC pauses, Studio that reports real health instead
          of fake greens.
        </p>
      </section>

      <section className="lb-band lb-reveal" id="promise">
        <h2>Agents need a database that keeps up.</h2>
        <p>
          Short-lived sessions, machine-speed API calls, and Auth on every request. Librebase is a
          Postgres-compatible platform aimed at that workload — not a port of yesterday&rsquo;s
          monolith.
        </p>
      </section>

      <section className="lb-band" id="how">
        <h2>How it works</h2>
        <ol className="lb-steps">
          <li>
            <strong>Create a project</strong>
            <span>Dedicated instance or shared runtime.</span>
          </li>
          <li>
            <strong>Connect</strong>
            <span>Postgres protocol, REST, and Auth from the first boot.</span>
          </li>
          <li>
            <strong>Operate</strong>
            <span>RLS, Studio SQL, MCP tools for agents.</span>
          </li>
        </ol>
      </section>

      <section className="lb-band" id="features">
        <h2>What you get</h2>
        <ul className="lb-benefits">
          <li>
            <strong>Small footprint</strong>
            <span>Lean native binary — fit for dense hosts and edge-adjacent boxes.</span>
          </li>
          <li>
            <strong>Security defaults</strong>
            <span>Auth and row-level security in the path, not bolted on later.</span>
          </li>
          <li>
            <strong>Agent APIs</strong>
            <span>MCP plus REST so agents can query and manage without a human in the loop.</span>
          </li>
          <li>
            <strong>Studio</strong>
            <span>Projects, SQL, and status in one console.</span>
          </li>
        </ul>
      </section>

      <section className="lb-band" id="waitlist">
        <h2>Join the waitlist for early access</h2>
        <p>Get notified when Cloud and dedicated instances open.</p>
        <WaitlistForm />
      </section>

      <section className="lb-band" id="matrix">
        <h2>Ship when tests pass</h2>
        <p>
          Capability rows stay incomplete until contracts are green. Read the matrix if you want the
          honest status.
        </p>
        <a
          className="lb-btn lb-btn-ghost"
          href="https://github.com/librebase-official/librebase/blob/main/docs/lidb-capability-matrix.md"
        >
          Capability matrix
        </a>
      </section>

      <section className="lb-band lb-faq" id="faq">
        <h2>FAQ</h2>
        <details>
          <summary>Is this a full Supabase replacement?</summary>
          <p>
            Not yet. Core path first: SQL, REST, Auth, RLS. Storage and Edge follow when those
            contracts pass.
          </p>
        </details>
        <details>
          <summary>What is Li?</summary>
          <p>
            A systems language that compiles to native code. Librebase&rsquo;s engine and supervisor
            path are Li-first for speed and a small memory profile.
          </p>
        </details>
        <details>
          <summary>Can I self-host?</summary>
          <p>Yes — local binary or Docker. Cloud waitlist is for hosted instances.</p>
        </details>
        <details>
          <summary>How do agents use it?</summary>
          <p>MCP tools for projects, health, and SQL-shaped workflows; REST for app clients.</p>
        </details>
        <details>
          <summary>Dedicated vs shared?</summary>
          <p>Dedicated: one instance per project. Shared: many projects on one runtime.</p>
        </details>
      </section>

      <section className="lb-final">
        <h2>Join the waitlist for early access</h2>
        <p>Studio is open on this host today.</p>
        <div className="lb-cta-row">
          <a className="lb-btn lb-btn-primary lb-btn-lg" href="#waitlist">
            Join the waitlist for early access
          </a>
          <Link className="lb-btn lb-btn-ghost lb-btn-lg" href="/projects">
            Open Studio
          </Link>
        </div>
      </section>

      <footer className="lb-footer">
        <span className="lb-wordmark">
          Libre<span>base</span>
        </span>
        <div className="lb-footer-links">
          <Link href="/projects">Studio</Link>
          <Link href="/setup">Setup</Link>
          <a href="https://github.com/librebase-official/librebase">GitHub</a>
        </div>
      </footer>
    </div>
  );
}

function ProductMesh() {
  return (
    <div className="lb-mesh">
      <div className="lb-mesh-glow" />
      <svg className="lb-mesh-svg" viewBox="0 0 960 720" role="presentation">
        <defs>
          <linearGradient id="lbStream" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#2FD4C2" stopOpacity="0" />
            <stop offset="45%" stopColor="#2FD4C2" stopOpacity="0.85" />
            <stop offset="100%" stopColor="#2FD4C2" stopOpacity="0" />
          </linearGradient>
        </defs>
        <rect x="72" y="88" width="520" height="360" rx="18" className="lb-panel-a" />
        <rect x="120" y="140" width="180" height="14" rx="4" className="lb-row" />
        <rect x="120" y="172" width="420" height="14" rx="4" className="lb-row" />
        <rect x="120" y="204" width="360" height="14" rx="4" className="lb-row" />
        <rect x="120" y="236" width="400" height="14" rx="4" className="lb-row" />
        <rect x="120" y="268" width="280" height="14" rx="4" className="lb-row" />
        <rect x="340" y="220" width="420" height="320" rx="18" className="lb-panel-b" />
        <text x="372" y="268" className="lb-sql">
          select * from parity_items
        </text>
        <text x="372" y="304" className="lb-sql lb-sql-dim">
          where owner_id = auth.uid()
        </text>
        <path
          d="M180 520 C 320 460, 520 600, 760 420"
          fill="none"
          stroke="url(#lbStream)"
          strokeWidth="3"
          className="lb-stream"
        />
        <circle cx="760" cy="420" r="8" className="lb-pulse" />
      </svg>
    </div>
  );
}

function WaitlistForm() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "ok" | "err">("idle");
  const [message, setMessage] = useState("");

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setStatus("loading");
    setMessage("");
    try {
      const res = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, source: "landing" }),
      });
      const data = (await res.json()) as { ok?: boolean; error?: string };
      if (!res.ok || !data.ok) {
        setStatus("err");
        setMessage(
          data.error === "invalid_email"
            ? "Enter a valid email."
            : "Could not join right now. Try again shortly.",
        );
        return;
      }
      setStatus("ok");
      setMessage("You are on the list.");
      setEmail("");
    } catch {
      setStatus("err");
      setMessage("Network error. Try again.");
    }
  }

  return (
    <form className="lb-waitlist" onSubmit={onSubmit}>
      <label className="lb-waitlist-label" htmlFor="lb-waitlist-email">
        Work email
      </label>
      <div className="lb-waitlist-row">
        <input
          id="lb-waitlist-email"
          type="email"
          required
          autoComplete="email"
          placeholder="you@company.com"
          value={email}
          onChange={(ev) => setEmail(ev.target.value)}
          disabled={status === "loading"}
        />
        <button className="lb-btn lb-btn-primary" type="submit" disabled={status === "loading"}>
          {status === "loading" ? "Joining…" : "Join the waitlist for early access"}
        </button>
      </div>
      {message ? (
        <p className={`lb-waitlist-msg${status === "err" ? " is-err" : ""}`}>{message}</p>
      ) : null}
    </form>
  );
}
