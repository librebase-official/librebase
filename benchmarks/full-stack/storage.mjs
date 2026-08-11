#!/usr/bin/env node
/**
 * Object storage benchmark — Librebase (lis routes/storage).
 *
 * Measures bucket create, object PUT (upload), object list, object GET, and
 * signed GET round-trip latency. lis side only: the Supabase storage container
 * is blocked in our podman bootstrap (403 storage role grants), so a dual-stack
 * head-to-head is not possible until that bootstrap is fixed (see CATCHUP G4).
 *
 * STACK=lis   LIS_API (lis base, e.g. http://127.0.0.1:54321)
 *             LIS_AUTH=1 + LIS_EMAIL/LIS_PASSWORD for a Bearer JWT; if LIS_AUTH=0
 *             (default) it signs up/logs in a throwaway user.
 */
import { performance } from "node:perf_hooks";

const API = (process.env.LIS_API ?? "http://127.0.0.1:54321").replace(/\/$/, "");
const RUNS = Number(process.env.RUNS ?? 60);
const BUCKET = process.env.LIS_BUCKET ?? "bench-" + Date.now();

const stats = (a) => {
  if (!a.length) return { n: 0, min: 0, p50: 0, p95: 0, max: 0 };
  const s = [...a].sort((x, y) => x - y);
  const p = (q) => s[Math.min(s.length - 1, Math.floor(q * s.length))];
  return { n: s.length, min: +s[0].toFixed(2), p50: +p(0.5).toFixed(2), p95: +p(0.95).toFixed(2), max: +s[s.length - 1].toFixed(2) };
};

const j = (b) => JSON.stringify(b);
const POST = (path, body, hdrs = {}) =>
  fetch(`${API}${path}`, { method: "POST", headers: { "Content-Type": "application/json", ...hdrs }, body: j(body) });
const PUT = (path, body, hdrs = {}) =>
  fetch(`${API}${path}`, { method: "PUT", headers: { "Content-Type": "text/plain", ...hdrs }, body });
const GET = (path, hdrs = {}) => fetch(`${API}${path}`, { headers: hdrs });

async function getToken() {
  const email = process.env.LIS_EMAIL ?? `storage-bench-${Date.now()}@example.com`;
  const password = process.env.LIS_PASSWORD ?? "storage-bench-secret";
  await POST("/v1/auth/signup", { email, password }).catch(() => {});
  const res = await POST("/v1/auth/login", { email, password });
  const body = await res.json();
  const token = body?.access_token || body?.token;
  if (!token) throw new Error(`login failed: ${res.status} ${j(body)}`);
  return { token, email, password };
}

async function main() {
  const { token } = await getToken();
  const hdr = { Authorization: `Bearer ${token}`, apikey: token };

  // bucket create
  const createBucket = [];
  for (let i = 0; i < 5; i++) {
    const t = performance.now();
    await POST("/storage/v1/bucket", { name: BUCKET, public: false }, hdr);
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
    await PUT(`/storage/v1/object/${BUCKET}/${key}`, payload, { ...hdr, "Content-Type": "text/plain" });
    upload.push(performance.now() - t);

    t = performance.now();
    await GET(`/storage/v1/object/list/${BUCKET}?prefix=bench`, hdr);
    list.push(performance.now() - t);

    t = performance.now();
    const got = await GET(`/storage/v1/object/${BUCKET}/${key}`, hdr);
    await got.arrayBuffer();
    get.push(performance.now() - t);

    t = performance.now();
    const signRes = await POST(`/storage/v1/object/sign/${BUCKET}/${key}`, { expiresIn: 300 }, hdr);
    const signBody = await signRes.json();
    if (signBody?.signedURL) {
      const useT = performance.now();
      const ok = await fetch(`${API}${signBody.signedURL}`);
      await ok.arrayBuffer();
      signed.push(performance.now() - useT);
    }
  }

  console.log(
    JSON.stringify(
      {
        benchmark: "lis object storage — bucket/upload/list/get/signed-GET latency",
        stack: "librebase-lis-storage",
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
          "lis side only — Supabase storage blocked in podman bootstrap (403 role grants). Not a head-to-head.",
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
