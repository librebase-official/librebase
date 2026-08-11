# Librebase demo video — "Supabase's vision, without the cost or the wait"

Covers Supabase's own vision (from their positioning): sub-second provisioning, a
footprint small enough for a sandbox, and an upgrade path to full Supabase. The
benchmark shows Librebase delivering all of it — compared head-to-head against
**Supabase (full)** and **Supabase Light** (minimal db+auth+rest).

**Record tooling:** `scripts/record-vision-demo.sh` (health-checks + seeds the
three backends, prints capture commands) and `demo-storyboard.html` (clickable
beat board that opens the quoted result files).

## Record today in under 20 minutes

| Step | Time | Action |
|------|------|--------|
| 1 | 3 min | `./scripts/record-vision-demo.sh` (bring up lis/Supalite/Supabase full first; script health-checks + seeds) |
| 2 | 1 min | Open `docs/demo/demo-storyboard.html` in a browser; set display zoom 100%, dark room, hide notifications |
| 3 | 12–15 min | One take following the beats below; pause ≤2 s on each table |
| 4 | 2 min | Optional trim in QuickTime or `ffmpeg` (commands printed by the script) |

---

## 0:00–0:15 — Hook: the vision, stated back

*[Split screen: Supabase logo fades to Librebase; text: "sub-second provisioning",
"runs in a sandbox", "upgrade path to Supabase"]*

**VO:** "Supabase built the vision: a PostgREST and Auth compatible API that
applications written against `@supabase/supabase-js` use as-is — interchangeable
on Postgres, upgradable to the full platform. The missing piece? The cost and the
wait. A database you can give to every prototype. That's what Librebase delivers."

**On screen:** the exact Supabase vision bullet points.

---

## 0:15–0:35 — The footprint gap: three stacks, one table

*[Screen record: `podman images` + `podman stats` on all three]*

**VO:** "Let's measure the whole vision. Same Mac, same podman, same `items` table.
Full Supabase: twelve containers, seven and a half gigabytes of images, almost
**two gigabytes of RAM** just sitting idle. Supabase Light — just Postgres, Auth,
and REST: still two and a half gigabytes of images, a hundred and forty megabytes
of RAM. And Librebase: **one container, 8 megabytes, about 2 megabytes resident**."

**On screen:**

| | Images | RAM idle | Containers |
|---|---|---|---|
| Supabase (full) | ~7.5 GB | ~1.85 GB | 12 |
| Supabase Light | ~2.3 GB | ~140 MB | 3 |
| **Librebase** | **8.2 MB** | **~2 MB** | **1** |

---

## 0:35–0:55 — Sub-second provisioning: cold start to ready

*[Screen record: timed `podman run` + `curl /health` on Librebase, then a stop/start on Supabase]*

**VO:** "Provisioning is the wait. Librebase cold-starts to a healthy, queryable
database in about a **quarter of a second**. Supabase Light takes near half a
second just to bring REST and Auth back; a full cold start of the whole stack is
measured in seconds. Sub-second provisioning — that's Librebase, today."

**On screen:** `librebase-tiny cold start: 265ms` vs `supabase-light: 442ms`.

---

## 0:55–1:20 — supabase-js compatibility: your app works as-is

*[Screen record: the official `@supabase/postgrest-js` test suite running
against Librebase, then the same suite against Supabase full]*

**VO:** "The whole point is drop-in. We run the **official** PostgREST test
suite — the same `@supabase/postgrest-js` tests the Supabase team ships —
against Librebase and Supabase full, as-is, no client shims. On the core Data
API, Librebase passes **111 of 111 — identical to Supabase full**. Across the
whole suite, Librebase passes 274 of 350; the rest are Postgres-native features
like stored functions and `explain` that an in-memory engine doesn't execute."

**On screen:**

| | official postgrest-js suite | core Data API |
|---|---|---|
| Supabase full (Kong + Postgres) | 350/350 | 111/111 |
| **Librebase (lis)** | **274/350** | **111/111 (= reference)** |

**VO (honest):** "The comparison is tiered: in-memory versus in-memory,
on-disk versus on-disk. Librebase's in-memory tier matches the reference on
everything that doesn't need Postgres SQL functions."

---

## 1:20–1:45 — And the data plane isn't a toy

*[Cut to the CRUD benchmark table from benchmarks/full-stack/]*

**VO:** "Lean doesn't mean slow. In our 50k-row index benchmark, Librebase's
indexed point lookup is **0.04 milliseconds** at the session protocol — versus
about 3 milliseconds through Supabase's full stack on the same machine. Range
queries, paging, bulk ingest — all in the same ballpark or faster, at 1/200th
the footprint."

**On screen:** lookup p50 table: Supabase ~3ms vs Librebase 0.04ms.

---

## 1:45–2:00 — The vision, delivered + honest gaps

*[Librebase logo + one line]*

**VO:** "Sub-second provisioning. Sandbox-sized footprint. A PostgREST and Auth
compatible API your supabase-js app already speaks. And when you graduate to
production, full Supabase is the upgrade path — Librebase is the fastest way to
get there. Run it on every prototype. Give it to every AI builder."

**VO (honest, small):** "Realtime REST→WS event delivery is measured (p50 ≈ 50 ms,
60/60 delivered). Supabase-side Realtime delivery and Storage bucket ops are blocked
by self-host bootstrap config on our bench box. Footprint, provisioning, and speed
claims are measured, not marketed."

---

## Production notes

- **Storyboard:** `docs/demo/demo-storyboard.html` — clickable beat board; links
  open the result JSONs each beat quotes.
- **Socials cut:** `docs/demo/socials/` — rendered 26 s, 9:16 HyperFrames
  composition (`librebase-socials.mp4`): hook → footprint → provisioning →
  compat → outro with wordmark lockup. Render with `npx hyperframes render`.
- Record the three-stack comparison live: `podman images`, `podman stats --no-stream`,
  timed cold starts.
- Use the supabase-js-shaped client demo (`createClient` + auth + CRUD) against
  Librebase.
- Show the `benchmarks/full-stack/` results (ingest-index, realtime, vector).
- **Compat beat:** run the official suite with `run-suite.sh` (see
  `benchmarks/full-stack/postgrest-js-suite/README.md`): Librebase at
  `REST_URL=http://127.0.0.1:54325/rest/v1`, Supabase full with the Kong anon key.
- Honesty rule: show measured numbers only. Realtime REST→WS delivery is measured
  (lis); Supabase-side Realtime/Storage gaps are bootstrap-blocked on the bench box.
- Output: `docs/demo/librebase-vision-benchmark.mp4` (ffmpeg, 1080p).
