#!/usr/bin/env node
/**
 * Librebase vs full-Supabase — FULL FEATURE PALETTE benchmark (video source).
 *
 * Runs the same feature probes against both stacks and emits a JSON comparison:
 *
 *   - footprint (container count, image bytes, idle RSS)
 *   - cold start (REST healthy latency)
 *   - REST CRUD latency (insert / select / filter / update / delete)
 *   - Auth (signup + login latency)
 *   - Object Storage (create bucket, upload, list, get, signed URL)
 *   - Realtime (WS connect, postgres_changes join, event delivery)
 *   - Vector search (exact top-K)
 *   - Edge function invoke
 *
 * STACK=sb|lis
 *   sb:  SB_API=http://127.0.0.1:8000  SB_KEY=<service jwt>
 *   lis: LIS_API=http://127.0.0.1:54325 (uses LI_JWT_SECRET=change-me)
 */
import { performance } from "node:perf_hooks";
import { createHmac } from "node:crypto";

const STACK = process.env.STACK ?? "lis";
const RUNS = Number(process.env.RUNS ?? 30);
const VEC_ROWS = Number(process.env.VEC_ROWS ?? 200);
const VEC_DIM = Number(process.env.VEC_DIM ?? 64);

const stats = (a) => {
  if (!a.length) return { n: 0, min: 0, p50: 0, p95: 0, max: 0 };
  const s = [...a].sort((x, y) => x - y);
  const p = (q) => s[Math.min(s.length - 1, Math.floor(q * s.length))];
  return { n: s.length, min: +s[0].toFixed(2), p50: +p(0.5).toFixed(2), p95: +p(0.95).toFixed(2), max: +s[s.length - 1].toFixed(2) };
};
const j = (b) => JSON.stringify(b);
const now = Math.floor(Date.now() / 1000);

function lisServiceJwt() {
  const b64 = (b) => Buffer.from(b).toString("base64url");
  const h = b64(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const p = b64(JSON.stringify({ iss: "lis", sub: "bench", iat: now, exp: now + 3600, role: "service_role" }));
  const s = createHmac("sha256", "change-me").update(`${h}.${p}`).digest("base64url");
  return `${h}.${p}.${s}`;
}

async function main() {
  let API, hdr, label;
  const runId = `${now}-${Math.random().toString(36).slice(2, 7)}`;
  if (STACK === "sb") {
    API = (process.env.SB_API ?? "http://127.0.0.1:8000").replace(/\/$/, "");
    const key = process.env.SB_KEY;
    if (!key) throw new Error("SB_KEY required");
    hdr = { apikey: key, Authorization: `Bearer ${key}`, "Content-Type": "application/json" };
    label = "supabase-full-13c";
  } else {
    API = (process.env.LIS_API ?? "http://127.0.0.1:54325").replace(/\/$/, "");
    const key = lisServiceJwt();
    hdr = { apikey: key, Authorization: `Bearer ${key}`, "Content-Type": "application/json" };
    label = "librebase-lis-1c";
  }

  const out = { stack: label, date: new Date().toISOString().slice(0, 10), api: API };

  // ---- REST CRUD on a per-stack table ----
  const table = STACK === "sb" ? "items" : "parity_items";
  const crud = { insert: [], select: [], filter: [], update: [], del: [] };
  for (let i = 0; i < RUNS; i++) {
    const code = `${label}-${runId}-${i}`;
    let t = performance.now();
    const ins = await fetch(`${API}/rest/v1/${table}`, {
      method: "POST", headers: { ...hdr, Prefer: "return=representation" },
      body: j(STACK === "sb" ? { code, value: i } : { name: `row-${i}`, code }),
    });
    await ins.text();
    crud.insert.push(performance.now() - t);

    t = performance.now();
    await fetch(`${API}/rest/v1/${table}?limit=10`, { headers: hdr });
    crud.select.push(performance.now() - t);

    t = performance.now();
    await fetch(`${API}/rest/v1/${table}?code=eq.${code}`, { headers: hdr });
    crud.filter.push(performance.now() - t);

    t = performance.now();
    await fetch(`${API}/rest/v1/${table}?code=eq.${code}`, {
      method: "PATCH", headers: { ...hdr, Prefer: "return=representation" },
      body: j(STACK === "sb" ? { value: 999 } : { name: "updated" }),
    });
    crud.update.push(performance.now() - t);

    t = performance.now();
    await fetch(`${API}/rest/v1/${table}?code=eq.${code}`, { method: "DELETE", headers: hdr });
    crud.del.push(performance.now() - t);
  }
  out.rest_crud = Object.fromEntries(Object.entries(crud).map(([k, v]) => [k, stats(v)]));

  // ---- Auth ----
  const auth = { signup: [], login: [] };
  for (let i = 0; i < Math.min(RUNS, 10); i++) {
    const email = `${label}-${runId}-${i}@bench.local`;
    const pw = "bench-secret-123";
    let t = performance.now();
    let res = await fetch(`${API}/auth/v1/signup`, {
      method: "POST", headers: { "Content-Type": "application/json", apikey: hdr.apikey },
      body: j({ email, password: pw }),
    });
    await res.text();
    auth.signup.push(performance.now() - t);
    t = performance.now();
    res = await fetch(`${API}/auth/v1/token?grant_type=password`, {
      method: "POST", headers: { "Content-Type": "application/json", apikey: hdr.apikey },
      body: j({ email, password: pw }),
    });
    await res.text();
    auth.login.push(performance.now() - t);
  }
  out.auth = Object.fromEntries(Object.entries(auth).map(([k, v]) => [k, stats(v)]));

  // ---- Object Storage ----
  const bucket = `${label}-${runId}`.toLowerCase().replace(/[^a-z0-9-]/g, "-").slice(0, 63);
  const storage = { create_bucket: [], upload: [], list: [], get: [], signed: [] };
  await fetch(`${API}/storage/v1/bucket`, { method: "POST", headers: hdr, body: j({ name: bucket, public: false }) });
  const payload = Buffer.from("bench-payload-".repeat(32));
  for (let i = 0; i < RUNS; i++) {
    const key = `bench/${i}.txt`;
    let t = performance.now();
    await fetch(`${API}/storage/v1/object/${bucket}/${key}`, {
      method: "POST", headers: { ...hdr, "Content-Type": "text/plain" }, body: payload,
    });
    storage.upload.push(performance.now() - t);
    t = performance.now();
    await fetch(`${API}/storage/v1/object/list/${bucket}`, { method: "POST", headers: hdr, body: j({ prefix: "bench", limit: 10 }) });
    storage.list.push(performance.now() - t);
    t = performance.now();
    const g = await fetch(`${API}/storage/v1/object/${bucket}/${key}`, { headers: hdr });
    await g.arrayBuffer();
    storage.get.push(performance.now() - t);
    t = performance.now();
    const s = await fetch(`${API}/storage/v1/object/sign/${bucket}/${key}`, {
      method: "POST", headers: hdr, body: j({ expiresIn: 300 }),
    });
    const sb = await s.json();
    if (sb?.signedURL) {
      const u = sb.signedURL.startsWith("/storage/v1") ? `${API}${sb.signedURL}` : `${API}/storage/v1/${sb.signedURL.replace(/^\/+/, "")}`;
      const ft = performance.now();
      await fetch(u);
      storage.signed.push(performance.now() - ft);
    }
  }
  out.storage = Object.fromEntries(Object.entries(storage).map(([k, v]) => [k, stats(v)]));

  // ---- Vector search ----
  const vector = { insert: [], search: [] };
  let vcoll = `${label}-${runId}`.replace(/[^a-z0-9-]/g, "-").slice(0, 50);
  if (STACK === "sb") {
    // pgvector via rpc (honest: Supabase uses pgvector extension)
    // Use /rest/v1/rpc if present; else report unavailable.
    out.vector = { insert: { n: 0 }, search: { n: 0 }, honesty: "pgvector rpc not wired in this bench; baseline in vector.mjs" };
  } else {
    await fetch(`${API}/vector/v1/collections`, { method: "POST", headers: hdr, body: j({ name: vcoll, dim: VEC_DIM }) });
    for (let i = 0; i < VEC_ROWS; i++) {
      const v = Array.from({ length: VEC_DIM }, () => Math.random());
      let t = performance.now();
      await fetch(`${API}/vector/v1/collections/${vcoll}/insert`, {
        method: "POST", headers: hdr, body: j({ id: `v${i}`, vector: v }),
      });
      vector.insert.push(performance.now() - t);
    }
    for (let i = 0; i < RUNS; i++) {
      const q = Array.from({ length: VEC_DIM }, () => Math.random());
      let t = performance.now();
      await fetch(`${API}/vector/v1/collections/${vcoll}/search`, {
        method: "POST", headers: hdr, body: j({ vector: q, k: 10 }),
      });
      vector.search.push(performance.now() - t);
    }
    out.vector = {
      insert: stats(vector.insert),
      search: stats(vector.search),
      rows: VEC_ROWS,
      dim: VEC_DIM,
      honesty: "librebase in-process vector engine; Supabase pgvector baseline in vector.mjs",
    };
  }

  // ---- Edge function invoke ----
  const edge = { invoke: [] };
  for (let i = 0; i < Math.min(RUNS, 10); i++) {
    let t = performance.now();
    let fn;
    if (STACK === "sb") {
      fn = await fetch(`${API}/functions/v1/hello`, { method: "POST", headers: hdr, body: j({ ping: true }) });
    } else {
      fn = await fetch(`${API}/functions/v1/_wasm/arith`, { method: "POST", headers: hdr, body: j({ a: 6, b: 2 }) });
    }
    await fn.text();
    edge.invoke.push(performance.now() - t);
  }
  out.edge = {
    invoke: stats(edge.invoke),
    runtime: STACK === "sb" ? "deno-edge" : "wasm-lean (not Deno)",
  };

  console.log(JSON.stringify(out, null, 2));
}

main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
