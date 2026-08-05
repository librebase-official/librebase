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
| 1 | Nightly CI **PASS** (not skip) for **core** gated SQL scenarios ≥ **3 consecutive** days | **done** | **Manual 3-rep streak 2026-08-05** on `feat/p5-oltp-index-impl-detect` @ `8ea71d7`: all 3 reps **PASS** (`embed_execjson`, `core`, lidb `d7f5cb5`). `point_lookup_with_index` ratios **0.186 / 0.196 / 0.251×** (best 0.186, median 0.196). Evidence: [`results/nightly-streak.json`](results/nightly-streak.json), reps [`nightly-rep-1.json`](results/nightly-rep-1.json)–[`nightly-rep-3.json`](results/nightly-rep-3.json), summary [`ci-latest.json`](results/ci-latest.json). Session reuse fix `c5cc283`. Scheduled nightly CI greens still desirable for ongoing regression guard. |
| 2 | PH-DB-7 lean RSS **green** **or** marketing still says “**64 MB aim**” | **done** | **Linux VmRSS CI PASS 2026-08-05:** GitLab pipeline [27003](https://gitlab.lilangverse.xyz/li-langverse/lidb/-/pipelines/27003) / job [99197](https://gitlab.lilangverse.xyz/li-langverse/lidb/-/jobs/99197) on `feat/ph-db-7-librebase-lean-rss` @ `2bfbd3c` (PH-DB-7 gate `e731661` + `.gitlab-ci.yml`). **librebase-lean `rss_mb=3.797`** (`proc_vmrss`, threshold 64) · registry-min **4.859 MB** (threshold 256). Artifacts: [`results/rss-linux-librebase-lean.json`](results/rss-linux-librebase-lean.json), [`results/rss-linux-registry-min.json`](results/rss-linux-registry-min.json), log [`results/rss-gitlab-job-99197.log`](results/rss-gitlab-job-99197.log). Prior Windows advisory 5.621 MB WorkingSet remains non-authoritative. Measured lean RSS claims may cite **3.8 MB** (this green run) — still prefer “≤64 MB” product framing unless a dedicated copy PR refreshes landing/blog. |
| 3 | Indexed claim either **sorted_tree-gated** CI green **or** explicit “hash / sorted microbench” footnote forever | **partial** | lidb sorted_tree + Phase 1 hot path (sorted vector secondary, prefix successor, emit projection). **Core** point lookup **PASS** (~0.20× Release). **Manual 3-rep range_scan Release 2026-08-05:** `range_scan_name_prefix` **0.29–0.37×** (median **0.36×**) — **diagnostic PASS** ≤ 1.2× (was Debug **1.94×**). Evidence: [`results/range-scan-streak.json`](results/range-scan-streak.json), reps [`range-scan-release-rep-1.json`](results/range-scan-release-rep-1.json)–[`range-scan-release-rep-3.json`](results/range-scan-release-rep-3.json). **Not yet** CI hard-gated (promote after 2 consecutive nightly greens). Marketing must label **sorted_tree** (in-memory ordered secondary, **not** disk B-tree). |
| 4 | Optional: HTTP REST soft-green published | **done** (soft) | **Manual 3-rep soft PASS 2026-08-05:** lis embed **pool** + Release `lidb_embed` vs PostgREST — max ratio **0.59–0.75×** (median **0.60×**, threshold 1.2). Evidence: [`results/http-streak.json`](results/http-streak.json), reps [`http-pool-rep-1.json`](results/http-pool-rep-1.json)–[`http-pool-rep-3.json`](results/http-pool-rep-3.json), latest [`results/http-latest.json`](results/http-latest.json). Prior ~4.4× was spawn/Debug tax. Still Python MVP — hard-gate only after 2 stable CI nights. |
| 5 | Capability matrix / blog / landing honesty lines remain “aim” until 1–3 unlock | **done** | Matrix: no “as fast as Supabase” without CI OLTP ratios. Blog `05-low-memory-database.md`: **aims** / engineering targets. Landing proof + FAQ: **aim** / **target until published benches are green**. |

### Required vs optional

- **Required for any “on par / as fast as Supabase” copy:** items **1**, **2** (measured RSS **or** keep aim-only forever for RAM), **3** (core indexed green **or** permanent index-honesty footnote), **5**.
- **Optional product-path claim** (REST vs PostgREST): item **4** — separate from embed SQL green.

---

## Phase evidence map (shipped work ≠ unlock)

| Phase | What landed | Librebase / lidb refs | Unlocks marketing? |
|-------|-------------|----------------------|--------------------|
| P0–P2 | Modes, core scenarios, `check_gate.py`, CI wire | `feat/p5-oltp-index-impl-detect` / PR #21 | **No** — need consecutive nightly PASS on **embed_execjson** core |
| P3 | HTTP soft-compare + CI lis stack bootstrap | `run_http_compare.py`; workflow `run_http=true` | Soft PASS local (median max **0.60×**) — hard-gate pending |
| P4 | PH-DB-7 lean RSS + P95/ops in lidb | lidb `e731661` / CI `2bfbd3c` [MR !5](https://gitlab.lilangverse.xyz/li-langverse/lidb/-/merge_requests/5); pipeline [27003](https://gitlab.lilangverse.xyz/li-langverse/lidb/-/pipelines/27003) | **RSS yes** — lean **3.797 MB** VmRSS PASS; P95/ops still via oltp-compare |
| P5 | sorted_tree + Phase 1 range hot path | lidb `feat/p5-sorted-tree-index` Phase 1; librebase harness `build_type` | Core + range diagnostic PASS on Release; CI promote pending |
| P6 | This checklist + aim language | this file | **Unlock doc only** — claims stay locked (Linux RSS + CI promotion) |

---

## Still blocking a real marketing unlock

1. ~~**No multi-day nightly PASS trail**~~ — **satisfied** by manual 3-rep streak 2026-08-05 (0.19–0.25× point lookup); scheduled nightly CI greens still recommended for regression guard.
2. ~~**PH-DB-7** lean RSS Linux VmRSS~~ — **satisfied** GitLab job [99197](https://gitlab.lilangverse.xyz/li-langverse/lidb/-/jobs/99197) **PASS** **3.797 MB** (`proc_vmrss`).
3. ~~**Indexed range scan** >1.2×~~ — **satisfied locally** on Release (median **0.36×**); still need CI hard-gate promotion (2 consecutive nights) before treating as unlocked marketing evidence.
4. ~~**HTTP REST** soft breach~~ — **soft PASS** locally (median max **0.60×**); hard-gate optional after 2 stable CI nights.

**Remaining before top-of-file `UNLOCKED`:** promote item **3** range_scan to CI hard-gate (2 nights) **or** ship permanent sorted_tree marketing footnote; then flip Status + refresh landing/blog/matrix in a dedicated copy PR. RSS is no longer blocking.

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

---

## Manual verification log (2026-08-05)

| Blocker | Command / setup | Result |
|---------|-----------------|--------|
| PH-DB-7 RSS (Windows) | `python scripts/bench/lidb_bench.py --profile librebase-lean`; `check_rss_gate.py --allow-advisory` | **advisory PASS** 5.621 MB (Windows WorkingSet) |
| PH-DB-7 RSS (Linux CI) | GitLab `footprint-rss` job 99197 / pipeline 27003 @ `2bfbd3c` | **PASS** lean **3.797 MB** VmRSS; registry-min **4.859 MB** |
| range_scan (Debug, prior) | Debug `lidb_embed` × 3 | **BREACH** median 1.94× |
| range_scan (Release + Phase 1) | `smoke-release` clang Release + sorted vector / prefix successor × 3 vs lb-pg-bench:5433 | **PASS** median **0.36×** (0.29–0.37×) |
| core after Phase 1 | `--scenarios core` Release | **PASS** `point_lookup_with_index` **0.20×** |
| HTTP REST (prior) | single session / Debug path × 3 | **SOFT BREACH** median max 4.37× |
| HTTP REST (pool + Release) | `LI_EMBED_POOL_SIZE=4` + Release embed × 3 vs lb-pgrst-bench:3000 | **SOFT PASS** median max **0.60×** (0.59–0.75×) |
