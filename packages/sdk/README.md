# `@librebase/librebase`

Minimal **supabase-js-shaped** client for Librebase / lis.

Calls:

| Surface | Path |
|---------|------|
| REST | `/rest/v1/{table}` |
| Auth | `/v1/auth/signup`, `/v1/auth/login` |
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
