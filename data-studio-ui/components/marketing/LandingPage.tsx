"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

function useReveal() {
  const ref = useRef<HTMLDivElement>(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      ([e]) => {
        if (e.isIntersecting) setInView(true);
      },
      { threshold: 0.12 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);
  return { ref, inView };
}

export function LandingPage() {
  const [ready, setReady] = useState(false);
  const bench = useReveal();

  useEffect(() => {
    const t = requestAnimationFrame(() => setReady(true));
    return () => cancelAnimationFrame(t);
  }, []);

  const heroIn = ready;

  return (
    <div className={`lb-landing${ready ? " is-ready" : ""}`}>
      <header className="lb-nav">
        <Link href="/landing" className="lb-wordmark" style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <Image src="/brand/librebase-mark.svg" alt="" width={28} height={28} priority />
          Libre<span>base</span>
        </Link>
        <div className="lb-nav-actions">
          <Link className="lb-link-quiet" href="/for-agents">For agents</Link>
          <Link className="lb-link-quiet" href="/design">Design</Link>
          <Link className="lb-btn lb-btn-ghost" href="/login">Sign in</Link>
          <Link className="lb-btn lb-btn-primary" href="/setup">Get started</Link>
        </div>
      </header>

      <section className="lb-cin-hero">
        <div className="lb-cin-orbs" aria-hidden="true">
          <div className="lb-cin-orb lb-cin-orb-a" />
          <div className="lb-cin-orb lb-cin-orb-b" />
        </div>
        <div className={`lb-cin-reveal lb-brand-signal${heroIn ? " is-in" : ""}`}>
          Postgres-compatible · agent-first
        </div>
        <h1 className={`lb-cin-reveal lb-cin-wordmark${heroIn ? " is-in" : ""}`} style={{ transitionDelay: "80ms" }}>
          Libre<span className="lb-cin-base">base</span>
        </h1>
        <p className={`lb-cin-reveal lb-cin-title${heroIn ? " is-in" : ""}`} style={{ transitionDelay: "140ms" }}>
          Honest data for <span className="lb-cin-em">builders &amp; agents</span>
        </p>
        <p className={`lb-cin-reveal lb-cin-sub${heroIn ? " is-in" : ""}`} style={{ transitionDelay: "200ms" }}>
          A small-footprint Postgres layer with real health status, MCP tools, and REST — no fake-green dashboards.
        </p>
        <div className={`lb-cin-reveal lb-cin-cta${heroIn ? " is-in" : ""}`} style={{ transitionDelay: "260ms" }}>
          <Link className="lb-btn lb-btn-primary lb-btn-lg" href="/setup">Create organization</Link>
          <Link className="lb-btn lb-btn-ghost lb-btn-lg" href="/for-agents">Connect via MCP</Link>
        </div>
        <div className={`lb-cin-reveal lb-cin-herostat${heroIn ? " is-in" : ""}`} style={{ transitionDelay: "340ms" }}>
          <p className="lb-cin-herostat-label">Designed footprint</p>
          <p className="lb-cin-herostat-value">
            &lt;64<span className="lb-cin-unit">MB</span>
          </p>
          <p className="lb-cin-herostat-sub">
            <strong>Li-native</strong> runtime · Auth, REST, Realtime included
          </p>
        </div>
      </section>

      <section className="lb-cin-bench" ref={bench.ref}>
        <h2 className={`lb-cin-reveal lb-cin-bench-title${bench.inView ? " is-in" : ""}`}>
          Built for teams who read the metrics
        </h2>
        <p className={`lb-cin-reveal lb-cin-bench-sub${bench.inView ? " is-in" : ""}`} style={{ transitionDelay: "80ms" }}>
          Librebase surfaces what is actually running — instances, migrations, sealed secrets — so operators and agents share the same truth.
        </p>
        <div className="lb-cin-rows">
          {[
            { name: "Studio console", note: "Projects, SQL, auth providers", href: "/login" },
            { name: "MCP for agents", note: "Browser auth, KMS-sealed secrets", href: "/for-agents" },
            { name: "Open stack", note: "Postgres-compatible, self-hostable", href: "https://github.com/librebase-official/librebase" },
          ].map((row, i) => (
            <Link
              key={row.name}
              href={row.href}
              className={`lb-cin-reveal lb-cin-row${bench.inView ? " is-in" : ""}`}
              style={{ transitionDelay: `${120 + i * 80}ms` }}
            >
              <span className="lb-cin-row-label">{row.name}</span>
              <span className="lb-cin-val">{row.note}</span>
              <span className="lb-cin-val-lb">→</span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
