/**
 * CRUD latency benchmark — 60 HTTP responses against the lis-backed todo app.
 * Same measurement as apps/todo-app-supabase/test/bench-crud.mjs (head-to-head).
 *
 * Spawns lis + the todo-app HTTP server locally, drives 60 rounds of
 * create/list/update/delete, reports min/p50/p95/max/mean per op.
 */
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const REPO = path.resolve(fileURLToPath(new URL("../../../", import.meta.url)));
const LIS = process.env.LIS_ROOT ?? path.resolve(REPO, "..", "lis");
const API_PORT = 15433;
const APP_PORT = 18788;
const ROUNDS = Number(process.env.BENCH_ROUNDS ?? 60);

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function waitHttp(url) {
  for (let i = 0; i < 60; i++) {
    try { const r = await fetch(url); if (r.ok || r.status < 500) return; } catch {}
    await sleep(250);
  }
  throw new Error(`never healthy: ${url}`);
}
async function timeRequest(fn) {
  const start = performance.now();
  const out = await fn();
  return { ms: performance.now() - start, out };
}
function stats(a) {
  const s = [...a].sort((x, y) => x - y);
  const p = (q) => s[Math.min(s.length - 1, Math.floor(q * s.length))];
  return { n: s.length, min: s[0], p50: p(0.5), p95: p(0.95), max: s[s.length - 1], mean: s.reduce((x, y) => x + y, 0) / s.length };
}

export async function run() {
  const tmp = mkdtempSync(path.join(tmpdir(), "lis-bench-"));
  const children = [];
  const cleanup = () => children.forEach((c) => { try { c.kill("SIGKILL"); } catch {} });

  let lis;
  try {
    lis = spawn(process.env.PYTHON ?? "python3", [path.join(LIS, "routes", "registry", "server.py"), "--host", "127.0.0.1", "--port", String(API_PORT)], {
      env: { ...process.env, PYTHONPATH: LIS, LI_API_PORT: String(API_PORT), LI_JWT_SECRET: "bench", LI_AUTH_BACKEND: "mock", LI_REGISTRY_MOCK: "1", LI_DATA_DIR: path.join(tmp, "lis") },
      stdio: "ignore",
    });
    children.push(lis);
    await waitHttp(`http://127.0.0.1:${API_PORT}/rest/v1/todos?limit=1`);
    const app = spawn(process.execPath, [path.join(REPO, "apps", "todo-app", "src", "server.mjs")], {
      env: { ...process.env, PORT: String(APP_PORT), LIBREBASE_API: `http://127.0.0.1:${API_PORT}`, LIBREBASE_ANON: "anon" },
      stdio: "ignore",
    });
    children.push(app);
    await waitHttp(`http://127.0.0.1:${APP_PORT}/health`);
  } catch (e) {
    cleanup();
    console.log("lis bench: SKIPPED", e.message);
    return;
  }

  const BASE = `http://127.0.0.1:${APP_PORT}`;
  const email = `bench-${Date.now()}@example.com`;
  const pw = "secret-pass";

  const su = await timeRequest(async () => {
    const r = await fetch(`${BASE}/auth/signup`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email, password: pw }) });
    return r.json();
  });
  const token = su.out.access_token;
  assert.ok(token, "signup token");

  const lat = { create: [], list: [], update: [], delete: [] };
  const totalStart = performance.now();
  for (let i = 0; i < ROUNDS; i++) {
    const c = await timeRequest(async () => {
      const r = await fetch(`${BASE}/todos`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: "Bearer " + token }, body: JSON.stringify({ title: `bench-${i}` }) });
      return r.json();
    });
    const id = c.out.todo.id;
    lat.create.push(c.ms);

    const l = await timeRequest(async () => {
      const r = await fetch(`${BASE}/todos`, { headers: { Authorization: "Bearer " + token } });
      await r.json();
    });
    lat.list.push(l.ms);

    const u = await timeRequest(async () => {
      const r = await fetch(`${BASE}/todos/${id}/complete`, { method: "POST", headers: { Authorization: "Bearer " + token } });
      await r.json();
    });
    lat.update.push(u.ms);

    const d = await timeRequest(async () => {
      const r = await fetch(`${BASE}/todos/${id}`, { method: "DELETE", headers: { Authorization: "Bearer " + token } });
      await r.json();
    });
    lat.delete.push(d.ms);
  }
  const totalMs = performance.now() - totalStart;

  const report = {
    backend: "lis (local)",
    url: BASE,
    rounds: ROUNDS,
    total_time_ms: Math.round(totalMs),
    total_responses: ROUNDS * 4,
    ops_per_second: Math.round((ROUNDS * 4) / (totalMs / 1000)),
    signup_ms: Math.round(su.ms),
    per_op_ms: Object.fromEntries(Object.entries(lat).map(([k, v]) => [k, stats(v)])),
  };
  console.log(JSON.stringify(report, null, 2));
  cleanup();
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  run().then(() => process.exit(0)).catch((e) => { console.error(e); process.exit(1); });
}
