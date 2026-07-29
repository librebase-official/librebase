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
          <Link className="lb-btn lb-btn-primary" href="/projects">
            Open Studio
          </Link>
        </div>
      </header>

      <section className="lb-hero" aria-label="Hero">
        <div className="lb-hero-copy">
          <p className="lb-brand-signal">Librebase</p>
          <h1 className="lb-hero-title">Postgres platform. Honest status.</h1>
          <p className="lb-hero-sub">
            Supabase-shaped open data on lidb: Auth, REST, Realtime, and Studio for teams who need
            real health signals.
          </p>
          <div className="lb-cta-row">
            <Link className="lb-btn lb-btn-primary lb-btn-lg" href="/projects">
              Open Studio
            </Link>
            <a className="lb-btn lb-btn-ghost lb-btn-lg" href="#how">
              See how it runs
            </a>
          </div>
          <p className="lb-reassure">Dev stub stays labeled. Production path needs lidb + lis.</p>
        </div>
        <div className="lb-hero-visual" aria-hidden="true">
          <ProductMesh />
        </div>
      </section>

      <section className="lb-proof" aria-label="Proof">
        <p>
          Built on linative <strong>lidb</strong> + <strong>lis</strong>. Wave A parity is measured by
          executable contracts, not emoji counts.
        </p>
      </section>

      <section className="lb-band lb-reveal" id="promise">
        <h2>Stop guessing if the stack is up.</h2>
        <p>
          Librebase keeps degraded modes honest. Ports can listen while the engine is a stub. Studio
          says so. Agents can verify with the parity harness.
        </p>
      </section>

      <section className="lb-band" id="how">
        <h2>How it works</h2>
        <ol className="lb-steps">
          <li>
            <strong>Org and instance</strong>
            <span>Create a project on a dedicated or shared runtime.</span>
          </li>
          <li>
            <strong>lis profile librebase</strong>
            <span>Start Auth, registry, and /rest/v1 against lidb.</span>
          </li>
          <li>
            <strong>Prove with Wave A</strong>
            <span>Run SQL, REST, Auth, and RLS contracts before you claim parity.</span>
          </li>
        </ol>
      </section>

      <section className="lb-band" id="features">
        <h2>What you get</h2>
        <ul className="lb-benefits">
          <li>
            <strong>Studio console</strong>
            <span>Projects, instances, SQL, and admin setup in one place.</span>
          </li>
          <li>
            <strong>HTTP contracts</strong>
            <span>/rest/v1 and /v1/auth shaped for Supabase-style clients.</span>
          </li>
          <li>
            <strong>Agent control</strong>
            <span>MCP tools for health, projects, and parity_run.</span>
          </li>
          <li>
            <strong>Honest matrix</strong>
            <span>Capability rows flip to usable only when tests pass.</span>
          </li>
        </ul>
      </section>

      <section className="lb-band" id="matrix">
        <h2>Capability matrix</h2>
        <p>
          Track lidb, lis, Storage, Edge, and SDK status in-repo. Core vertical first: SQL, REST,
          Auth, RLS.
        </p>
        <a className="lb-btn lb-btn-ghost" href="https://github.com/librebase-official/librebase/blob/main/docs/lidb-capability-matrix.md">
          View matrix on GitHub
        </a>
      </section>

      <section className="lb-band lb-faq" id="faq">
        <h2>FAQ</h2>
        <details>
          <summary>Is this full Supabase parity today?</summary>
          <p>No. Wave A harness defines the contracts. Matrix rows stay in progress until tests are green.</p>
        </details>
        <details>
          <summary>Do I need lidb installed?</summary>
          <p>
            Local Studio can use LIDB_RUNTIME_MODE=dev for a labeled stub. Production local path uses
            LIDB_ROOT and lis on PATH.
          </p>
        </details>
        <details>
          <summary>Dedicated vs shared instances?</summary>
          <p>Both. Dedicated is one instance per project. Shared puts many projects on one runtime.</p>
        </details>
        <details>
          <summary>What is the primary CTA?</summary>
          <p>Open Studio. That lands you in the org project console.</p>
        </details>
      </section>

      <section className="lb-final">
        <h2>Start with a real console.</h2>
        <p>Spin a project, watch health tell the truth, then wire lidb when you are ready.</p>
        <Link className="lb-btn lb-btn-primary lb-btn-lg" href="/projects">
          Open Studio
        </Link>
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
