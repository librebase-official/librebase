#!/usr/bin/env node
/**
 * Realtime streaming benchmark — Supabase Realtime vs Librebase (lis realtime).
 *
 * Measures:
 *   - WS connect latency
 *   - postgres_changes join/subscribe latency
 *   - (Supabase) event delivery latency: INSERT via PostgREST -> WS postgres_changes
 *
 * Supabase:  WS ws://127.0.0.1:4000/websocket  (Realtime v2 Phoenix protocol)
 * Librebase: WS ws://127.0.0.1:54323/realtime/v1/websocket (lis realtime, Phoenix v1)
 *
 * Honesty: lis row-event delivery depends on the lidb changefeed (native WAL poll);
 * the HTTP in-memory REST store does not emit changefeed records, so event-delivery
 * is only fully measured on Supabase. We measure connect+join on both, and document
 * the lis delivery path (native changefeed) separately.
 */
import { performance } from "node:perf_hooks";

const STACK = process.env.STACK ?? "sb";
const N = Number(process.env.RUNS ?? 60);

const stats = (a) => {
  const s = [...a].sort((x, y) => x - y);
  const p = (q) => s[Math.min(s.length - 1, Math.floor(q * s.length))];
  return { n: s.length, min: +s[0].toFixed(2), p50: +p(0.5).toFixed(2), p95: +p(0.95).toFixed(2), max: +s[s.length - 1].toFixed(2) };
};

async function benchSupabase() {
  const WS = process.env.SB_WS ?? "ws://127.0.0.1:4000/websocket";
  const API = (process.env.LIBREBASE_API ?? "http://127.0.0.1:3000").replace(/\/$/, "");
  const SR = process.env.LIBREBASE_SERVICE_ROLE ?? "";
  const ANON = process.env.LIBREBASE_ANON ?? "";
  if (!SR) throw new Error("LIBREBASE_SERVICE_ROLE required");
  const hdr = { apikey: ANON || SR, Authorization: `Bearer ${SR}`, "Content-Type": "application/json" };

  // one subscription for event delivery
  const ws = new WebSocket(WS);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  const connectLat = performance.now() - 0; // baseline below

  // subscribe to postgres_changes on public.items INSERT
  const joinSent = performance.now();
  ws.send(JSON.stringify({
    topic: "realtime:items",
    event: "phx_join",
    payload: { config: { postgres_changes: [{ event: "INSERT", schema: "public", table: "items" }] } },
    ref: "1", join_ref: "1",
  }));
  const joinReply = await new Promise((res) => {
    ws.onmessage = (ev) => {
      const m = JSON.parse(ev.data);
      if (m.event === "phx_reply") res(m);
    };
  });
  const joinMs = performance.now() - joinSent;

  // event delivery: insert via PostgREST -> wait for WS postgres_changes
  const delivery = [];
  for (let i = 0; i < N; i++) {
    const code = `rt-${i}`;
    const t = performance.now();
    await fetch(`${API}/items`, { method: "POST", headers: hdr, body: JSON.stringify({ code, value: i }) });
    const delivered = await new Promise((res) => {
      const to = setTimeout(() => res(null), 2000);
      ws.onmessage = (ev) => {
        const m = JSON.parse(ev.data);
        if (m.payload?.record?.code === code) { clearTimeout(to); res(performance.now() - t); }
      };
    });
    if (delivered !== null) delivery.push(delivered);
  }
  ws.close();
  return {
    stack: "supabase-realtime",
    ws: WS,
    connect_ms: Math.round(connectLat),
    join_subscribe_ms: Math.round(joinMs),
    event_delivery_ms: stats(delivery),
    events_received: delivery.length,
  };
}

async function benchLis() {
  const WS = process.env.LIS_WS ?? "ws://127.0.0.1:54323/realtime/v1/websocket";
  const API = (process.env.LIS_API ?? "http://127.0.0.1:54321").replace(/\/$/, "");
  const N = Number(process.env.RUNS ?? 60);

  const connects = [];
  const joins = [];
  const delivery = [];
  for (let i = 0; i < N; i++) {
    const t0 = performance.now();
    const ws = new WebSocket(WS);
    await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
    connects.push(performance.now() - t0);
    const t1 = performance.now();
    ws.send(JSON.stringify({
      topic: "realtime:parity",
      event: "phx_join",
      payload: { config: { postgres_changes: [{ event: "INSERT", schema: "public", table: "parity_items" }] } },
      ref: "1", join_ref: "1",
    }));
    const joinReply = await new Promise((res) => {
      ws.onmessage = (ev) => { const m = JSON.parse(ev.data); if (m.event === "phx_reply") res(m); };
    });
    joins.push(performance.now() - t1);
    // event delivery: insert via lis REST -> wait for WS postgres_changes
    const code = `lis-rt-${i}`;
    const t = performance.now();
    await fetch(`${API}/rest/v1/parity_items`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Prefer: "return=representation" },
      body: JSON.stringify({ name: "lis-rt", code }),
    });
    const delivered = await new Promise((res) => {
      const to = setTimeout(() => res(null), 2000);
      ws.onmessage = (ev) => {
        const m = JSON.parse(ev.data);
        const data = m.payload?.data ?? {};
        if (m.event === "postgres_changes" && data.table === "parity_items" && data.record?.code === code) {
          clearTimeout(to); res(performance.now() - t);
        }
      };
    });
    if (delivered !== null) delivery.push(delivered);
    ws.close();
  }
  return {
    stack: "librebase-lis-realtime",
    ws: WS,
    connect_ms: stats(connects),
    join_subscribe_ms: stats(joins),
    event_delivery_ms: stats(delivery),
    events_received: delivery.length,
    honesty: "Requires lis REST + realtime sharing LI_DATA_DIR with LI_REST_CHANGEFEED=1; memory-store writes append changefeed JSONL the WS server fans out. Native lidb changefeed path measured separately.",
  };
}

const out = STACK === "sb" ? await benchSupabase() : await benchLis();
console.log(JSON.stringify(out, null, 2));
