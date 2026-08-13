"use client";

import {
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from "react";

/* ---------- tiny motion helpers (no deps) ---------- */

function useInView<T extends HTMLElement>(threshold = 0.2) {
  const ref = useRef<T | null>(null);
  const [inView, setInView] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) {
            setInView(true);
            io.disconnect();
          }
        }
      },
      { threshold },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [threshold]);
  return { ref, inView };
}

function Reveal({
  children,
  className = "",
  delay = 0,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
}) {
  const { ref, inView } = useInView<HTMLDivElement>(0.15);
  return (
    <div
      ref={ref}
      className={`lb-cin-reveal${inView ? " is-in" : ""} ${className}`}
      style={delay ? { transitionDelay: `${delay}ms` } : undefined}
    >
      {children}
    </div>
  );
}

function CountUp({
  to,
  duration = 1800,
  suffix = "",
}: {
  to: number;
  duration?: number;
  suffix?: string;
}) {
  const { ref, inView } = useInView<HTMLSpanElement>(0.4);
  const [val, setVal] = useState(0);
  useEffect(() => {
    if (!inView) return;
    let raf = 0;
    const t0 = performance.now();
    const tick = (t: number) => {
      const p = Math.min(1, (t - t0) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      setVal(Math.round(to * eased));
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [inView, to, duration]);
  return (
    <span ref={ref}>
      {val.toLocaleString("en-US")}
      {suffix}
    </span>
  );
}

/* ---------- benchmark comparison rows ---------- */

const ROWS = [
  { label: "Vector search · 100% recall", os: "499 QPS", lb: "4,683 QPS", fill: 0.11 },
  { label: "Idle memory", os: "~1.85 GB", lb: "~2 MB", fill: 1 },
  { label: "Containers", os: "12", lb: "1", fill: 1 },
  { label: "Auth login", os: "196 ms", lb: "52 ms", fill: 1 },
  { label: "Storage upload", os: "24 ms", lb: "2.8 ms", fill: 1 },
];

/* ---------- component ---------- */

export function CinematicHero() {
  return (
    <>
      <section className="lb-cin-hero">
        <div className="lb-cin-orbs" aria-hidden="true">
          <span className="lb-cin-orb lb-cin-orb-a" />
          <span className="lb-cin-orb lb-cin-orb-b" />
        </div>

        <Reveal className="lb-cin-kicker">Benchmark · same machine · same tests</Reveal>
        <Reveal className="lb-cin-wordmark" delay={80}>
          Libre<span className="lb-cin-base">base</span>
        </Reveal>
        <Reveal className="lb-cin-title" delay={160}>
          Tiny. Fast. <span className="lb-cin-em">Honest.</span>
        </Reveal>
        <Reveal className="lb-cin-sub" delay={240}>
          A high-performance backend as a service for AI — a lean native engine that
          out-benchmarks the open stack on footprint, speed, and vector search.
        </Reveal>

        <Reveal className="lb-cin-cta" delay={320}>
          <a className="lb-btn lb-btn-primary lb-btn-lg" href="#waitlist">
            Join the waitlist
          </a>
          <a className="lb-btn lb-btn-ghost lb-btn-lg" href="#bench">
            See the numbers
          </a>
        </Reveal>

        <Reveal className="lb-cin-herostat" delay={420}>
          <span className="lb-cin-herostat-label">Vector search · 100% recall</span>
          <span className="lb-cin-herostat-value">
            <CountUp to={4683} /> <span className="lb-cin-unit">QPS</span>
          </span>
          <span className="lb-cin-herostat-sub">
            Librebase HNSW — <strong>9.4×</strong> the open stack at equal accuracy
          </span>
        </Reveal>
      </section>

      <section className="lb-cin-bench" id="bench">
        <Reveal className="lb-cin-kicker">Benchmark</Reveal>
        <Reveal className="lb-cin-bench-title" delay={60}>
          Measured against the open stack
        </Reveal>
        <Reveal className="lb-cin-bench-sub" delay={120}>
          Same machine. Same workload. One table. Every number below is measured.
        </Reveal>

        <div className="lb-cin-rows">
          {ROWS.map((r, i) => (
            <Reveal key={r.label} className="lb-cin-row" delay={i * 70}>
              <span className="lb-cin-row-label">{r.label}</span>
              <span className="lb-cin-bar">
                <span
                  className="lb-cin-fill lb-cin-fill-os"
                  style={{ "--fill": r.fill } as CSSProperties}
                />
              </span>
              <span className="lb-cin-val">{r.os}</span>
              <span className="lb-cin-val lb-cin-val-lb">{r.lb}</span>
            </Reveal>
          ))}
        </div>
      </section>
    </>
  );
}
