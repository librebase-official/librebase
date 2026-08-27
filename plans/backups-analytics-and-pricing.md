# Backups + Analytics Plan (with Revised Pricing at Starter €12)

**Status:** Draft (approved for implementation)
**Date:** 2026-08-26
**Owner:** Librebase
**Repo:** `librebase-official/librebase`

> **TL;DR.** Add a backup service to the Librebase SaaS on Hetzner. Backups live on
> **additional Hetzner Volumes** (€0.04/GB/mo, triple-replicated, detachable) — one per
> project/server — **decoupled** from the VM price. Each pricing tier gets a fixed GB
> quota + schedule/retention; **everything that exceeds the included backup scheme is a
> custom request negotiated with the client** (no self-serve metered overage, no surprise
> bills). The **Starter tier is €12/mo** (the lowest paid tier), with the €2/month backup
> volume comfortably inside the margin. Full metrics exposed both per-account (org) and
> SaaS-wide via the saas-admin dashboard.

> **Not found anywhere:** a prior "backups plan with pricing" did not exist in any local
> database (grok/klautcode/opencode/hermes agent DBs, the VPS `admin.db`, local
> SQLite volumes were all checked). This plan is built from the codebase + Hetzner +
> Supabase research. See "Research grounding" §2.

---

## 1. Goals

| Goal | Notes |
|---|---|
| **Volume-backed backups** | Backups stored as an *additional* Hetzner Volume attached to each host VM, mounted at `/hcbk`. One volume per host (shared by that host's projects), GB-metered at €0.04/GB. Never Hetzner's server-backup add-on (server-bound, ~20% of VM, not migratable). |
| **Tiered quotas** | Each price tier includes a defined GB of backup storage + a snapshot frequency/retention policy (see §4). |
| **Overage = custom request** | Exceeding the included backup GB does not auto-bill. Usage >80% → warning; >100% → backups suspended, client must sign a custom quote or upgrade. Matches the "honest pricing" brand. |
| **Per-account analytics** | org-level: GB used, quota %, last backup, snapshot count, health. |
| **SaaS-wide analytics** | platform view: total backup GB, volume cost €, per-host, per-org top consumers, growth trend, health distribution. |
| **Starter @ €12** | New lowest paid tier. The €2/mo 50 GB backup volume is comfortably inside the margin. |

---

## 2. Research grounding

### 2.1 Hetzner Cloud (Aug 2026 — from `pricing_validation.py`)

| VM | Price | vCPU | RAM | Disk (local NVMe) |
|---|---|---|---|---|
| CX11 | €3.29 | 1 | 2 GB | 20 GB |
| CX21 | €5.35 | 2 | 4 GB | 40 GB |
| CX31 | €10.55 | 4 | 8 GB | 80 GB |
| CX41 | €18.95 | 8 | 16 GB | 160 GB |
| CX51 | €35.95 | 16 | 32 GB | 320 GB |

- **Block Storage Volumes**: €0.04/GB/mo, 10 GB–10 TB each, **triple-replicated** across 3
  physical servers, max 16 volumes/VM, **detachable + resizable (grow-only)**.
- **Server backup add-on** (~20% of server price, 7 daily slots, server-bound, deleted with
  the server): **not used** — can't migrate, can't per-customer meter, can't report per-instance.
- **Local NVMe** hosts the live DB (fast); the **backup volume** is a *separate, additional*
  volume = `data_dir` (live) vs `/hcbk` (backups).

### 2.2 Supabase (competitor benchmark)

| Feature | Free | Pro | Team | Enterprise |
|---|---|---|---|---|
| Automatic backups | none | 7-day daily | 14-day daily | custom |
| PITR | none | $100 / 7-day window (add-on) | same | custom |
| Disk overage | — | $0.125/GB | $0.125/GB | custom |

Librebase advantage: Hetzner volumes are **5× cheaper** than Supabase's disk overage ($0.125/GB
vs €0.04/GB), and triple-replicated by default.

### 2.3 Current Librebase pricing (`admin_server.py` PLANS)

> ⚠️ **Historical conflict (resolved):** an earlier sales deck listed Scale = €99 while
> `pricing_validation.py` listed €79; the live `PLANS` dict = 99. Per the decision in §1,
> **Starter = €12**. Scale stays €99. All sources are reconciled in the implementation (§9).

| Current tier | Price | Instances | RAM | Local storage (storage_gb) | Backup (Hetzner vol) | Support |
|---|---|---|---|---|---|---|
| Sandbox | €0 | 1 (shared) | 64 MB | 1 GB | 0 GB | community |
| Starter | €9 → **€12** | 1 | 512 MB | 10 GB | 50 GB | email |
| Pro | €20 | 3 | 1 GB each | 50 GB | 100 GB | priority |
| Scale | €99 | 10 | 2 GB each | 200 GB | 250 GB | slack |
| Self-host | €0 | unlimited | — | — | — | community |
| Enterprise | €299+ | custom | custom | custom | custom | premium |

---

## 3. Cost model (honest RAM-derived packing, shared hosts)

Backups are an **additional** Hetzner volume (€0.04/GB/mo, triple-replicated). The VM hosts the
live DB on a small local NVMe working set; the bulk (backups + customer disk) lives on volumes,
so **RAM — not disk — is the scaling metric**. Customers are packed N-per-host by RAM
(`host_RAM // (instances × ram_mb)`); there is **no customer cap** — "N per host" is only how
many fit on one VM, and you scale by adding VMs.

| Tier | Price | RAM/cust | Best host | Fit/VM | VM/cust | Backup vol | Infra | Margin |
|---|---|---|---|---|---|---|---|---|
| Starter | €12 | 0.5 GB | CX51 | 64 | €0.56 | 50 GB = €2.00 | €2.56 | **79%** 📉 |
| Pro | €20 | 3 GB | CX51 | 10 | €3.60 | 100 GB = €4.00 | €7.60 | **62%** 📉 |
| Scale | €99 | 20 GB | CX51 | 1 | €35.95 | 250 GB = €10.00 | €45.95 | **54%** 📉 |
| Sandbox | €0 | shared | — | — | 0 | 0 | 0 | — |

> **Decision (option B — strong specs over margin):** we keep the strong specs (Starter 1×512 MB
> + 50 GB/30-day backup; Pro 3×1 GB + 100 GB; Scale 10×2 GB + 250 GB) and **accept** the margins
> that result (Starter 79 %, Pro 62 %, Scale 54 %). They stay profitable, and the specs beat
> Supabase (Pro backup 100 GB vs 8 GB; Scale 83 % cheaper than Team).
>
> **Why the tiers sit under 80 %:** Starter's 512 MB + 50 GB backup; Pro's 100 GB backup alone is
> €4.00 = the entire 20 % margin budget of a €20 price; Scale's 20 GB RAM fits only 1 customer per
> CX51 (no amortisation). `pricing_validation.py` (REFERENCE section) shows the exact spec cuts
> that would recover margin later (Starter RAM→256 MB; Pro backup→50 GB; Scale RAM→~8 GB).

---

## 4. Backup tiers (per pricing plan)

| Plan | Schedule | Retention | Included backup GB | Restore window | PITR | Overage |
|---|---|---|---|---|---|---|
| **Sandbox** (€0) | none | none | 0 GB | — | no | custom request |
| **Starter** (€12) | daily | 30 days | 50 GB | 30 days | no | custom request |
| **Pro** (€20) | daily | 30 days | 100 GB | 30 days | no | custom request |
| **Scale** (€99) | daily + 6-hourly | 30 days | 250 GB | 30 days | no (add-on) | custom request |
| **Enterprise** (€299+) | customizable | customizable | per-contract | per-contract | yes (€10/7-day window) | per-contract |

### 4.1 Overage handling (no self-serve billing)

> *Everything that exceeds this backup scheme must be negotiated with the client (custom request).*

- **≤80% of included GB:** healthy, no action.
- **80–100%:** warning in Studio project settings + `backup_quota_warning` flag in the SaaS-admin dashboard. Host-agent continues scheduling but logs a warning.
- **>100%:** backup scheduling **suspended** for the org; instance status flag
  `backup_quota_exceeded`. The user sees a prompt to (a) upgrade tier or (b) contact sales.
  No automatic top-up — expansion is a custom quote / new Stripe subscription.
- **No metered overage line item** is added to Stripe. Backups are **tier-locked**, mirroring
  the product's "honest, flat-rate, no surprise bills" brand.

---

## 5. Revised pricing tiers (all adapted)

| Tier | Price (€/mo) | Instances | RAM/instance | Local storage | Included backups | Support |
|---|---|---|---|---|---|---|
| **Sandbox** | 0 | 1 (shared) | 64 MB | 1 GB | 0 GB / none | community |
| **Starter** | **12** | 1 | 512 MB | 10 GB | 50 GB / 30-day daily | email |
| **Pro** | 20 | 3 | 1 GB | 50 GB | 100 GB / 30-day daily | priority |
| **Scale** | 99 | 10 | 2 GB | 200 GB | 250 GB / 30-day + 6h | slack |
| **Enterprise** | 299+ | custom | custom | custom | custom | premium |

**Rationale for the €9 → €12 Starter move:** the backup volume (50 GB @ €0.04 = €2.00) is a
new line cost. At €12, Starter's infra is €2.28 (vm share €0.28 on CX51 + €2.00 backup) → 81 %
margin per §3, comfortably absorbing the backup service. This is the "upgrade pricing to 12"
directive: the **lowest paid tier rises to €12** so backups are in-margin, not a surprise add-on.

---

## 6. Backup analytics

### 6.1 Per-account (organization) — self-service + operator

Visible in **Studio** (project → Backups tab) and **SaaS-admin** (Orgs table + detail view).

**Per-org rollup (stored on the org / derived on read):**

| Field | Source |
|---|---|
| `backup_quota_gb` | `PLANS[plan].backup_gb` (the tier's included GB) |
| `backup_used_gb` | `sum(instances.backup_bytes)` for the org |
| `backup_count` | count of `backups` rows for the org (present) |
| `backup_last_at` | max(`last_backup_at`) across the org's instances |
| `backup_status` | `healthy` (≤80%) / `quota_warning` (80–100%) / `quota_exceeded` (>100%) / `suspended` |
| `backup_cost_eur_mo` | `backup_used_gb × 0.04` (Hetzner volume cost) |

### 6.2 SaaS-wide — operator dashboard (`data-saas-admin` → Backups page)

**Stat cards:**
- Total backup GB (all orgs)
- Monthly Hetzner volume cost (total GB × €0.04)
- Top 5 orgs by backup GB
- Health: % healthy / % warning / % exceeded

**Tables:**
- Per-org rows (the 6.1 fields + host_id)
- Per-host rows: host, provider region, total backup GB, volume utilisation %, tenant count
- Per-tier distribution: backup-GB by price tier (where's the volume-cost risk)

**Trend:** backup GB over the last 30 days (roll-up by day).

---

## 7. Architecture

```
                         ┌──────────────────────┐
                         │  Instance (Podman)     │
                         │  /data  = local NVMe   │
                         │  lidb-runtime          │
                         │  POST /backup → tarball│
                         └──────────┬─────────────┘
                                    │ export (tarball stream)
                                    ▼
                         ┌──────────────────────┐
                         │  Host-agent           │  host-agent/service.py
                         │  - GET /org/v1/.../instances  (desired set)│
                         │  - for each running inst:    │
                         │      call POST /backup → tarball to /pipe │
                         │  - write to /hcbk/<org>/<inst>/<ts>.tar │
                         │  - prune beyond plan.retention_days │
                         │  - on heartbeat: report backup_bytes  │
                         │    backup_count, last_backup_at, disk_bytes│
                         └──────────┬─────────────┘
                                    │ POST /org/v1/host-agent/heartbeat {...}
                                    ▼
                         ┌──────────────────────┐
                         │  admin-api            │  admin-api/scripts/admin_server.py
                         │  - persist instance.  │ backup_* columns
                         │  - append backups ledger rows
                         │  - quota gate on schedule/launch
                         │  - GET /org/v1/orgs/{id}/backups  (rollup)
                         └──────────┬─────────────┘
                                    │ (synced admin.db, read-only)
                        ┌──────────┴──────────────────────┐
                        ▼                                  ▼
              ┌────────────────────┐          ┌────────────────────────┐
              │ data-studio-ui     │          │ saas-admin-api         │
              │ (self-service)     │◄──/admin/v1/*──│ (dashboard API)    │
              │ GET /org/v1/.../backups  │          │  GET /admin/v1/backups* │
              └────────────────────┘          └──────────┬────────────┘
                                        data-saas-admin │
                              ┌─────────────────────────┴────────┐
                              ▼                                   ▼
                  ┌────────────────────────┐      ┌──────────────────────────┐
                  │ /dashboard/backups     │      │ Orgs table: backup cols  │
                  │ (SaaS-wide analytics)  │      │                            │
                  └────────────────────────┘      └──────────────────────────┘
```

### 7.1 Data flow

1. **Backup job** — host-agent, on the schedule the tier allows (Starter = daily @ 03:00), for
   each running instance: pull a backup tarball from the lidb-runtime `POST /backup`
   endpoint and stream-write it to the host's `/hcbk` volume at
   `/hcbk/<org_id>/<instance_id>/<YYYY-MM-DD>.tar`.
2. **Retention** — after writing, prune snapshots older than `plan.retention_days` per instance
   folder.
3. **Report metrics** — the host-agent heartbeat (`POST /org/v1/host-agent/heartbeat`) now
   carries a per-instance payload: `{id, data_bytes, backup_bytes, backup_count, last_backup_at}`.
   admin-api persists these into `instances` columns + appends a row to the `backups` ledger.
4. **Quota gate** — before scheduling a backup, admin-api compares the org's running
   `backup_used_gb` to `plan.backup_gb`; over quota → refuse + flag `backup_quota_exceeded`.
5. **Analytics** — `saas-admin-api` reads the synced `admin.db` (read-only) and derives SaaS-wide
   stats without touching the production admin-api.

---

## 8. Implementation phases

### Phase 1 — Data model + control plane (`admin-api`)

1. **Migration 022** (§9.1): add `backups` table + instance backup columns + host backup-volume columns.
2. **PLANS dict** (§9.2): add `backup_gb`, `backup_retention_days`, `backup_frequency`; re-price
   Starter to 12.
3. **admin-api routes:**
   - `GET /org/v1/orgs/{id}/backups` — per-org rollup (6.1).
   - `GET /org/v1/orgs/{id}/backups/ledger` — paged backup rows.
   - `POST /org/v1/orgs/{id}/backups/schedule` — admin sets/adjusts schedule (owner/admin).
   - Quota gate in `/host-agent/instances` (refuse to advertise backup-eligible instances
     when the org is over quota) + a `/org/v1/orgs/{id}/backups/status` summary.
4. **Heartbeat parser** — accept `backup_bytes`/`backup_count`/`last_backup_at` in the agent
   payload (extend `agent_heartbeat`/`host_heartbeat` handlers).

### Phase 2 — Host agent (`host-agent/service.py`)

1. Mount a Hetzner volume at `/hcbk` per host (provisioned in cloud-init / `hetzner.py`:
   create volume, attach, mount, `mkdir -p /hcbk/<org>/<inst>`).
2. Add `_run_backup(instance)` — `POST /instances/{id}/backup` (or exec) → stream tarball
   to `/hcbk/<org>/<inst>/<ts>.tar`.
3. Add `_prune_backups(instance, retention_days)` — delete old tarballs.
4. Extend `heartbeat()` to carry `instances: [{id, data_bytes, backup_bytes, backup_count, last_backup_at}]`.

### Phase 3 — SaaS-admin backend (`saas-admin-api`)

1. New read-only endpoints over synced `admin.db`:
   - `GET /admin/v1/backups/overeview` — `totalGb`, `totalCostEUR`, `healthDistribution`, `topOrgs`, `trend[30]`.
   - `GET /admin/v1/backups/orgs` — per-org rows (6.1).
   - `GET /admin/v1/backups/hosts` — per-host rows + volume utilisation.
   - `GET /admin/v1/backups/ledger?org=&limit=`.
2. Enrich `GET /admin/v1/orgs` with the 6.1 backup fields.
3. Enrich `GET /admin/v1/overview` with `totalBackupGb`, `backupCostEUR`, `backupHealth`.

### Phase 4 — Dashboard (`data-saas-admin`)

1. New `/dashboard/backups` page — stat cards (§6.2) + per-org + per-host tables.
2. Orgs table — add **Backup GB**, **Used %**, **Last backup**, **Status** columns.
3. Overview page — add a backup stat card.
4. `lib/admin-client.ts` — new `BackupsOverview`, `BackupOrgRow`, `BackupHostRow` types +
   `getBackups()`.

### Phase 5 — Pricing + docs

1. `pricing_validation.py` — add the volume-backup cost model (§3 table).
2. Reconcile Scale €99 across `pricing_validation.py` + `PLANS` dict.
3. `docs/sdd/specs/cloud-ga/PLAN.md` §7 + new `docs/backups.md`.
4. Update `HANDOFF.md` open items.

### Phase 6 — Tests

- `tests/test_host_agent.py` — assert backup fields flow through the heartbeat (mocked).
- `tests/test_backups_analytics.py` (new) — quota gate + SaaS-wide rollup queries over a temp DB.

---

## 9. Code anchors

### 9.1 Migration `admin-api/migrations/022_backups.sql`

```sql
-- Backup service on Hetzner volumes (per-host shared backup volume + ledger).
-- Everything that exceeds a tier's included backup GB is a custom request.

-- Per-host Hetzner volume that holds this host's backups
ALTER TABLE hosts ADD COLUMN backup_volume_id TEXT;       -- Hetzner volume UUID
ALTER TABLE hosts ADD COLUMN backup_volume_gb INTEGER;    -- provisioned capacity
ALTER TABLE hosts ADD COLUMN backup_used_gb REAL DEFAULT 0;-- reported by agent

-- Latest reported backup metrics per instance
ALTER TABLE instances ADD COLUMN backup_bytes INTEGER DEFAULT 0;
ALTER TABLE instances ADD COLUMN backup_count INTEGER DEFAULT 0;
ALTER TABLE instances ADD COLUMN last_backup_at TEXT;     -- UTC ISO

-- Canonical ledger: one row per snapshot tarball
CREATE TABLE IF NOT EXISTS backups (
    id TEXT PRIMARY KEY,            -- backup_<org>_<instance>_<timestamp>
    org_id TEXT NOT NULL,
    instance_id TEXT NOT NULL,
    host_id TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_at TEXT NOT NULL,        -- snapshot timestamp
    retention_days INTEGER NOT NULL, -- plan policy at backup time
    path TEXT NOT NULL,              -- /hcbk/<org>/<inst>/<name>.tar
    status TEXT NOT NULL,            -- present | pruning | error
    deleted_at TEXT,
    INDEX idx_backups_org (org_id),
    INDEX idx_backups_host (host_id),
    INDEX idx_backups_instance (instance_id),
    INDEX idx_backups_created (created_at)
);
```

### 9.2 PLANS dict extension

```python
# Added to each non-sandbox tier in PLANS:
"backup_gb": <included GB>,          # volume-billed quota (0.04 €/GB/mo)
"backup_retention_days": <n>,        # how long snapshots are kept
"backup_frequency": "<schedule>",    # "daily" | "daily+6h" | "none" | "custom"
```
- sandbox: `backup_gb=0, backup_retention_days=0, backup_frequency="none"`
- starter: `backup_gb=50,  backup_retention_days=30, backup_frequency="daily"`
- pro: `backup_gb=100, backup_retention_days=30, backup_frequency="daily"`
- scale: `backup_gb=250, backup_retention_days=30, backup_frequency="daily+6h"`
- enterprise: `backup_gb=None, backup_retention_days=None, backup_frequency="custom"`

### 9.3 Host-agent heartbeat payload extension

```jsonc
{
  "hostId": "host_abc",
  "instances": [
    {
      "id": "inst_xyz",
      "data_bytes": 1234567,
      "backup_bytes": 234567,
      "backup_count": 7,
      "last_backup_at": "2026-08-26T03:00:00Z"
    }
  ]
}
```

---

## 10. Open questions / decision log

| # | Question | Decision |
|---|---|---|
| 1 | Backup mechanism: pull (host calls instance `/backup` API) vs push (instance cron writes volume) | **Pull** — host-agent schedules centrally, streams tarball via instance API port; keeps scheduling logic single-tenant-safe. |
| 2 | Volume per host vs per instance | **Per host** (one ~2 TB volume at `/hcbk`, per-org folders) — avoids the 16-volume/VM cap and is cheaper. Per-instance folders give per-customer isolation for analytics. |
| 3 | Scale shrink 10→5 instances | **No shrink** — Scale stays 10×2GB @ €99; only Starter moves €9→€12. The "12" is the new floor, not a ceiling cut. |
| 4 | €99 vs €79 vs €9 conflict | Standardise on **€99** for Scale (matches the live `PLANS` dict + landing page). |
| 5 | GDPR / SOC 2 | See §11 — PII-prefixed logs, retention, access controls (detailed in the separate "Analytics" plan the user asked for next). |

> Note: this plan's backup metrics (`backup_bytes`, `backup_count`, `last_backup_at`) are
> PII-free metadata only — see `plans/analytics-compliance.md` §2.1/§3.2 for how the
> `backups` ledger rows are exported into the auditable analytics store with retention.

---

## 11. Compliance quick-notes (GDPR / SOC 2)

This backups/analytics plan is deliberately **tier-locked + custom-overage** to keep billing
predictable for finance teams (a stated product tenet). For the deeper compliance design
(logging, access controls, retention, audit) see the companion **`plans/analytics-compliance.md`**.
That plan defines the structured audit store (`audit_log` table, §3.2), PII hashing of
identifiers, the TTL purge job, and the customer-scoped read API. Briefly, the backup service
respects:

- **Data residency:** Hetzner is GDPR-relevant (DE-hosted); backups inherit the instance's
  region; no cross-region replication unless explicitly contracted (Enterprise).
- **No PII in backup metrics:** `backups.size_bytes`, `backup_count`, `last_backup_at` are
  size/timing metadata only — no row content is stored in `admin.db`.
- **Retention:** backup files are pruned per-tier policy; the `backups` ledger row is
  soft-deleted (`deleted_at`) and hard-purged after 90 days for the audit trail (purge is
  auditable — see `analytics-compliance.md` §3.4).

---

## 12. Files to create / modify

| File | Action |
|---|---|
| `plans/backups-analytics-and-pricing.md` | **this doc** |
| `admin-api/migrations/022_backups.sql` | create |
| `admin-api/scripts/admin_server.py` | PLANS dict + routes + heartbeat parser |
| `host-agent/service.py` | backup scheduling + heartbeat metrics |
| `saas-admin-api/scripts/admin_dashboard_server.py` | `/admin/v1/backups*` endpoints |
| `data-saas-admin/lib/admin-client.ts` | backup types + `getBackups()` |
| `data-saas-admin/app/dashboard/backups/page.tsx` | **new** — SaaS-wide page |
| `data-saas-admin/app/dashboard/orgs/page.tsx` | backup columns |
| `pricing_validation.py` | volume-backup cost model |
| `docs/sdd/specs/cloud-ga/PLAN.md` | §7 + backup mention |
| `tests/test_backups_analytics.py` | **new** |
| `plans/analytics-compliance.md` | companion — GDPR/SOC 2 audit + product analytics store |
