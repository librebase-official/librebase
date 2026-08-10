# Todo app CRUD benchmark — Supabase vs Librebase/lis (both REMOTE)

Same todo app (auth + todos CRUD), measured head-to-head. Both backends run on the
**same homelab k3s cluster** and are reached over the **same public HTTPS path**
(FritzBox → nginx → NodePort), so the network is apples-to-apples.

Each run: **60 rounds × 4 ops (create / list / update / delete) = 240 HTTP responses**,
after a warmup cycle (TLS + connection pooling to steady state).

## Results (3 runs each)

| Backend | ops/s | create p50 | list p50 | update p50 | delete p50 |
|---------|-------|-----------|----------|------------|-----------|
| **Librebase lis** (`todo.librebase.xyz`) | 33–38 | 23–30 ms | 22–27 ms | 23–28 ms | 25–27 ms |
| **Supabase** (`supabase.obsevia.com`) | 38–42 | 21–22 ms | 19–22 ms | 21–22 ms | 21 ms |

**Statistically equivalent.** Both sustain ~35–42 ops/s over public HTTPS with
~20–27 ms p50 per operation. Supabase is marginally faster per-op in these runs
(within noise).

## Why the earlier "225×" was wrong

An earlier local-vs-remote comparison showed lis at 677 ops/s vs Supabase at 3 ops/s.
That was **not a real difference**:
- lis ran **locally in-process** (no network); Supabase was **remote over public HTTPS**.
- Supabase's first run was **cold**: admin user creation + TLS handshake + Kong
  warmup inflated p50 to ~240 ms and the total to 75 s.
- After adding a warmup cycle and measuring **both over the same remote path**, the
  gap vanished (both ~35–42 ops/s).

Lesson: benchmark the same transport. The lis number from a local in-process run is
a local upper bound, not a head-to-head figure.

## Raw numbers (run averages)

- lis remote: total ≈ 6.3–7.4 s / 240 responses, p50 ≈ 25 ms, p95 ≈ 0.3–1.7 s
- supabase remote: total ≈ 5.7–6.2 s / 240 responses, p50 ≈ 21 ms, p95 ≈ 40–90 ms

## How to run

```bash
# lis backend (remote)
cd apps/todo-app
node test/bench-crud-remote.mjs                 # -> https://todo.librebase.xyz

# supabase backend (remote)
cd apps/todo-app-supabase
LIBREBASE_ANON=<anon> LIBREBASE_SERVICE_ROLE=<service_role> \
  node test/bench-crud.mjs                      # -> https://supabase.obsevia.com
```

Both scripts take `BENCH_ROUNDS` (default 60) and warm up before timing.
