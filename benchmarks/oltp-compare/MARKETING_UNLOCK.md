# Marketing unlock checklist (P6)

**Status: LOCKED** — do **not** ship “as fast as Supabase”, “on par with Supabase”, or measured **64 MB** steady-state claims until every **required** row below is green.

North-star thresholds (engineering aims until then):

| Metric | Target |
|--------|--------|
| Core-path P95 | ≤ **1.2×** Postgres 16 on same hardware (`ratio_vs_postgres_p95 ≤ 1.2`) |
| Librebase-lean RSS | ≤ **64 MB** steady (lidb PH-DB-7) |
| Throughput | Competitive indexed read+write ops/sec (report + soft gate first) |

Honesty rule: harness code and MRs are **not** a marketing unlock. Cite only committed / CI-published **PASS** (not skip) artifacts.

Related: [README.md](README.md) · [capability matrix](../../docs/lidb-capability-matrix.md) · [blog draft 05](../../docs/blog/drafts/05-low-memory-database.md) · landing FAQ (`data-studio-ui` “How much memory…”)

---

## Unlock checklist

| # | Gate | Status | Evidence |
|---|------|--------|----------|
| 1 | Nightly CI **PASS** (not skip) for gated SQL scenarios ≥ **3 consecutive** days | **pending** | Workflow [`.github/workflows/oltp-compare.yml`](../../.github/workflows/oltp-compare.yml) + gate harness shipped in librebase `0bcf838` (`feat/deepen-phase1-auth-storage-mcp` / PR lineage). No committed multi-day green trail yet. Prefer [`results/ci-latest.json`](results/ci-latest.json) once a nightly bot lands — **placeholder only today**. |
| 2 | PH-DB-7 lean RSS **green** **or** marketing still says “**64 MB aim**” | **partial** | **Honesty path done:** blog / landing / matrix / product rule keep **aim/target** language. **Measured 64 MB unlock pending:** lidb PH-DB-7 MR [!5](https://gitlab.lilangverse.xyz/li-langverse/lidb/-/merge_requests/5) — not yet a librebase-cited green CI row. Until then copy must say **aim**, never measured MB. |
| 3 | Indexed claim either **btree/sorted_tree-gated** CI green **or** explicit “hash / sorted microbench” footnote forever | **partial** | lidb sorted_tree `d7f5cb5` + librebase detect `3b9329e` (PR [#21](https://github.com/librebase-official/librebase/pull/21)). Harness records `index_impl`. **`range_scan_name_prefix` still diagnostic** — not gated. Marketing must not claim indexed Supabase-class parity; label microbench / `sorted_tree` (not disk B-tree) until CI greens promote range + indexed gates. |
| 4 | Optional: HTTP REST soft-green published | **pending** | Suite + soft gate `c64e50f` (`run_http_compare.py` / `check_http_gate.py`). Soft-skips until live **lis + PostgREST** on the runner. No published soft-green artifact for claims. |
| 5 | Capability matrix / blog / landing honesty lines remain “aim” until 1–3 unlock | **done** | Matrix: no “as fast as Supabase” without CI OLTP ratios. Blog `05-low-memory-database.md`: **aims** / engineering targets. Landing proof + FAQ: **aim** / **target until published benches are green**. |

### Required vs optional

- **Required for any “on par / as fast as Supabase” copy:** items **1**, **2** (measured RSS **or** keep aim-only forever for RAM), **3** (gated green **or** permanent index-honesty footnote), **5**.
- **Optional product-path claim** (REST vs PostgREST): item **4** — separate from embed SQL green.

---

## Phase evidence map (shipped work ≠ unlock)

| Phase | What landed | Librebase / lidb refs | Unlocks marketing? |
|-------|-------------|----------------------|--------------------|
| P0–P2 | Modes, core scenarios, `check_gate.py`, CI wire | `0bcf838`+ on `feat/deepen-phase1-auth-storage-mcp` | **No** — need consecutive nightly PASS |
| P3 | HTTP soft-compare | `c64e50f` | **No** — soft-skip until live stack |
| P4 | PH-DB-7 lean RSS + P95/ops in lidb | [lidb MR !5](https://gitlab.lilangverse.xyz/li-langverse/lidb/-/merge_requests/5) | **No** until green CI cited here |
| P5 | sorted_tree + `index_impl` detect | lidb `d7f5cb5`; librebase `3b9329e` / PR #21 | **No** — range_scan still diagnostic |
| P6 | This checklist + aim language | this file | **Unlock doc only** — claims stay locked |

---

## Still blocking a real marketing unlock

1. **No multi-day nightly PASS trail** committed (or bot-PR’d) for gated SQL (`point_lookup_with_index` ≤ 1.2×).
2. **PH-DB-7** lean RSS not yet a citable green gate in product docs (keep **64 MB aim**).
3. **Indexed path** not marketing-ready: sorted_tree helps honesty, but range_scan ungated and no “Supabase-class indexed” claim without CI + clear index footnote.
4. **HTTP REST** compare not soft-green in CI (live lis + PostgREST still required).

When all required rows flip to **done**, update this file’s top **Status** to `UNLOCKED`, link the three green CI days (or `ci-latest.json` SHAs), then refresh landing / blog / matrix in a dedicated copy PR.

---

## How to flip a row to done

| Row | Done means |
|-----|------------|
| 1 | Three scheduled `oltp-compare` runs with `skipped` false, gate exit 0; preferably bot commits updating `results/ci-latest.json` |
| 2 | lidb PH-DB-7 CI fails above 64 MB lean RSS **and** a green run is linked here — **or** deliberately keep forever “64 MB aim” and never claim measured MB |
| 3 | Gated CI green with `index_impl` ∈ {`sorted_tree`,`btree`} **and** (optional) `range_scan` promoted — **or** permanent marketing footnote: hash/sorted microbench only |
| 4 | Soft-green HTTP artifact published (not soft-skip); hard-gate only after two stable nights per plan |
| 5 | Re-audit landing / matrix / blog on the unlock PR — still no invented numbers |
