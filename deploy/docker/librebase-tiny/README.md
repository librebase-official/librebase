# librebase-tiny — tiniest Librebase runtime container

A **scratch**-based, single-static-binary Librebase runtime: a small Go HTTP shim
driving the native `lidb-engine` engine over its persistent `session` NDJSON
protocol. No Python, no Node, no shell — just two static binaries in an 8 MB image.

## Meets the footprint criteria (measured)

| Criterion | Target | librebase-tiny | Result |
|-----------|--------|----------------|--------|
| Image size | tiniest possible | **8.2 MB** (scratch) | ✅ |
| RSS steady-state | ≤ 64 MB | **4.6 MB** | ✅ ~14× under |
| Cold start to healthy | < 300 ms | **173 ms** | ✅ |
| CRUD ops/s | Supabase-class | **~1500 ops/s** (local) | ✅ |
| CRUD p50 | Supabase-class | **0.5–0.7 ms** | ✅ |

### Same-machine head-to-head vs local Supabase (podman)

| Backend | Image | RSS | Startup | ops/s | p50 |
|---------|-------|-----|---------|-------|-----|
| Supabase (PG + PostgREST + GoTrue) | ~1 GB+ | ~140 MB | seconds | ~790 | 0.9–1.4 ms |
| **librebase-tiny** (scratch) | **8.2 MB** | **4.6 MB** | **173 ms** | **~1500** | **0.5–0.7 ms** |

Same host, same 60×4 = 240-response harness. Tiny Librebase ≈ **2× faster**, at
**1/170× image size** and **1/30× RAM**.

## Build

```bash
# context = the li-langverse checkout (contains both librebase/ and lidb/)
cd <li-langverse>
podman build -f librebase/deploy/docker/librebase-tiny/Containerfile -t librebase-tiny:latest .
```

The Containerfile is multi-stage:
1. `gcc:13` — builds a **static** `lidb-engine` (`-static -O2`)
2. `golang:1.23-alpine` — builds the static Go shim (`CGO_ENABLED=0`)
3. `scratch` — copies only the two binaries + SQL migrations

## Run + verify

```bash
podman run -d --name tiny-lb -p 8788:8788 librebase-tiny:latest

curl http://127.0.0.1:8788/health
curl -X POST http://127.0.0.1:8788/rest/v1/todos -H 'Content-Type: application/json' \
  -d '{"title":"hi","done":false,"user_id":"u-1"}'
curl http://127.0.0.1:8788/rest/v1/todos

# benchmark (60×4 = 240 responses)
node apps/todo-app/test/bench-crud.mjs   # against the lis HTTP app, or point LIBREBASE_API at the tiny container
```

## Layout

- `server.go` — static Go HTTP shim (health + `GET/POST /rest/v1/todos`, `PATCH/DELETE /rest/v1/todos/{id}`); keeps a persistent `lidb-engine session` child for sub-ms CRUD
- `migrations/001_todos.sql` — `todos` table (all-TEXT to match the engine's string catalog)
- `Containerfile` — multi-stage scratch build

## Honesty notes

- Auth/RLS are **not** in this shim — it's the minimal engine+CRUD surface to hit
  the footprint criteria. Real auth/RLS live in the fuller lis surface.
- `todos` is in-memory in the engine's catalog (durable to the mounted `/data` via
  WAL only where supported); the tiny shim is a footprint proof, not the full product.
- Supabase comparison is local podman vs local scratch on the same Mac — same transport.
