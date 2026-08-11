#!/usr/bin/env node
/**
 * Supabase-js compatibility suite — runs the SAME @supabase/supabase-js surface
 * against any PostgREST+GoTrue-compatible backend, AS-IS (no backend fixes).
 *
 * BACKEND=supalite|supabase|librebase  (or API_URL + ANON_KEY)
 *
 * Uses the real @supabase/supabase-js client. Records actual pass/fail; does not
 * crash on response-shape differences (e.g. insert returning object vs array).
 */
import { createClient } from "@supabase/supabase-js";
import { performance } from "node:perf_hooks";

const BACKEND = process.env.BACKEND ?? "supalite";
const CFG = {
  supalite: { api: "http://127.0.0.1:54321", anon: "dev-anon-key", label: "Supabase Lite (SQLite)", auth: "http://127.0.0.1:54321" },
  supabase: { api: "http://127.0.0.1:8000", anon: "", label: "Supabase full (Kong)", auth: "http://127.0.0.1:8000" },
  librebase: { api: "http://127.0.0.1:54325", anon: "anon", label: "Librebase (lis)", auth: "http://127.0.0.1:54325" },
}[BACKEND];
const API = process.env.API_URL ?? CFG.api;
const AUTH_URL = process.env.AUTH_URL ?? CFG.auth;
const ANON = process.env.ANON_KEY ?? CFG.anon;

// Supabase full: createClient needs one URL; use a fetch that routes /auth to
// AUTH_URL and everything else to API (split gateway).
const fetcher = AUTH_URL === API ? undefined : async (input, init) => {
  const url = String(input);
  const target = url.includes("/auth/") ? AUTH_URL + url.slice(API.length) : url;
  return fetch(target, init);
};
const sb = createClient(API, ANON, fetcher ? { fetch: fetcher } : undefined);
const results = [];
function check(name, ok, detail = "") {
  results.push({ name, ok, detail });
  console.log(`${ok ? "PASS" : "FAIL"}  ${name}${detail ? "  " + detail : ""}`);
}
const email = `${BACKEND}-${Date.now()}@example.com`;
const pw = "secret-pass";
const latencies = [];
async function timed(name, fn) {
  const t0 = performance.now();
  try {
    const r = await fn();
    latencies.push({ name, ms: performance.now() - t0 });
    return r;
  } catch (e) {
    latencies.push({ name, ms: performance.now() - t0, err: e.message });
    throw e;
  }
}

// Helper: normalize the PK from insert/select responses (array or single object).
function firstId(data) {
  if (Array.isArray(data) && data.length) return data[0]?.id;
  if (data && typeof data === "object") return data.id;
  return undefined;
}

export async function run() {
  // ---- Auth ----
  try {
    const { data, error } = await timed("auth.signUp", () => sb.auth.signUp({ email, password: pw }));
    check("auth.signUp", !error, error?.message ?? "");
  } catch (e) { check("auth.signUp", false, e.message); }

  try {
    const { data, error } = await timed("auth.signInWithPassword", () => sb.auth.signInWithPassword({ email, password: pw }));
    check("auth.signInWithPassword", !error, error?.message ?? "no session?");
  } catch (e) { check("auth.signInWithPassword", false, e.message); }

  try {
    const { data, error } = await timed("auth.getUser", () => sb.auth.getUser());
    check("auth.getUser", !error && !!data?.user, error?.message ?? "");
  } catch (e) { check("auth.getUser", false, e.message); }

  // ---- Data API: insert ----
  let ins = null;
  try {
    const { data, error } = await timed("from.insert", () => sb.from("items").insert({ code: "c1", value: 1 }).select());
    ins = data;
    check("from.insert", !error, error?.message ?? "shape=" + (Array.isArray(data) ? "array" : typeof data));
  } catch (e) { check("from.insert", false, e.message); }

  // ---- Data API: select + eq ----
  try {
    const { data, error } = await timed("from.select.eq", () => sb.from("items").select("*").eq("code", "c1"));
    const ok = !error && (Array.isArray(data) ? data.length >= 1 : data != null);
    check("from.select.eq", ok, error?.message ?? `rows=${Array.isArray(data) ? data.length : typeof data}`);
  } catch (e) { check("from.select.eq", false, e.message); }

  // ---- Data API: update by id ----
  const upId = firstId(ins);
  if (upId != null) {
    try {
      const { data, error } = await timed("from.update.id", () => sb.from("items").update({ value: 22 }).eq("id", upId));
      check("from.update.id", !error, error?.message ?? "");
    } catch (e) { check("from.update.id", false, e.message); }
  } else {
    check("from.update.id", false, "insert returned no PK id (shape=" + typeof ins + ")");
  }

  // ---- order + limit + range ----
  try {
    const { data, error } = await timed("from.order.limit", () => sb.from("items").select("code").order("id", { ascending: false }).limit(1));
    check("from.order.limit", !error, error?.message ?? "");
  } catch (e) { check("from.order.limit", false, e.message); }

  try {
    const { data, error } = await timed("from.range", () => sb.from("items").select("*").range(0, 1));
    check("from.range", !error, error?.message ?? "");
  } catch (e) { check("from.range", false, e.message); }

  // ---- delete by id ----
  const delId = firstId(ins);
  if (delId != null) {
    try {
      const { error } = await timed("from.delete.id", () => sb.from("items").delete().eq("id", delId));
      check("from.delete.id", !error, error?.message ?? "");
    } catch (e) { check("from.delete.id", false, e.message); }
  } else {
    check("from.delete.id", false, "no PK id available");
  }

  // ---- Storage ----
  try {
    const { data, error } = await timed("storage.listBuckets", () => sb.storage.listBuckets());
    check("storage.listBuckets", !error, error?.message ?? "");
  } catch (e) { check("storage.listBuckets", false, e.message); }

  try {
    const { error } = await timed("storage.createBucket", () => sb.storage.createBucket(`bench-${Date.now()}`));
    check("storage.createBucket", !error, error?.message ?? "");
  } catch (e) { check("storage.createBucket", false, e.message); }

  try {
    const { data, error } = await timed("storage.upload", () => sb.storage.from("bench").upload(`a-${Date.now()}.txt`, "hello"));
    check("storage.upload", !error, error?.message ?? "");
  } catch (e) { check("storage.upload", false, e.message); }

  // ---- Summary ----
  const pass = results.filter((r) => r.ok).length;
  const fail = results.filter((r) => !r.ok).length;
  const avg = (n) => {
    const l = latencies.filter((x) => x.name === n && !x.err);
    return l.length ? (l.reduce((a, b) => a + b.ms, 0) / l.length).toFixed(2) : "-";
  };
  const summary = {
    backend: BACKEND,
    label: CFG.label,
    api: API,
    passed: pass,
    failed: fail,
    total: results.length,
    per_op_ms: Object.fromEntries([...new Set(latencies.map((l) => l.name))].map((n) => [n, avg(n)])),
  };
  console.log("\n" + JSON.stringify(summary, null, 2));
  if (fail > 0) process.exitCode = 1;
}

if (process.argv[1] === new URL(import.meta.url).pathname) {
  run();
}
