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
    if (init.method === "PATCH" || init.method === "DELETE") {
      return Promise.resolve(
        new Response(JSON.stringify({ id: 1, done: true }), {
          status: 200,
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

const upd = await client.from("parity_items").update({ done: true }).eq("id", "abc");
assert.equal(upd.error, null, JSON.stringify(upd.error));
assert.ok(
  calls.some((c) => c.method === "PATCH" && c.url.includes("/rest/v1/parity_items") && c.url.includes("id=eq.abc")),
  `expected PATCH /rest/v1/parity_items?id=eq.abc got ${calls.map((c) => `${c.method} ${c.url}`).join(", ")}`,
);

const del = await client.from("parity_items").delete().eq("id", "abc");
assert.equal(del.error, null, JSON.stringify(del.error));
assert.ok(
  calls.some((c) => c.method === "DELETE" && c.url.includes("/rest/v1/parity_items") && c.url.includes("id=eq.abc")),
  `expected DELETE /rest/v1/parity_items?id=eq.abc`,
);

const updNonId = await client.from("parity_items").update({ done: true }).eq("code", "v1");
assert.equal(updNonId.error, null, JSON.stringify(updNonId.error));
assert.ok(
  calls.some((c) => c.method === "PATCH" && c.url.includes("/rest/v1/parity_items") && c.url.includes("code=eq.v1")),
  `expected PATCH /rest/v1/parity_items?code=eq.v1 (non-id filter)`,
);

const delNonId = await client.from("parity_items").delete().eq("code", "v1");
assert.equal(delNonId.error, null, JSON.stringify(delNonId.error));
assert.ok(
  calls.some((c) => c.method === "DELETE" && c.url.includes("/rest/v1/parity_items") && c.url.includes("code=eq.v1")),
  `expected DELETE /rest/v1/parity_items?code=eq.v1 (non-id filter)`,
);

const updNoId = await client.from("parity_items").update({ done: true });
assert.ok(updNoId.error, "update without filter should error");
assert.match(String(updNoId.error.message), /filter/);

// Filter operator coverage — each must emit the PostgREST form `col=op.value`
const ops = [
  ["eq", "name", "x", "name=eq.x"],
  ["neq", "name", "x", "name=neq.x"],
  ["gt", "age", 18, "age=gt.18"],
  ["gte", "age", 18, "age=gte.18"],
  ["lt", "age", 18, "age=lt.18"],
  ["lte", "age", 18, "age=lte.18"],
  ["in", "code", ["a", "b"], "code=in.(a,b)"],
  ["like", "name", "%x%", "name=like.%25x%25"],
  ["ilike", "name", "%X%", "name=ilike.%25X%25"],
  ["is", "deleted", "null", "deleted=is.null"],
];
for (const [fn, col, arg, expect] of ops) {
  calls.length = 0;
  await client.from("parity_items").select()[fn](col, arg);
  const hit = calls.some((c) => c.url.includes(`/rest/v1/parity_items`) && c.url.includes(expect));
  assert.ok(hit, `expected ${fn} to emit ?${expect} got ${calls.map((c) => c.url).join(", ")}`);
}

// update() with a non-eq operator still works (filters address the rows)
calls.length = 0;
await client.from("parity_items").update({ seen: true }).gt("age", 21);
assert.ok(
  calls.some((c) => c.method === "PATCH" && c.url.includes("age=gt.21")),
  `expected PATCH with gt filter`,
);

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
