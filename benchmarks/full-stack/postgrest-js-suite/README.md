# PostgREST-js suite — official @supabase/postgrest-js tests, run as-is

Runs the **real** `@supabase/postgrest-js` test suite (the official Data API spec
tests that ship in the supabase-js monorepo) against Librebase and the other
backends. Same suite, same client, same snapshots (regenerated per backend with
`-u`, exactly like the upstream CI does).

## Tiered methodology (fair comparison)

In-memory and on-disk storage are **different tiers**. Compare only within a
tier; the cross-tier numbers are research inputs for a hybrid design, not
head-to-head wins.

| Tier | Backends | Storage |
|------|----------|---------|
| **In-memory** (volatile, sandbox) | Librebase lis (memory store), in-memory SQLite | process RAM |
| **On-disk** (durable) | Librebase lis + lidb (WAL+heap), SQLite file, Supabase full (Postgres) | disk |

Librebase lis is the API/server (stateless HTTP). The data tier is decided by
what backs it: `_STORE` in-memory dict, or the lidb C++ engine (WAL + heap files
under `.lidb/`). See `lis/routes/rest/handlers.py` + `lidb/engine/`.

## Results (2026-08-11, same Mac, same suite)

Full postgrest-js suite, fresh state + `-u` per backend (upstream CI method):

| Backend | Tier | Full suite | Core Data API (basic + filters) |
|---------|------|-----------|--------------------------------|
| Supabase full (Kong + PostgREST + Postgres) | on-disk | **350/350 (100%)** | 111/111 |
| **Librebase (lis)** | in-memory | **274/350 (78%)** | **111/111 (= reference)** |

The 76 Librebase misses are Postgres-native features an in-memory store does not
execute: RPC/stored functions (37), spread + nested spreads (13), `explain`
(2), self-referencing FK joins (4), and a handful of type-cast / JSON-accessor
queries. All are Postgres-SQL features; the same class Supalite documents as
unsupported/skipped on SQLite.

## What lis implements (added for this suite)

Implemented directly in `lis/routes/rest/handlers.py`:

- Filter operators: `eq neq gt gte lt lte in like ilike is`
- Embedded resources: `relation!hint(cols)`, `alias:relation(cols)`,
  FK-constraint names (`tbl_col_fkey`), cardinality (to-one object vs
  to-many array), nested aggregates (`count/sum/avg`, aliased)
- `single`/`maybeSingle` via `Accept: application/vnd.pgrst.object+json`
  (+ PGRST116 multi-row error)
- `Prefer: count=exact|planned` → `Content-Range` total; HEAD requests
- `Prefer: max-affected` → PGRST124 on update/delete over limit
- `;nulls=stripped` Accept → strip null fields
- bulk insert (array payload), upsert `on_conflict` resolution
- sequential identity ids, unknown-table PGRST205, select projection, order/offset

## Run

```bash
# Librebase (in-memory, lis at :54325)
REST_URL=http://127.0.0.1:54325/rest/v1 SEED=1 ./run-suite.sh -u

# Supabase full (Kong, requires apikey)
REST_URL=http://127.0.0.1:8000/rest/v1 ANON_KEY=<anon> SEED=0 ./run-suite.sh -u
```

Note: the suite mutates data; run from a fresh backend state (restart lis /
`db reset`) and regenerate snapshots (`-u`) per backend, matching upstream CI.
