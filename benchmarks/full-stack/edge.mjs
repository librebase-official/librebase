#!/usr/bin/env node
/**
 * Edge function invoke benchmark — Librebase (lis /functions/v1, li-edge runtime).
 *
 * Measures POST /functions/v1/{name} latency. Honest note: li-edge invoke.py is a
 * lean subprocess runtime, NOT Deno/WASM — no claim of Supabase Edge parity.
 *
 * LIS_API=http://127.0.0.1:54321   FN=hello   RUNS=60
 */
import { performance } from "node:perf_hooks";

const API = (process.env.LIS_API ?? "http://127.0.0.1:54321").replace(/\/$/, "");
const FN = process.env.FN ?? "hello";
const RUNS = Number(process.env.RUNS ?? 60);

const stats = (a) => {
  if (!a.length) return { n: 0, min: 0, p50: 0, p95: 0, max: 0 };
  const s = [...a].sort((x, y) => x - y);
  const p = (q) => s[Math.min(s.length - 1, Math.floor(q * s.length))];
  return { n: s.length, min: +s[0].toFixed(2), p50: +p(0.5).toFixed(2), p95: +p(0.95).toFixed(2), max: +s[s.length - 1].toFixed(2) };
};

async function main() {
  const lat = [];
  for (let i = 0; i < RUNS; i++) {
    const t = performance.now();
    const res = await fetch(`${API}/functions/v1/${FN}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ping: true }),
    });
    await res.json();
    if (!res.ok) throw new Error(`invoke ${FN} status=${res.status}`);
    lat.push(performance.now() - t);
  }
  console.log(
    JSON.stringify(
      {
        benchmark: `lis edge function invoke — ${FN} (li-edge runtime)`,
        stack: "librebase-lis-edge",
        date: new Date().toISOString().slice(0, 10),
        fn: FN,
        runs: RUNS,
        invoke_ms: stats(lat),
        honesty:
          "li-edge invoke.py subprocess runtime — not Deno/WASM, not Supabase Edge parity. Warm sequential loop.",
      },
      null,
      2,
    ),
  );
}

main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
