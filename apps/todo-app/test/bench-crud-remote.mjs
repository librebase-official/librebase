/**
 * CRUD latency benchmark — 60 HTTP responses against the LIS-BACKED todo app,
 * driven the same way as apps/todo-app-supabase/test/bench-crud.mjs.
 *
 * Targets a REMOTE URL by default (todo.librebase.xyz) so both backends are
 * measured over the same public network path. Env:
 *   LIBREBASE_API   default https://todo.librebase.xyz
 *   BENCH_ROUNDS    default 60
 */
import assert from "node:assert/strict";

const API = (process.env.LIBREBASE_API ?? "https://todo.librebase.xyz").replace(/\/$/, "");
const ROUNDS = Number(process.env.BENCH_ROUNDS ?? 60);
const EMAIL = `bench-${Date.now()}@example.com`;
const PW = "secret-pass";

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
  // signup (lis returns token directly)
  const su = await timeRequest(async () => {
    const r = await fetch(`${API}/auth/signup`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: EMAIL, password: PW }) });
    const body = await r.json();
    assert.ok(r.ok, `signup: ${r.status} ${JSON.stringify(body)}`);
    return body;
  });
  const token = su.out.access_token;
  assert.ok(token, "signup returns access_token");

  // Warmup: 5 request/response cycles so TLS + connection pooling reach steady state.
  {
    const w = await fetch(`${API}/todos`, { headers: { Authorization: "Bearer " + token } });
    await w.json();
    const wc = await fetch(`${API}/todos`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: "Bearer " + token }, body: JSON.stringify({ title: "warmup" }) });
    const wb = await wc.json();
    const wid = wb.todo.id;
    await fetch(`${API}/todos/${wid}/complete`, { method: "POST", headers: { Authorization: "Bearer " + token } });
    await fetch(`${API}/todos/${wid}`, { method: "DELETE", headers: { Authorization: "Bearer " + token } });
  }

  const lat = { create: [], list: [], update: [], delete: [] };
  const totalStart = performance.now();
  for (let i = 0; i < ROUNDS; i++) {
    const c = await timeRequest(async () => {
      const r = await fetch(`${API}/todos`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: "Bearer " + token }, body: JSON.stringify({ title: `bench-${i}` }) });
      const body = await r.json();
      assert.ok(r.ok, `create[${i}]: ${r.status}`);
      return body;
    });
    const id = c.out.todo.id;
    lat.create.push(c.ms);

    const l = await timeRequest(async () => {
      const r = await fetch(`${API}/todos`, { headers: { Authorization: "Bearer " + token } });
      await r.json();
      assert.ok(r.ok, `list[${i}]: ${r.status}`);
    });
    lat.list.push(l.ms);

    const u = await timeRequest(async () => {
      const r = await fetch(`${API}/todos/${id}/complete`, { method: "POST", headers: { Authorization: "Bearer " + token } });
      await r.json();
      assert.ok(r.ok, `update[${i}]: ${r.status}`);
    });
    lat.update.push(u.ms);

    const d = await timeRequest(async () => {
      const r = await fetch(`${API}/todos/${id}`, { method: "DELETE", headers: { Authorization: "Bearer " + token } });
      await r.json();
      assert.ok(r.ok, `delete[${i}]: ${r.status}`);
    });
    lat.delete.push(d.ms);
  }
  const totalMs = performance.now() - totalStart;

  const report = {
    backend: "librebase-lis (remote)",
    url: API,
    rounds: ROUNDS,
    total_time_ms: Math.round(totalMs),
    total_responses: ROUNDS * 4,
    ops_per_second: Math.round((ROUNDS * 4) / (totalMs / 1000)),
    signup_ms: Math.round(su.ms),
    per_op_ms: Object.fromEntries(Object.entries(lat).map(([k, v]) => [k, stats(v)])),
  };
  console.log(JSON.stringify(report, null, 2));
}

if (process.argv[1] === new URL(import.meta.url).pathname) {
  run().then(() => process.exit(0)).catch((e) => { console.error(e); process.exit(1); });
}
