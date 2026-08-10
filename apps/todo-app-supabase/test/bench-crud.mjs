/**
 * CRUD latency benchmark — 60 HTTP responses against a real Supabase backend.
 *
 * Env:
 *   LIBREBASE_API       Supabase URL (default https://supabase.obsevia.com)
 *   LIBREBASE_ANON      anon key (required)
 *   LIBREBASE_SERVICE_ROLE  service_role key (required to create a confirmed user)
 *   BENCH_ROUNDS        responses to measure (default 60)
 *
 * Measures per-operation latency (signup, signin, create, list, update, delete)
 * across N responses, reporting min / p50 / p95 / max / mean + total time.
 */
import assert from "node:assert/strict";

const API = (process.env.LIBREBASE_API ?? "https://supabase.obsevia.com").replace(/\/$/, "");
const AUTH = (process.env.LIBREBASE_AUTH_URL ?? API).replace(/\/$/, "");
const REST_PREFIX = (process.env.LIBREBASE_REST_PREFIX ?? "/rest/v1").replace(/\/$/, "");
const ANON = process.env.LIBREBASE_ANON ?? "";
const SR = process.env.LIBREBASE_SERVICE_ROLE ?? "";
const ROUNDS = Number(process.env.BENCH_ROUNDS ?? 60);
const EMAIL = `bench-${Date.now()}@example.com`;
const PW = "secret-pass";

assert.ok(ANON, "LIBREBASE_ANON required");
assert.ok(SR, "LIBREBASE_SERVICE_ROLE required");

const h = (token) => ({
  apikey: ANON,
  Authorization: `Bearer ${token}`,
  "Content-Type": "application/json",
});

async function timeRequest(fn) {
  const start = performance.now();
  const out = await fn();
  const ms = performance.now() - start;
  return { ms, out };
}

function stats(latencies) {
  const sorted = [...latencies].sort((a, b) => a - b);
  const p = (q) => sorted[Math.min(sorted.length - 1, Math.floor(q * sorted.length))];
  const mean = sorted.reduce((a, b) => a + b, 0) / sorted.length;
  return {
    n: sorted.length,
    min: sorted[0],
    p50: p(0.5),
    p95: p(0.95),
    max: sorted[sorted.length - 1],
    mean,
  };
}

export async function run() {
  // 1. Create a confirmed user via admin API (service_role).
  const createUser = await timeRequest(async () => {
    const res = await fetch(`${AUTH}/admin/users`, {
      method: "POST",
      headers: h(SR),
      body: JSON.stringify({ email: EMAIL, password: PW, email_confirm: true }),
    });
    const body = await res.json();
    assert.ok(res.ok, `admin create user: ${res.status} ${JSON.stringify(body)}`);
    return body;
  });

  // 2. Sign in once (shared session for CRUD).
  const signinRes = await timeRequest(async () => {
    const res = await fetch(`${AUTH}/token?grant_type=password`, {
      method: "POST",
      headers: h(ANON),
      body: JSON.stringify({ email: EMAIL, password: PW }),
    });
    const body = await res.json();
    assert.ok(res.ok, `signin: ${res.status} ${JSON.stringify(body)}`);
    return body;
  });
  const token = signinRes.out.access_token;
  const sub = JSON.parse(Buffer.from(token.split(".")[1], "base64url").toString()).sub;

  // Warmup: one full CRUD cycle so TLS + connection pooling reach steady state.
  {
    const w = await fetch(`${API}${REST_PREFIX}/todos`, {
      method: "POST", headers: { ...h(token), Prefer: "return=representation" },
      body: JSON.stringify({ title: "warmup", done: false, user_id: sub }),
    });
    const wBody = await w.json();
    if (!Array.isArray(wBody) || !wBody[0]) {
      throw new Error(`warmup create returned non-array: ${w.status} ${JSON.stringify(wBody)}`);
    }
    const wid = wBody[0].id;
    await fetch(`${API}${REST_PREFIX}/todos?id=eq.${wid}`, { method: "PATCH", headers: { ...h(token), Prefer: "return=representation" }, body: JSON.stringify({ done: true }) });
    await fetch(`${API}${REST_PREFIX}/todos?id=eq.${wid}`, { method: "DELETE", headers: h(token) });
  }

  const latencies = {
    create: [],
    list: [],
    update: [],
    delete: [],
  };
  const totalStart = performance.now();
  const ids = [];

  for (let i = 0; i < ROUNDS; i++) {
    // create
    const c = await timeRequest(async () => {
      const res = await fetch(`${API}${REST_PREFIX}/todos`, {
        method: "POST",
        headers: { ...h(token), Prefer: "return=representation" },
        body: JSON.stringify({ title: `bench-${i}`, done: false, user_id: sub }),
      });
      const body = await res.json();
      assert.ok(res.ok, `create[${i}]: ${res.status}`);
      return body;
    });
    ids.push(c.out[0].id);
    latencies.create.push(c.ms);

    // list
    const l = await timeRequest(async () => {
      const res = await fetch(`${API}${REST_PREFIX}/todos?select=id&limit=1`, { headers: h(token) });
      await res.json();
      assert.ok(res.ok, `list[${i}]: ${res.status}`);
    });
    latencies.list.push(l.ms);

    // update (complete)
    const u = await timeRequest(async () => {
      const res = await fetch(`${API}${REST_PREFIX}/todos?id=eq.${ids[ids.length - 1]}`, {
        method: "PATCH",
        headers: { ...h(token), Prefer: "return=representation" },
        body: JSON.stringify({ done: true }),
      });
      await res.json();
      assert.ok(res.ok, `update[${i}]: ${res.status}`);
    });
    latencies.update.push(u.ms);

    // delete
    const d = await timeRequest(async () => {
      const res = await fetch(`${API}${REST_PREFIX}/todos?id=eq.${ids[ids.length - 1]}`, {
        method: "DELETE",
        headers: h(token),
      });
      assert.ok(res.ok, `delete[${i}]: ${res.status}`);
    });
    latencies.delete.push(d.ms);
  }
  const totalMs = performance.now() - totalStart;

  const report = {
    backend: "supabase",
    url: API,
    rounds: ROUNDS,
    total_time_ms: Math.round(totalMs),
    total_responses: ROUNDS * 4,
    ops_per_second: Math.round((ROUNDS * 4) / (totalMs / 1000)),
    admin_create_user_ms: Math.round(createUser.ms),
    signin_ms: Math.round(signinRes.ms),
    per_op_ms: Object.fromEntries(Object.entries(latencies).map(([k, v]) => [k, stats(v)])),
  };
  console.log(JSON.stringify(report, null, 2));

  // sanity: every op was measured 60 times
  for (const [k, v] of Object.entries(latencies)) {
    assert.equal(v.length, ROUNDS, `${k} should have ${ROUNDS} samples`);
  }
  return report;
}

if (process.argv[1] === new URL(import.meta.url).pathname) {
  run().then((r) => process.exit(0)).catch((e) => { console.error(e); process.exit(1); });
}
