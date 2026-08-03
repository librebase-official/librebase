/**
 * Offline smoke: shape + URL wiring via mock fetch (no live lis required).
 */
import { createClient } from "../src/index.js";
import assert from "node:assert/strict";

const calls = [];

function mockFetch(input, init = {}) {
  calls.push({ url: String(input), method: init.method ?? "GET", body: init.body, headers: init.headers });
  const url = String(input);
  if (url.includes("/v1/auth/")) {
    return Promise.resolve(
      new Response(JSON.stringify({ access_token: "tok-1", user: { email: "a@b.c" } }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  }
  if (url.includes("/rest/v1/")) {
    if ((init.method ?? "GET") === "POST") {
      return Promise.resolve(
        new Response(JSON.stringify([{ id: 1, name: "x" }]), {
          status: 201,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }
    return Promise.resolve(
      new Response(JSON.stringify([{ id: 1, name: "x" }]), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  }
  if (url.includes("/storage/v1/")) {
    return Promise.resolve(
      new Response(JSON.stringify({ Key: "ok" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }),
    );
  }
  return Promise.resolve(new Response("not found", { status: 404 }));
}

assert.throws(() => createClient("", "k"), /url/);
assert.throws(() => createClient("http://x", ""), /key/);

const client = createClient("http://127.0.0.1:54321/", "anon", { fetch: mockFetch });

assert.equal(typeof client.from, "function");
assert.equal(typeof client.auth.signUp, "function");
assert.equal(typeof client.auth.signIn, "function");
assert.equal(typeof client.storage.from, "function");

const sel = await client.from("parity_items").select().eq("name", "x").limit(1);
assert.equal(sel.error, null);
assert.ok(Array.isArray(sel.data));
assert.ok(calls.some((c) => c.url.includes("/rest/v1/parity_items") && c.url.includes("name=eq.x")));

const ins = await client.from("parity_items").insert({ name: "x" });
assert.equal(ins.error, null);
assert.ok(calls.some((c) => c.method === "POST" && c.url.includes("/rest/v1/parity_items")));

const up = await client.auth.signUp({ email: "a@b.c", password: "secret" });
assert.equal(up.error, null);
assert.ok(calls.some((c) => c.url.endsWith("/v1/auth/signup")));

const inn = await client.auth.signIn({ email: "a@b.c", password: "secret" });
assert.equal(inn.error, null);
assert.ok(calls.some((c) => c.url.endsWith("/v1/auth/login")));

const stor = await client.storage.from("avatars").upload("u/1.png", "bytes");
assert.equal(stor.error, null);
assert.ok(calls.some((c) => c.url.includes("/storage/v1/object/avatars/u/1.png")));

console.log("sdk smoke ok");
