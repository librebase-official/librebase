#!/usr/bin/env node
/**
 * Object storage benchmark — Librebase (lis) vs Supabase Storage (podman).
 *
 * Measures bucket create, object PUT (upload), object list (POST), object GET,
 * and signed GET round-trip latency on both stacks.
 *
 * Supabase side unblocked 2026-08-11: storage role grants + canonical RLS
 * policies + PGRST_DB_SCHEMAS=storage (see CATCHUP G4).
 *
 * STACK=lis|sb
 *   lis: LIS_API=http://127.0.0.1:54321   (signs up a throwaway user)
 *   sb:  SB_API=http://127.0.0.1:8000  SB_KEY=<anon-or-service JWT>
 */
import { performance } from "node:perf_hooks";

const STACK = process.env.STACK ?? "lis";
const RUNS = Number(process.env.RUNS ?? 60);
const BUCKET = process.env.BUCKET ?? "bench-" + Date.now();

const stats = (a) => {
  if (!a.length) return { n: 0, min: 0, p50: 0, p95: 0, max: 0 };
  const s = [...a].sort((x, y) => x - y);
  const p = (q) => s[Math.min(s.length - 1, Math.floor(q * s.length))];
  return { n: s.length, min: +s[0].toFixed(2), p50: +p(0.5).toFixed(2), p95: +p(0.95).toFixed(2), max: +s[s.length - 1].toFixed(2) };
};

const j = (b) => JSON.stringify(b);

async function getLisToken() {
  const API = (process.env.LIS_API ?? "http://127.0.0.1:54321").replace(/\/$/, "");
  const email = process.env.LIS_EMAIL ?? `storage-bench-${Date.now()}@example.com`;
  const password = process.env.LIS_PASSWORD ?? "storage-bench-secret";
  const post = (p, b) => fetch(`${API}${p}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: j(b) });
  await post("/v1/auth/signup", { email, password }).catch(() => {});
  const res = await post("/v1/auth/login", { email, password });
  const body = await res.json();
  const token = body?.access_token || body?.token;
  if (!token) throw new Error(`lis login failed: ${res.status} ${j(body)}`);
  return { token, API };
}

async function main() {
  let API;
  let hdr = { "Content-Type": "application/json" };
  let stackLabel;
  if (STACK === "lis") {
    const { token, API: a } = await getLisToken();
    API = a;
    hdr = { ...hdr, Authorization: `Bearer ${token}`, apikey: token };
    stackLabel = "librebase-lis-storage";
  } else {
    API = (process.env.SB_API ?? "http://127.0.0.1:8000").replace(/\/$/, "");
    const key = process.env.SB_KEY;
    if (!key) throw new Error("SB_KEY required for STACK=sb (service_role JWT)");
    hdr = { ...hdr, Authorization: `Bearer ${key}`, apikey: key };
    stackLabel = "supabase-storage";
  }

  const createBucket = [];
  for (let i = 0; i < 5; i++) {
    const t = performance.now();
    await fetch(`${API}/storage/v1/bucket`, { method: "POST", headers: hdr, body: j({ name: BUCKET, public: false }) });
    createBucket.push(performance.now() - t);
  }

  const upload = [];
  const list = [];
  const get = [];
  const signed = [];
  const payload = Buffer.from("bench-object-".repeat(64));

  for (let i = 0; i < RUNS; i++) {
    const key = `bench/${i}.txt`;
    let t = performance.now();
    await fetch(`${API}/storage/v1/object/${BUCKET}/${key}`, { method: "POST", headers: { ...hdr, "Content-Type": "text/plain" }, body: payload });
    upload.push(performance.now() - t);

    // list is POST with a JSON body on both stacks
    t = performance.now();
    await fetch(`${API}/storage/v1/object/list/${BUCKET}`, {
      method: "POST",
      headers: hdr,
      body: j({ prefix: "bench", limit: 10, offset: 0, sortBy: { column: "name", order: "asc" } }),
    });
    list.push(performance.now() - t);

    t = performance.now();
    const got = await fetch(`${API}/storage/v1/object/${BUCKET}/${key}`, { headers: hdr });
    await got.arrayBuffer();
    get.push(performance.now() - t);

    t = performance.now();
    const signRes = await fetch(`${API}/storage/v1/object/sign/${BUCKET}/${key}`, { method: "POST", headers: hdr, body: j({ expiresIn: 300 }) });
    const signBody = await signRes.json();
    if (signBody?.signedURL) {
      const useT = performance.now();
      // lis returns /storage/v1/... ; supabase returns /object/sign/... (kong-relative)
      const url = signBody.signedURL.startsWith("/storage/v1") ? `${API}${signBody.signedURL}` : `${API}/storage/v1/${signBody.signedURL.replace(/^\/+/, "")}`;
      const ok = await fetch(url);
      await ok.arrayBuffer();
      signed.push(performance.now() - useT);
    }
  }

  console.log(
    JSON.stringify(
      {
        benchmark: "object storage — bucket/upload/list/get/signed-GET latency",
        stack: stackLabel,
        date: new Date().toISOString().slice(0, 10),
        bucket: BUCKET,
        object_bytes: payload.length,
        runs: RUNS,
        create_bucket_ms: stats(createBucket),
        upload_ms: stats(upload),
        list_ms: stats(list),
        get_ms: stats(get),
        signed_get_ms: stats(signed),
        honesty:
          "Dual-stack since 2026-08-11 after fixing Supabase storage bootstrap (role grants, RLS policies, PGRST_DB_SCHEMAS). Same script, same bucket shape.",
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
