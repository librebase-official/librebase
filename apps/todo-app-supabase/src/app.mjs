/**
 * Todo app core on Supabase — auth + todos against a real Supabase project.
 *
 * Env:
 *   LIBREBASE_API       Supabase project URL (default https://supabase.obsevia.com)
 *   LIBREBASE_ANON      Supabase anon/publishable key (required)
 *   LIBREBASE_SERVICE_ROLE  service_role key (used only to create confirmed bench users)
 */
import { createClient } from "@librebase/librebase";

export function createSupabaseTodoApp(apiUrl, anonKey, options = {}) {
  if (!apiUrl) throw new Error("createSupabaseTodoApp: apiUrl is required");
  if (!anonKey) throw new Error("createSupabaseTodoApp: anonKey is required");

  // supabase-js-shaped client pointed at Supabase's GoTrue + PostgREST.
  const client = createClient(apiUrl, anonKey, {
    fetch: options.fetch,
    // supabase-js-style: use GoTrue /auth/v1/* aliases
  });
  process.env.LIBREBASE_AUTH_GOTRUE = "1";

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
      async create(title, userId) {
        if (!title || !String(title).trim()) throw new Error("todos.create: title is required");
        const res = await client
          .from("todos")
          .insert({ title: String(title).trim(), done: false, user_id: userId });
        if (res.error) throw toAppError("todos.create", res.error);
        return firstRow(res);
      },
      async list() {
        const res = await client.from("todos").select("*").limit(100);
        if (res.error) throw toAppError("todos.list", res.error);
        return Array.isArray(res.data) ? res.data : [];
      },
      async complete(id) {
        const res = await client.from("todos").update({ done: true }).eq("id", id);
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
