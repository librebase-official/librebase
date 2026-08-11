# `@librebase/librebase`

Minimal **supabase-js-shaped** client for Librebase / lis.

Calls:

| Surface | Path |
|---------|------|
| REST | `/rest/v1/{table}` |
| Auth | `/v1/auth/*` or `/auth/v1/*` (set `LIBREBASE_AUTH_GOTRUE=1`) |
| Storage (stub) | `/storage/v1/object/...` |

## Install

```bash
npm install @librebase/librebase
```

## Usage

```js
import { createClient } from "@librebase/librebase";

const librebase = createClient("http://127.0.0.1:54321", "anon-key");

const { data, error } = await librebase.from("parity_items").select().eq("name", "demo");

// Update/delete by any filter column (id, code, name, ...) — PostgREST form:
await librebase.from("parity_items").update({ done: true }).eq("code", "v1");
await librebase.from("parity_items").delete().eq("code", "v1");

// Filter operators (PostgREST form, all usable on select/update/delete):
// eq neq gt gte lt lte in like ilike is
const adults = await librebase.from("users").select().gte("age", 21).like("name", "%an%");
await librebase.from("parity_items").update({ seen: true }).gt("age", 21);

await librebase.auth.signUp({ email: "a@b.c", password: "secret" });
await librebase.auth.signIn({ email: "a@b.c", password: "secret" });

// Storage stubs (Wave B — may 404 until lis Storage is wired)
await librebase.storage.from("avatars").upload("user/1.png", bytes);
```

## Status

Scaffold for Wave B. REST + Auth match Wave A lis contracts; Storage methods are stubs that hit `/storage/v1` and return honest errors until object storage lands.

## Test

```bash
npm test
```
