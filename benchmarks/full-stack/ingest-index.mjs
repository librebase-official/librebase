#!/usr/bin/env node
/**
 * Bulk ingest + large-index benchmark — Supabase (Postgres B-tree via PostgREST)
 * vs Librebase (lidb sorted_tree via engine exec).
 *
 * Loads ROWS into an indexed `items` table, measures ingest + indexed queries.
 *
 * STACK=sb|lidb   LIBREBASE_API (PostgREST) + SERVICE_ROLE for sb;
 *                 LIDB_EMBED + data dir for lidb.
 */
import { performance } from "node:perf_hooks";
import { createHmac } from "node:crypto";
import { spawn, spawnSync } from "node:child_process";
import { mkdirSync } from "node:fs";

const STACK = process.env.STACK ?? "sb";
const ROWS = Number(process.env.ROWS ?? 100_000);
const Q = Number(process.env.QUERIES ?? 60);

const stats = (a) => {
  if (!a.length) return { n: 0, min: 0, p50: 0, p95: 0, max: 0 };
  const s = [...a].sort((x, y) => x - y);
  const p = (q) => s[Math.min(s.length - 1, Math.floor(q * s.length))];
  return { n: s.length, min: +s[0].toFixed(2), p50: +p(0.5).toFixed(2), p95: +p(0.95).toFixed(2), max: +s[s.length - 1].toFixed(2) };
};

function jwt(role, secret) {
  const b64 = (b) => Buffer.from(b).toString("base64url");
  const now = Math.floor(Date.now() / 1000);
  const h = b64(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const p = b64(JSON.stringify({ iss: "supabase", iat: now, exp: now + 3600, role }));
  const s = createHmac("sha256", secret).update(`${h}.${p}`).digest("base64url");
  return `${h}.${p}.${s}`;
}

async function benchSupabase() {
  const API = (process.env.LIBREBASE_API ?? "http://127.0.0.1:3000").replace(/\/$/, "");
  const SR = process.env.LIBREBASE_SERVICE_ROLE ?? "";
  if (!SR) throw new Error("LIBREBASE_SERVICE_ROLE required");
  const hdr = { apikey: SR, Authorization: `Bearer ${SR}`, "Content-Type": "application/json", Prefer: "return=representation" };

  // ensure table + btree index (via psql through podman is cleaner; here via REST create is not possible)
  // table must be created out-of-band (psql). Ingest via PostgREST bulk insert.
  const ingestStart = performance.now();
  const BATCH = 500;
  let inserted = 0;
  for (let i = 0; i < ROWS; i += BATCH) {
    const rows = [];
    for (let j = i; j < Math.min(i + BATCH, ROWS); j++) rows.push({ code: `code-${j}`, value: j });
    const res = await fetch(`${API}/items`, { method: "POST", headers: hdr, body: JSON.stringify(rows) });
    if (!res.ok) throw new Error(`insert batch ${i}: ${res.status} ${await res.text()}`);
    inserted += rows.length;
  }
  const ingestMs = performance.now() - ingestStart;

  const lat = { lookup: [], range: [], page: [] };
  for (let q = 0; q < Q; q++) {
    const key = `code-${Math.floor(Math.random() * ROWS)}`;
    const t = performance.now();
    await fetch(`${API}/items?code=eq.${key}&select=value&limit=1`, { headers: { apikey: SR, Authorization: `Bearer ${SR}` } });
    lat.lookup.push(performance.now() - t);
    const t2 = performance.now();
    await fetch(`${API}/items?code=like.code-${Math.floor(Math.random() * ROWS)}%25&select=value&limit=50`, { headers: { apikey: SR, Authorization: `Bearer ${SR}` } });
    lat.range.push(performance.now() - t2);
    const t3 = performance.now();
    await fetch(`${API}/items?select=value&limit=50`, { headers: { apikey: SR, Authorization: `Bearer ${SR}` } });
    lat.page.push(performance.now() - t3);
  }
  return { stack: "supabase-pg-btree", rows: inserted, ingest_rows_per_sec: Math.round(inserted / (ingestMs / 1000)), ingest_total_ms: Math.round(ingestMs), query_ms: Object.fromEntries(Object.entries(lat).map(([k, v]) => [k, stats(v)])) };
}

function lidbExec(dataDir, sql, params = []) {
  const embed = process.env.LIDB_EMBED ?? "/Users/julian/Documents/coding-projects/li-langverse-gitlab/li-langverse/lidb/build/smoke/lidb_embed";
  const r = spawnSync(embed, ["exec-json", dataDir, sql], { input: JSON.stringify(params), encoding: "utf8" });
  if (r.status !== 0) throw new Error(`lidb exec failed: ${r.stderr || r.stdout}`);
  return JSON.parse(r.stdout);
}

/** Persistent `lidb_embed session` (NDJSON) — the realistic server path, avoids
 *  per-query subprocess spawn (which dominated the old benchmark at ~5ms/query). */
function lidbSession(dataDir) {
  const embed = process.env.LIDB_EMBED ?? "/Users/julian/Documents/coding-projects/li-langverse-gitlab/li-langverse/lidb/build/smoke/lidb_embed";
  const child = spawn(embed, ["session", dataDir], { stdio: ["pipe", "pipe", "ignore"] });
  let buf = "";
  let gotReady = false;
  const queue = [];
  const readyResolvers = [];
  child.stdout.on("data", (c) => {
    buf += c.toString();
    let i;
    while ((i = buf.indexOf("\n")) !== -1) {
      const line = buf.slice(0, i).trim();
      buf = buf.slice(i + 1);
      if (!line) continue;
      let msg;
      try { msg = JSON.parse(line); } catch { continue; }
      if (!gotReady) {
        gotReady = true;
        readyResolvers.forEach((r) => r());
        continue;
      }
      if (queue.length) queue.shift()(msg);
    }
  });
  return {
    ready: new Promise((res) => { if (gotReady) res(); else readyResolvers.push(res); }),
    exec(sql, params = []) {
      const p = new Promise((res) => queue.push(res));
      child.stdin.write(JSON.stringify({ cmd: "exec", sql, params }) + "\n");
      return p;
    },
    close() {
      child.stdin.write(JSON.stringify({ cmd: "quit" }) + "\n");
      child.kill();
    },
  };
}

async function benchLidb() {
  const dir = process.env.LIDB_DATA ?? "/tmp/lb-bench-data";
  mkdirSync(dir, { recursive: true });
  spawnSync(process.env.LIDB_EMBED ?? "lidb_embed", ["migrate", dir], { encoding: "utf8" });
  const s = lidbSession(dir);
  await s.ready;
  const r0 = await s.exec("CREATE TABLE IF NOT EXISTS items (id TEXT, code TEXT, value TEXT)");
  if (!r0.ok) throw new Error("CREATE TABLE failed: " + JSON.stringify(r0));
  await s.exec("CREATE INDEX IF NOT EXISTS idx_code ON items(code)");

  const ingestStart = performance.now();
  const BATCH = 2000;
  let inserted = 0;
  for (let i = 0; i < ROWS; i += BATCH) {
    // lidb exec_insert currently inserts ONE row per statement (multi-row VALUES
    // only applies the first). Insert rows individually for correctness.
    const batch = Math.min(BATCH, ROWS - i);
    for (let j = 0; j < batch; j++) {
      const n = i + j;
      await s.exec("INSERT INTO items (id, code, value) VALUES (?, ?, ?)", [`id-${n}`, `code-${n}`, String(n)]);
      inserted++;
    }
  }
  const ingestMs = performance.now() - ingestStart;

  const lat = { lookup: [], range: [], page: [] };
  for (let q = 0; q < Q; q++) {
    const key = `code-${Math.floor(Math.random() * ROWS)}`;
    const t = performance.now();
    await s.exec("SELECT value FROM items WHERE code = ?", [key]);
    lat.lookup.push(performance.now() - t);
    const t2 = performance.now();
    await s.exec("SELECT value FROM items WHERE code LIKE ? LIMIT 50", [`code-${Math.floor(Math.random() * ROWS)}%`]);
    lat.range.push(performance.now() - t2);
    const t3 = performance.now();
    await s.exec("SELECT value FROM items LIMIT 50");
    lat.page.push(performance.now() - t3);
  }
  s.close();
  return {
    stack: "librebase-lidb-sorted_tree",
    transport: "persistent session (NDJSON)",
    rows: inserted,
    ingest_rows_per_sec: Math.round(inserted / (ingestMs / 1000)),
    ingest_total_ms: Math.round(ingestMs),
    query_ms: Object.fromEntries(Object.entries(lat).map(([k, v]) => [k, stats(v)])),
  };
}

const out = STACK === "sb" ? await benchSupabase() : await benchLidb();
if (!out || Object.keys(out).length === 0) throw new Error("benchmark returned empty");
console.log(JSON.stringify(out, null, 2));
