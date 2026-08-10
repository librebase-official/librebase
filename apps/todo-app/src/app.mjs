/**
 * Todo app core — auth + todos against a Librebase project API.
 *
 * Uses @librebase/librebase (supabase-js-shaped) client. The API URL and anon
 * key come from the environment so the same code runs against any instance.
 */

import { createClient } from "@librebase/librebase";

/**
 * @param {string} apiUrl  e.g. http://127.0.0.1:54321
 * @param {string} anonKey  project anon/publishable key
 * @param {{ fetch?: typeof fetch }} [options]
 */
export function createTodoApp(apiUrl, anonKey, options = {}) {
  if (!apiUrl) throw new Error("createTodoApp: apiUrl is required");
  if (!anonKey) throw new Error("createTodoApp: anonKey is required");

  const client = createClient(apiUrl, anonKey, options);

  return {
    apiUrl,
    client,
    auth: {
      async signUp(email, password) {
        const res = await client.auth.signUp({ email, password });
        if (res.error) throw toAppError("signup", res.error);
        return { user: res.data?.user ?? res.data, session: res.data };
      },
      async signIn(email, password) {
        const res = await client.auth.signInWithPassword({ email, password });
        if (res.error) throw toAppError("signin", res.error);
        return { user: res.data?.user ?? res.data, session: res.data };
      },
      async signOut() {
        await client.auth.signOut();
      },
    },
    todos: {
      async create(title) {
        if (!title || !String(title).trim()) {
          throw new Error("todos.create: title is required");
        }
        const res = await client
          .from("todos")
          .insert({ title: String(title).trim(), done: false });
        if (res.error) throw toAppError("todos.create", res.error);
        return firstRow(res);
      },
      async list() {
        const res = await client.from("todos").select("*").limit(100);
        if (res.error) throw toAppError("todos.list", res.error);
        return Array.isArray(res.data) ? res.data : [];
      },
      async complete(id) {
        const res = await client
          .from("todos")
          .update({ done: true })
          .eq("id", id);
        if (res.error) throw toAppError("todos.complete", res.error);
        return firstRow(res);
      },
      async remove(id) {
        const res = await client.from("todos").delete().eq("id", id);
        if (res.error) throw toAppError("todos.remove", res.error);
        return res.data ?? { deleted: true };
      },
    },
  };
}

function firstRow(res) {
  if (Array.isArray(res.data)) return res.data[0] ?? null;
  if (res.data && typeof res.data === "object") return res.data;
  return null;
}

function toAppError(op, err) {
  const e = new Error(`${op}: ${err?.message ?? String(err)}`);
  e.status = err?.status;
  e.operation = op;
  return e;
}
