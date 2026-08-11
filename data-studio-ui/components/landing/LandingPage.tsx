"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

/** Primary conversion goal: waitlist email for early access. */
const PRIMARY_CTA = "Join the waitlist for early access";

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
          <Link className="lb-link-quiet" href="/blog">
            Blog
          </Link>
          <a className="lb-link-quiet" href="#faq">
            Questions
          </a>
          <a className="lb-btn lb-btn-primary" href="#waitlist">
            {PRIMARY_CTA}
          </a>
        </div>
      </header>

      <section className="lb-hero" aria-label="Hero">
        <div className="lb-hero-copy">
          <p className="lb-brand-signal">Librebase</p>
          <h1 className="lb-hero-title">A PostgreSQL platform that stays small and honest.</h1>
          <p className="lb-hero-sub">
            Sign-in by default. Usual database connection, web interfaces, and live updates. Built
            for apps and for AI tools that query your data.
          </p>
          <div className="lb-cta-row">
            <a className="lb-btn lb-btn-primary lb-btn-lg" href="#waitlist">
              {PRIMARY_CTA}
            </a>
            <Link className="lb-btn lb-btn-ghost lb-btn-lg" href="/projects">
              Open the console
            </Link>
          </div>
        </div>
        <div className="lb-hero-visual" aria-hidden="true">
          <ProductMesh />
        </div>
      </section>

      <section className="lb-proof" aria-label="Proof">
        <p>
          The engine is written in Li and compiles to machine code. A lean instance measures
          about 3.8&nbsp;MB of RAM resident, and indexed lookups and range scans benchmark at or
          better than Postgres on our published OLTP comparison. The console shows real health.
        </p>
      </section>

      <section className="lb-band lb-reveal" id="promise">
        <h2>Apps and agents need a database that keeps up.</h2>
        <p>
          Short sessions, many requests, sign-in on every call. Librebase is PostgreSQL-compatible
          and built for that load.
        </p>
      </section>

      <section className="lb-band" id="how">
        <h2>How it works</h2>
        <ol className="lb-steps">
          <li>
            <strong>Create a project</strong>
            <span>One server per project, or several projects on one machine.</span>
          </li>
          <li>
            <strong>Connect</strong>
            <span>PostgreSQL connection string, web interfaces, and sign-in from the first start.</span>
          </li>
          <li>
            <strong>Operate</strong>
            <span>Row-level access rules, SQL in the console, safe hooks for AI tools.</span>
          </li>
        </ol>
      </section>

      <section className="lb-band" id="features">
        <h2>What you get</h2>
        <ul className="lb-benefits">
          <li>
            <strong>Small footprint</strong>
            <span>Lean native runtime so you can pack more projects on one host.</span>
          </li>
          <li>
            <strong>Fast queries</strong>
            <span>Target: match managed Postgres speed on everyday reads and writes.</span>
          </li>
          <li>
            <strong>Sign-in and row rules</strong>
            <span>Included when the project starts.</span>
          </li>
          <li>
            <strong>AI tool access</strong>
            <span>Standard tool hooks so assistants can query and manage without a human in the loop.</span>
          </li>
          <li>
            <strong>One console</strong>
            <span>Projects, SQL, and status in one place.</span>
          </li>
        </ul>
        <div className="lb-cta-row lb-mid-cta">
          <a className="lb-btn lb-btn-primary" href="#waitlist">
            {PRIMARY_CTA}
          </a>
        </div>
      </section>

      <section className="lb-band" id="matrix">
        <h2>Done means tests pass</h2>
        <p>Incomplete work stays marked incomplete. See what works today.</p>
        <a
          className="lb-btn lb-btn-ghost"
          href="https://github.com/librebase-official/librebase/blob/main/docs/lidb-capability-matrix.md"
        >
          What works today
        </a>
      </section>

      <section className="lb-band lb-faq" id="faq">
        <h2>Common questions</h2>
        <details>
          <summary>How much memory are you targeting?</summary>
          <p>
            A lean instance measures about 3.8&nbsp;MB of RAM resident on Linux
            (published CI), and we hold the product target at 64&nbsp;MB for a
            comfortable dedicated host. Supabase-class / Postgres-class speed on
            the same hardware, from our published OLTP comparison&mdash;indexed
            lookups and range scans measured at or better than Postgres on our
            indexed path, with an honest caveat that the index is an in-memory
            ordered secondary, not a Postgres disk B-tree.
          </p>
        </details>
        <details>
          <summary>Is this a full replacement for Supabase?</summary>
          <p>
            Not yet. Core first: queries, web interfaces, sign-in, and per-row access rules. File
            storage and edge functions come after those pass tests.
          </p>
        </details>
        <details>
          <summary>What is Li?</summary>
          <p>
            A systems language that compiles to machine code. Librebase&rsquo;s database engine and
            process supervisor are written in Li.
          </p>
        </details>
        <details>
          <summary>Can I run it myself?</summary>
          <p>
            Yes. Local install or Docker. The waitlist is for hosted cloud instances we run for you.
          </p>
        </details>
        <details>
          <summary>How do AI tools connect?</summary>
          <p>
            Through standard assistant tool hooks for projects, health, and queries, plus web
            interfaces for app clients.
          </p>
        </details>
        <details>
          <summary>Dedicated vs shared?</summary>
          <p>
            Dedicated: one server, one project. Shared: several projects on one server, cheaper for
            staging.
          </p>
        </details>
        <details>
          <summary>What does early access include?</summary>
          <p>
            Email when cloud and dedicated servers open, plus the console on this site today.
          </p>
        </details>
      </section>

      <section className="lb-band" id="waitlist">
        <h2>{PRIMARY_CTA}</h2>
        <p>
          We email you when hosted cloud and private servers open. The console on this site works
          now.
        </p>
        <WaitlistForm />
      </section>

      <section className="lb-final">
        <h2>Get on the list</h2>
        <p>PostgreSQL for teams and AI tools. Small footprint. Honest status.</p>
        <div className="lb-cta-row">
          <a className="lb-btn lb-btn-primary lb-btn-lg" href="#waitlist">
            {PRIMARY_CTA}
          </a>
          <Link className="lb-btn lb-btn-ghost lb-btn-lg" href="/projects">
            Open the console
          </Link>
        </div>
      </section>

      <footer className="lb-footer">
        <span className="lb-wordmark">
          Libre<span>base</span>
        </span>
        <div className="lb-footer-links">
          <Link href="/blog">Blog</Link>
          <Link href="/projects">Console</Link>
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
          {status === "loading" ? "Joining…" : PRIMARY_CTA}
        </button>
      </div>
      {message ? (
        <p className={`lb-waitlist-msg${status === "err" ? " is-err" : ""}`}>{message}</p>
      ) : null}
    </form>
  );
}
