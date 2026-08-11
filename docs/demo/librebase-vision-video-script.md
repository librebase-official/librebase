# Librebase demo video — "Supabase's vision, without the cost or the wait"

Covers Supabase's own vision (from their positioning): sub-second provisioning, a
footprint small enough for a sandbox, and an upgrade path to full Supabase. The
benchmark shows Librebase delivering all of it — compared head-to-head against
**Supabase (full)** and **Supabase Light** (minimal db+auth+rest).

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

*[Screen record: the @librebase/librebase client (supabase-js-shaped) doing
`signUp`, `signInWithPassword`, `from("items").insert().select().eq()`]*

**VO:** "The whole point is drop-in. Our client is supabase-js-shaped —
`createClient(url, key)`, `auth.signUp`, `auth.signInWithPassword`,
`from("todos").insert(...).select("*").eq(...)`. Signup, login, insert, query —
the same calls your app already makes. Point it at Librebase and it just works,
with an upgrade path to full Supabase when the app graduates to production."

**On screen:** live REPL showing signUp → signInWithPassword → insert → select → rows.

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

**VO (honest, small):** "Supabase Realtime event-delivery and Storage bucket ops
are still behind full-Supabase bootstrap; update-by-filter needs one more SDK
tweak. The footprint and provisioning claims above are measured, not marketed."

---

## Production notes

- Record the three-stack comparison live: `podman images`, `podman stats --no-stream`,
  timed cold starts.
- Use the supabase-js-shaped client demo (`createClient` + auth + CRUD) against
  Librebase.
- Show the `benchmarks/full-stack/` results (ingest-index, realtime, vector).
- Honesty rule: show measured numbers; don't claim Realtime/Storage parity yet.
- Output: `docs/demo/librebase-vision-benchmark.mp4` (ffmpeg, 1080p).
