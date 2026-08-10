# Todo app CRUD benchmark — Supabase vs Librebase/lis

Same todo app (auth + todos CRUD) measured head-to-head on two backends.
Both runs: **60 rounds × 4 ops (create / list / update / delete) = 240 HTTP responses**.

## Results

| Backend | Total | Ops/sec | create p50 | list p50 | update p50 | delete p50 | p95 (all) |
|---------|-------|---------|-----------|----------|------------|-----------|-----------|
| **Supabase** (`supabase.obsevia.com`, remote HTTPS) | 74.8 s | **3** | 239 ms | 246 ms | 245 ms | 257 ms | ~1.0 s |
| **Librebase lis** (local, in-process) | 0.36 s | **677** | 1.6 ms | 1.3 ms | 1.4 ms | 1.2 ms | ~4 ms |

**~225× more ops/sec on lis than the remote Supabase** in this run.

## Caveats (honest)

- **Not apples-to-apples on transport:** Supabase runs on a remote host over public
  HTTPS (TLS + Kong proxy + PostgREST + Postgres on one VPS/cluster, WAN round-trips);
  lis runs locally in-process with mock auth + in-memory store. The lis number is a
  **local** upper bound, not a same-host comparison.
- Supabase per-op p50 ≈ 240 ms is dominated by network RTT + Kong proxy latency
  (`x-kong-proxy-latency` ~2.2 s was seen on first signin; steady-state lower).
- The lis backend stores todos in-memory (non-durable); Supabase persists to Postgres
  with RLS. Durability ≠ speed.
- To do a fair same-host comparison, deploy Supabase on the same machine/LAN and run
  the same harness against `http://<host>:8000` (Kong) instead of the public URL.

## How to run

### Supabase
```bash
cd apps/todo-app-supabase
LIBREBASE_ANON=<anon> LIBREBASE_SERVICE_ROLE=<service_role> \
  node test/e2e-supabase.mjs        # functional e2e
LIBREBASE_ANON=<anon> LIBREBASE_SERVICE_ROLE=<service_role> \
  BENCH_ROUNDS=60 node test/bench-crud.mjs   # 240-response latency
```

Requires a `todos` table with RLS:
```sql
CREATE TABLE IF NOT EXISTS todos (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null, title text not null,
  done boolean default false, created_at timestamptz default now());
ALTER TABLE todos ENABLE ROW LEVEL SECURITY;
CREATE POLICY todos_owner ON todos FOR ALL
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
```

### Librebase lis
```bash
cd apps/todo-app
LIS_ROOT=<lis> node test/bench-crud.mjs   # same 60×4 measurement, local stack
```
