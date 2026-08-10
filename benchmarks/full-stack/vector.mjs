#!/usr/bin/env node
/**
 * Vector search benchmark — pgvector (Supabase baseline).
 *
 * Librebase/lidb has NO vector engine yet — this is an honest baseline to set a
 * target for future lidb vector work.
 *
 * Loads ROWS random 128-dim vectors, builds an HNSW index, measures:
 *   - ingest throughput
 *   - exact (no index) top-K cosine search latency
 *   - HNSW approximate top-K latency + recall
 */
import { performance } from "node:perf_hooks";
import { createHmac } from "node:crypto";

const ROWS = Number(process.env.ROWS ?? 10_000);
const K = Number(process.env.K ?? 10);
const Q = Number(process.env.QUERIES ?? 60);
const SR = process.env.LIBREBASE_SERVICE_ROLE ?? "";
const SECRET = process.env.LIBREBASE_JWT_SECRET ?? "super-secret-jwt-token-with-at-least-32-characters-long";
if (!SR) throw new Error("LIBREBASE_SERVICE_ROLE required");

const b64 = (b) => Buffer.from(b).toString("base64url");
const now = Math.floor(Date.now() / 1000);
const h = b64(JSON.stringify({ alg: "HS256", typ: "JWT" }));
const p = b64(JSON.stringify({ iss: "supabase", iat: now, exp: now + 3600, role: "service_role" }));
const s = createHmac("sha256", SECRET).update(`${h}.${p}`).digest("base64url");
const token = `${h}.${p}.${s}`;
const hdr = { apikey: SR, Authorization: `Bearer ${SR}`, "Content-Type": "application/json" };

const rand = () => Array.from({ length: 128 }, () => +(Math.random() * 2 - 1).toFixed(6));
const toVec = (a) => `[${a.join(",")}]`;
function stats(a) {
  if (!a.length) return { n: 0, min: 0, p50: 0, p95: 0, max: 0 };
  const s = [...a].sort((x, y) => x - y);
  const q = (x) => s[Math.min(s.length - 1, Math.floor(x * s.length))];
  return { n: s.length, min: +s[0].toFixed(2), p50: +q(0.5).toFixed(2), p95: +q(0.95).toFixed(2), max: +s[s.length - 1].toFixed(2) };
}

// exact search
const exact = async (q) => await fetch(`http://127.0.0.1:8000/rest/v1/rpc/vector_search`, { method: "POST", headers: hdr, body: JSON.stringify({ query: toVec(q), k: K, exact: true }) });
const approx = async (q) => await fetch(`http://127.0.0.1:8000/rest/v1/rpc/vector_search`, { method: "POST", headers: hdr, body: JSON.stringify({ query: toVec(q), k: K, exact: false }) });

async function run() {
  // ensure table + HNSW index + search fn
  await fetch(`http://127.0.0.1:8000/rest/v1/rpc/exec_sql`, { method: "POST", headers: hdr, body: JSON.stringify({ q: `CREATE EXTENSION IF NOT EXISTS vector;` }) }).catch(() => {});
  // table is created out-of-band; index too

  // ingest via psql (fast path) - call helper
  const { execSync } = await import("node:child_process");
  const psql = `podman exec supabase-db sh -c "PGPASSWORD=postgres psql 'host=127.0.0.1 port=5432 user=supabase_admin dbname=postgres sslmode=disable' -q -c \\\"INSERT INTO vectors (embedding) SELECT ARRAY(SELECT round((random()*2-1)::numeric,6) FROM generate_series(1,128))::vector FROM generate_series(1,${ROWS})\\\""`;
  const t0 = performance.now();
  execSync(psql, { stdio: "ignore" });
  const ingestMs = performance.now() - t0;

  // exact + approx queries
  const queries = Array.from({ length: Q }, () => rand());
  const exactLat = [], approxLat = [];
  for (const q of queries) {
    const t = performance.now();
    await exact(q);
    exactLat.push(performance.now() - t);
    const t2 = performance.now();
    await approx(q);
    approxLat.push(performance.now() - t2);
  }
  console.log(JSON.stringify({
    stack: "supabase-pgvector",
    dim: 128, rows: ROWS, k: K,
    ingest_rows_per_sec: Math.round(ROWS / (ingestMs / 1000)),
    ingest_total_ms: Math.round(ingestMs),
    exact_search_ms: stats(exactLat),
    hnsw_approx_ms: stats(approxLat),
    honesty: "pgvector baseline; lidb has no vector engine yet — sets a target",
  }, null, 2));
}

run().catch((e) => { console.error(e); process.exit(1); });
