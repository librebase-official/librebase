# Marketing unlock checklist (P6)

**Status: LOCKED** — do **not** ship “as fast as Supabase”, “on par with Supabase”, or measured **64 MB** steady-state claims until every **required** row below is green.

North-star thresholds (engineering aims until then):

| Metric | Target |
|--------|--------|
| Core-path P95 | ≤ **1.2×** Postgres 16 on same hardware (`ratio_vs_postgres_p95 ≤ 1.2`) |
| Librebase-lean RSS | ≤ **64 MB** steady (lidb PH-DB-7) |
| Throughput | Competitive indexed read+write ops/sec (report + soft gate first) |

Honesty rule: harness code and MRs are **not** a marketing unlock. Cite only committed / CI-published **PASS** (not skip) artifacts.

Related: [README.md](README.md) · [capability matrix](../../docs/lidb-capability-matrix.md) · [blog draft 05](../../docs/blog/drafts/05-low-memory-database.md) · landing FAQ (`data-studio-ui` “How much memory…”)

---

## Unlock checklist

| # | Gate | Status | Evidence |
|---|------|--------|----------|
| 1 | Nightly CI **PASS** (not skip) for **core** gated SQL scenarios ≥ **3 consecutive** days | **pending** | Session subprocess reuse (`c5cc283`) fixed per-query spawn overhead. Local measured run 2026-08-05: **core gate PASS** (`point_lookup_with_index` **0.44–0.52×** vs Postgres P95). [`results/ci-latest.json`](results/ci-latest.json) + [`results/latest.json`](results/latest.json). Nightly now hard-gates `--scenarios core` only; **no** 3-night green streak yet. |
| 2 | PH-DB-7 lean RSS **green** **or** marketing still says “**64 MB aim**” | **partial** | **Honesty path done:** blog / landing / matrix / product rule keep **aim/target** language. **Measured 64 MB unlock pending:** lidb PH-DB-7 @ `e731661` ([MR !5](https://gitlab.lilangverse.xyz/li-langverse/lidb/-/merge_requests/5)) cited in [`docs/li-dependency-pins.md`](../../docs/li-dependency-pins.md); Linux RSS gate not green in librebase CI yet. |
| 3 | Indexed claim either **sorted_tree-gated** CI green **or** explicit “hash / sorted microbench” footnote forever | **partial** | lidb sorted_tree `d7f5cb5` ([MR !6](https://gitlab.lilangverse.xyz/li-langverse/lidb/-/merge_requests/6)) pinned for OLTP CI. **Core** indexed point lookup **PASS** (0.44–0.52×). `range_scan_name_prefix` still **2.28×** (sorted_tree LIKE perf, not spawn) — **diagnostic** until ≤ 1.2×. Marketing must label **sorted_tree** (in-memory ordered map, **not** disk B-tree). |
| 4 | Optional: HTTP REST soft-green published | **partial** | Live stack measured 2026-08-05: [`results/http-latest.json`](results/http-latest.json) **not skipped** — GET **3.82×**, POST **4.07×** PostgREST P95 (soft **WARN**, threshold 1.2). CI job can start lis + PostgREST when `run_http=true`. |
| 5 | Capability matrix / blog / landing honesty lines remain “aim” until 1–3 unlock | **done** | Matrix: no “as fast as Supabase” without CI OLTP ratios. Blog `05-low-memory-database.md`: **aims** / engineering targets. Landing proof + FAQ: **aim** / **target until published benches are green**. |

### Required vs optional

- **Required for any “on par / as fast as Supabase” copy:** items **1**, **2** (measured RSS **or** keep aim-only forever for RAM), **3** (core indexed green **or** permanent index-honesty footnote), **5**.
- **Optional product-path claim** (REST vs PostgREST): item **4** — separate from embed SQL green.

---

## Phase evidence map (shipped work ≠ unlock)

| Phase | What landed | Librebase / lidb refs | Unlocks marketing? |
|-------|-------------|----------------------|--------------------|
| P0–P2 | Modes, core scenarios, `check_gate.py`, CI wire | `feat/p5-oltp-index-impl-detect` / PR #21 | **No** — need consecutive nightly PASS on **embed_execjson** core |
| P3 | HTTP soft-compare + CI lis stack bootstrap | `run_http_compare.py`; workflow `run_http=true` | **No** — measured soft breach (~4×) |
| P4 | PH-DB-7 lean RSS + P95/ops in lidb | lidb `e731661` [MR !5](https://gitlab.lilangverse.xyz/li-langverse/lidb/-/merge_requests/5) | **No** until green CI cited |
| P5 | sorted_tree + `index_impl` detect + range_scan diagnostic | lidb `d7f5cb5` [MR !6](https://gitlab.lilangverse.xyz/li-langverse/lidb/-/merge_requests/6); librebase `c5cc283` session reuse | **No** — need 3-night core PASS; range_scan 2.28× still open |
| P6 | This checklist + aim language | this file | **Unlock doc only** — claims stay locked |

---

## Still blocking a real marketing unlock

1. **No multi-day nightly PASS trail** — core gate passes locally after `c5cc283` session reuse (0.44–0.52× point lookup); need 3 consecutive scheduled greens.
2. **PH-DB-7** lean RSS not yet a citable green gate in product docs (keep **64 MB aim**).
3. **Indexed range scan** (`range_scan_name_prefix`) still **2.28×** on sorted_tree — diagnostic, not marketing-unlock until ≤ 1.2×.
4. **HTTP REST** measured but soft-gate breached (~4× PostgREST); not soft-green.

When all required rows flip to **done**, update this file’s top **Status** to `UNLOCKED`, link the three green CI days (or `ci-latest.json` SHAs), then refresh landing / blog / matrix in a dedicated copy PR.

---

## How to flip a row to done

| Row | Done means |
|-----|------------|
| 1 | Three scheduled `oltp-compare` runs with `skipped` false, `mode=embed_execjson`, `--scenarios core`, gate exit 0; preferably bot commits updating `results/ci-latest.json` |
| 2 | lidb PH-DB-7 CI fails above 64 MB lean RSS **and** a green run is linked here — **or** deliberately keep forever “64 MB aim” and never claim measured MB |
| 3 | Core gated CI green (`point_lookup_with_index` ≤ 1.2×) **and** range_scan ≤ 1.2× when promoted from diagnostic — **or** permanent marketing footnote: sorted microbench / point-lookup only |
| 4 | Soft-green HTTP artifact published (max ratio ≤ 1.2, not soft-skip); hard-gate only after two stable nights per plan |
| 5 | Re-audit landing / matrix / blog on the unlock PR — still no invented numbers |
