/**
 * Supabase todo-app E2E — full HTTP surface against a real Supabase backend.
 * Skips (exit 0) if env keys are absent.
 */
import assert from "node:assert/strict";

const API = (process.env.LIBREBASE_API ?? "https://supabase.obsevia.com").replace(/\/$/, "");
const ANON = process.env.LIBREBASE_ANON ?? "";
const SR = process.env.LIBREBASE_SERVICE_ROLE ?? "";
const EMAIL = `e2e-sb-${Date.now()}@example.com`;
const PW = "secret-pass";

const h = (token, extra = {}) => ({ apikey: ANON, Authorization: `Bearer ${token}`, "Content-Type": "application/json", ...extra });

async function run() {
  if (!ANON || !SR) {
    console.log("supabase e2e: SKIPPED (set LIBREBASE_ANON + LIBREBASE_SERVICE_ROLE)");
    return;
  }

  // create confirmed user
  const cu = await fetch(`${API}/auth/v1/admin/users`, {
    method: "POST", headers: h(SR), body: JSON.stringify({ email: EMAIL, password: PW, email_confirm: true }),
  });
  assert.equal(cu.status, 200, `admin create user: ${cu.status}`);
  await cu.json();

  // sign in
  const si = await fetch(`${API}/auth/v1/token?grant_type=password`, {
    method: "POST", headers: h(ANON), body: JSON.stringify({ email: EMAIL, password: PW }),
  });
  assert.equal(si.status, 200, `signin: ${si.status}`);
  const token = (await si.json()).access_token;
  assert.ok(token, "signin returns access_token");
  const sub = JSON.parse(Buffer.from(token.split(".")[1], "base64url").toString()).sub;

  // create
  const create = await fetch(`${API}/rest/v1/todos`, {
    method: "POST", headers: { ...h(token), Prefer: "return=representation" },
    body: JSON.stringify({ title: "e2e supabase", done: false, user_id: sub }),
  });
  assert.equal(create.status, 201, `create: ${create.status}`);
  const created = (await create.json())[0];
  assert.ok(created.id, "created has id");

  // list
  const list = await fetch(`${API}/rest/v1/todos?select=*`, { headers: h(token) });
  assert.equal(list.status, 200, `list: ${list.status}`);
  const rows = await list.json();
  assert.ok(rows.some((r) => r.id === created.id), "created todo listed");

  // update
  const upd = await fetch(`${API}/rest/v1/todos?id=eq.${created.id}`, {
    method: "PATCH", headers: { ...h(token), Prefer: "return=representation" },
    body: JSON.stringify({ done: true }),
  });
  assert.equal(upd.status, 200, `update: ${upd.status}`);
  assert.equal((await upd.json())[0].done, true, "updated done=true");

  // delete
  const del = await fetch(`${API}/rest/v1/todos?id=eq.${created.id}`, { method: "DELETE", headers: h(token) });
  assert.equal(del.status, 204, `delete: ${del.status}`);

  // RLS guard: anon token (no user) sees zero rows for owned table
  const guard = await fetch(`${API}/rest/v1/todos?select=*`, { headers: { apikey: ANON, Authorization: `Bearer ${ANON}` } });
  assert.equal(guard.status, 200, `anon list: ${guard.status}`);
  const anonRows = await guard.json();
  assert.ok(Array.isArray(anonRows) && anonRows.length === 0, "anon sees no rows (RLS)");

  console.log("supabase e2e ok: admin-user -> signin -> create -> list -> update -> delete -> auth guard");
}

if (process.argv[1] === new URL(import.meta.url).pathname) {
  run().then(() => process.exit(0)).catch((e) => { console.error(e); process.exit(1); });
}
