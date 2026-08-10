/**
 * Todo app live test — requires a running Librebase project API on :54321
 * (lis librebase profile) with a `todos` migration applied.
 *
 * Run: LIBREBASE_API=http://127.0.0.1:54321 node test/live.mjs
 * Skips (exit 0) when the API is unreachable so offline CI stays green.
 */
import assert from "node:assert/strict";
import { createTodoApp } from "../src/app.mjs";

const API = (process.env.LIBREBASE_API ?? "http://127.0.0.1:54321").replace(/\/$/, "");
const ANON = process.env.LIBREBASE_ANON ?? "anon";
const EMAIL = process.env.TODO_LIVE_EMAIL ?? `live-${Date.now()}@example.com`;
const PASSWORD = process.env.TODO_LIVE_PASSWORD ?? "live-secret-change-me";

async function apiUp() {
  try {
    const res = await fetch(`${API}/rest/v1/todos?limit=1`);
    return true;
  } catch {
    return false;
  }
}

export async function run() {
  if (!(await apiUp())) {
    console.log(`todo-app live: SKIPPED (no API at ${API})`);
    return;
  }

  const app = createTodoApp(API, ANON);

  // auth
  const { user } = await app.auth.signUp(EMAIL, PASSWORD);
  assert.ok(user?.id, "live signup returns user");
  await app.auth.signIn(EMAIL, PASSWORD);

  // CRUD
  const created = await app.todos.create("live test todo");
  assert.ok(created.id, "live create returns id");
  const list = await app.todos.list();
  assert.ok(list.some((t) => t.id === created.id), "live list contains created");
  const done = await app.todos.complete(created.id);
  assert.equal(done.done, true, "live complete flips done");
  await app.todos.remove(created.id);
  const after = await app.todos.list();
  assert.ok(!after.some((t) => t.id === created.id), "live delete removes");

  console.log("todo-app live ok: signup→signin→create→list→complete→delete");
}

if (process.argv[1] === new URL(import.meta.url).pathname) {
  run().then(() => process.exit(0)).catch((e) => { console.error(e); process.exit(1); });
}
