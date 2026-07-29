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
          <a className="lb-link-quiet" href="#matrix">
            Capability matrix
          </a>
          <Link className="lb-btn lb-btn-primary" href="#waitlist">
            Join waitlist
          </Link>
        </div>
      </header>

      <section className="lb-hero" aria-label="Hero">
        <div className="lb-hero-copy">
          <p className="lb-brand-signal">Librebase</p>
          <h1 className="lb-hero-title">The database your agents deserve.</h1>
          <p className="lb-hero-sub">
            A high-performance Postgres-compatible database written in Li. Tiny memory footprint.
            Provable security. Auth, REST, and Realtime out of the box &mdash; built for agentic
            development from day one.
          </p>
          <div className="lb-cta-row">
            <a className="lb-btn lb-btn-primary lb-btn-lg" href="#waitlist">
              Join waitlist
            </a>
            <Link className="lb-btn lb-btn-ghost lb-btn-lg" href="/projects">
              Open Studio
            </Link>
          </div>
          <p className="lb-reassure">Early access for builders. No spam.</p>
        </div>
        <div className="lb-hero-visual" aria-hidden="true">
          <ProductMesh />
        </div>
      </section>

      <section className="lb-proof" aria-label="Proof">
        <p>
          Written in <strong>Li</strong> and compiled to native code &mdash; no garbage collector,
          no runtime overhead, just raw speed with formal safety guarantees.
        </p>
      </section>

      <section className="lb-band" id="waitlist">
        <h2>Get early access</h2>
        <p>Be the first to run Librebase Cloud when dedicated instances go live.</p>
        <WaitlistForm />
      </section>

      <section className="lb-band lb-reveal" id="promise">
        <h2>Why Librebase?</h2>
        <p>
          Traditional databases weren&rsquo;t designed for agents that spin up hundreds of sessions,
          need instant Auth, and call your API at machine speed. Librebase was.
        </p>
      </section>

      <section className="lb-band" id="how">
        <h2>How it works</h2>
        <ol className="lb-steps">
          <li>
            <strong>Create a project</strong>
            <span>Spin up a dedicated or shared database instance in seconds.</span>
          </li>
          <li>
            <strong>Connect instantly</strong>
            <span>Postgres wire protocol, REST API, and Auth &mdash; all ready from the start.</span>
          </li>
          <li>
            <strong>Ship with confidence</strong>
            <span>Row-level security, real health signals, and agent-native MCP tooling included.</span>
          </li>
        </ol>
      </section>

      <section className="lb-band" id="features">
        <h2>Built for what matters</h2>
        <ul className="lb-benefits">
          <li>
            <strong>Tiny footprint</strong>
            <span>Runs on a 256 MB container. No bloated runtimes.</span>
          </li>
          <li>
            <strong>Provable security</strong>
            <span>Row-level security and Auth baked in, verified by formal contracts.</span>
          </li>
          <li>
            <strong>Agent-native APIs</strong>
            <span>MCP server, REST, and Realtime designed for autonomous workflows.</span>
          </li>
          <li>
            <strong>Web console</strong>
            <span>Manage projects, run SQL, and monitor health from one dashboard.</span>
          </li>
        </ul>
      </section>

      <section className="lb-band" id="matrix">
        <h2>Open development</h2>
        <p>
          Every feature ships with a capability matrix. Nothing shows green until tests pass.
          Track progress in real time.
        </p>
        <a className="lb-btn lb-btn-ghost" href="https://github.com/librebase-official/librebase/blob/main/docs/lidb-capability-matrix.md">
          View progress on GitHub
        </a>
      </section>

      <section className="lb-band lb-faq" id="faq">
        <h2>FAQ</h2>
        <details>
          <summary>Is Librebase a full Supabase replacement?</summary>
          <p>Not yet. We&rsquo;re shipping the core vertical first &mdash; SQL, REST, Auth, and RLS &mdash; with more coming fast.</p>
        </details>
        <details>
          <summary>What language is it written in?</summary>
          <p>Li &mdash; a systems language that compiles to native code with formal verification, zero GC pauses, and minimal memory use.</p>
        </details>
        <details>
          <summary>Can I self-host?</summary>
          <p>Yes. Run locally with a single binary, or deploy on your own infrastructure with Docker.</p>
        </details>
        <details>
          <summary>What about agents?</summary>
          <p>Librebase includes an MCP server so your AI agents can query, manage projects, and check health programmatically.</p>
        </details>
      </section>

      <section className="lb-final">
        <h2>Your stack should be as fast as your agents.</h2>
        <p>Join the waitlist for early access, or explore Studio right now.</p>
        <div className="lb-cta-row">
          <a className="lb-btn lb-btn-primary lb-btn-lg" href="#waitlist">
            Join waitlist
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
          <Link href="/admin">Admin</Link>
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
      setMessage("You are on the list. We will email when early access opens.");
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
          {status === "loading" ? "Joining…" : "Join waitlist"}
        </button>
      </div>
      {message ? (
        <p className={`lb-waitlist-msg${status === "err" ? " is-err" : ""}`}>{message}</p>
      ) : null}
    </form>
  );
}
