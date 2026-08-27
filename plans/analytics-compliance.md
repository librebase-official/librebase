# Analytics + Compliance Plan

**Status:** Draft (approved for implementation)
**Date:** 2026-08-26
**Owner:** Librebase
**Related:** `plans/backups-analytics-and-pricing.md`

> **Scope.** What analytics users actually need (two distinct audiences), how and where we
> store it, and how the design satisfies **GDPR** and **SOC 2**. This is the product-side
> analytics + audit story — not the per-instance lidb request analytics (that already exists
> in `lis/routes/analytics`), but the **cross-instance / cross-org / control-plane** view a
> customer (or operator) needs to (a) prove compliance and (b) understand product usage.

---

## 1. User research — what users need from analytics

There are two audiences, with different needs:

### 1.1 Compliance users (auditors, legal, SRE/security)

> **"Did a user do X at time Y? Is anything PII-leaking? Can I prove who had access to
> what, and to whom?"**

They need:
- **Authentication & authorization audit trail** — every login/logout, token refresh, MFA
  challenge, invite accept, role change, org switch, plan change. *No PII beyond what's
  structurally required (email is an identifier, not "data" in the GDPR sense for auth logs,
  but it must be retained with a defined TTL and purged on account deletion).*
- **Data change events** — who created/deleted/restored instances, projects, hosts, KMS keys,
  OAuth providers. These are **regulated operations** (infra-as-code changes = change mgmt audit).
- **Export / deletion evidence** — proof that a GDPR "right to erasure" request was fulfilled
  (rows deleted, backups pruned).
- **Access controls** — who (operator role) can read the logs; read-only, append-only.

### 1.2 Product users (founders, PMs, devs, finance)

> **"How is the product being used? Are there bugs in production? Are we meeting SLAs? What
> costs money?"**

They need:
- **Usage/quota** — per org: instances count, RAM used, backup GB vs quota, over-quota events.
- **Error rate + latency** — per route/endpoint, p50/p95, 4xx/5xx breakdown.
- **Feature adoption** — which APIs are hot vs cold, which plans are growing.
- **Revenue + cost** — MRR per plan, backup volume cost (€), Hetzner host utilization.

> **Key requirement:** the two audiences have **opposite privacy needs**. Compliance users need
> *full* audit context (who, what, when) *within the law*. Product users need *aggregated,
> PII-free* dashboards. So we **separate** the stores: a **structured audit log** (full
  context, short retention, restricted read) and an **aggregated metrics store** (PII-free,
  long retention, broad read).

---

## 2. What analytics to collect (the event taxonomy)

### 2.1 Audit events (compliance) — structured, append-only

| Category | Event | Actor | Key fields | Retention |
|---|---|---|---|---|
| Auth | `auth.login_attempt` | user | email(hashed), ip, user_agent, provider, outcome, ts | 90 days |
| Auth | `auth.login_success` | user | email(hashed), ip, mfa_used, ts | 90 days |
| Auth | `auth.token_refresh` | user | email(hashed), ts | 90 days |
| Auth | `auth.mfa_challenge` | user | email(hashed), factor_type, outcome, ts | 90 days |
| Auth | `auth.logout` | user | email(hashed), session_id(hash), ts | 90 days |
| Org | `org.created` | user | org_id, plan, ts | 1 year |
| Org | `org.plan_changed` | admin | org_id, old_plan, new_plan, stripe_sub, ts | 1 year |
| Org | `org.role_changed` | admin | org_id, user_id, old_role, new_role, ts | 1 year |
| Project | `project.created` | user | org_id, project_id, region, ts | 1 year |
| Instance lifecycle | `instance.launch` / `stop` / `restart` / `delete` | user/agent | org_id, instance_id, host_id, user_agent, ts | 1 year |
| Host | `host.provisioned` / `started` / `stopped` / `decommissioned` | user/agent | host_id, server_id, region, provider, ts | 1 year |
| KMS | `kms.create_key` / `rotate` / `delete_key` | user/service | project_id, key_id, actor, ts | 1 year |
| Provider | `provider.upsert` / `delete` | user | project_id, provider, client_id(hash), changed_fields, ts | 1 year |
| Backup | `backup.snapshot_create` / `backup.restore` / `backup.prune` | user/agent | org_id, instance_id, size_bytes, backup_id, ts | 30 days |
| GDPR | `gdpr.data_export_requested` / `gdpr.data_deleted` | user/admin | user_id, scope, request_id, ts | 3 years (legal hold) |

**PII handling** — the critical compliance question:
- **email** → stored **as a hash** (SHA-256) in the audit log. The *raw* email is only in the
  `users` table for active accounts. Audit logs reference the hashed form so a reviewer can
  correlate "user X did Y" without exposing plaintext email in the log sink.
- **ip_address** → stored **truncated** to /24 (e.g. `192.0.2.0/24`), per GDPR "legitimate
  interest for security" guidance. Full IP is never persisted to the audit store.
- **session_id** → stored **hashed**, never raw.
- **user_agent** → stored as a **parsed bucket** (browser family + OS family, e.g.
  `Chrome/Firefox on Windows/macOS`), not the raw string, after ingestion. (Raw is allowed
  transiently in the JSONL before parsing.)

### 2.2 Aggregated metrics (product) — PII-free, queryable

| Metric family | Dimensions | Value | Refresh |
|---|---|---|---|
| `org.instance_count` | org, plan | count | per reconcile |
| `org.backup_usage_gb` | org, plan | sum(instances.backup_bytes) | per heartbeat |
| `org.backup_quota_pct` | org | used/included | per heartbeat |
| `api.request_count` | org, route, status_bucket | count | 1m roll-up |
| `api.error_rate` | org, route | ratio | 1m roll-up |
| `api.p95_latency_ms` | org, route | ms | 1m roll-up |
| `host.cpu_percent` | host, region | % | per heartbeat |
| `host.backup_volume_used_gb` | host | sum | per heartbeat |
| `plan.mrr` | plan | € | per billing webhook |
| `plan.org_count` | plan | count | per reconcile |
| `backup.cost_eur_mo` | org/host/plan | € (GB × 0.04) | per heartbeat |

**No raw PII** in any of these rows — only IDs, counts, sums, percentiles. Safe for any
dashboard reader.

---

## 3. Storage design

### 3.1 Per-instance runtime (lidb-runtime / lis) — **existing, no change**

- `lis/routes/analytics/` (engine.py) already produces an in-process aggregate summary:
  `total, error_count, error_rate, by_status, top_routes (+ p50/p95/avg latency),
  events_per_sec`. Bounded at 5,000 events / 100 samples per route. PII-safe (no client IP).
- `lis/routes/registry/audit_log.py` + `audit_store.py` write a structured JSONL
  (`registry-audit.jsonl`) capped at 10,000 in-memory entries + file sink.
- These are **per-instance**. We keep them as-is and **export** them (see §3.3).

### 3.2 Control plane (admin-api) — **new structured audit store**

A new append-only table in `admin.db`:

```sql
CREATE TABLE IF NOT EXISTS audit_log (
    id            TEXT PRIMARY KEY,        -- audit_<ulid>
    org_id        TEXT,                    -- nullable for control-plane-global events
    event         TEXT NOT NULL,           -- e.g. auth.login_success, instance.delete
    actor_kind    TEXT NOT NULL,           -- user | agent | system
    actor_id_hash TEXT,                    -- SHA-256(email) or service key id
    ip_prefix     TEXT,                    -- /24 of client IP (or NULL for internal)
    target_id_hash TEXT,                   -- hashed target (instance/project/host_id)
    outcome       TEXT NOT NULL,           -- success | failure
    detail        TEXT,                    -- JSON, no raw PII (hashed identifiers only)
    ts            TEXT NOT NULL,           -- UTC ISO
    retention_ttl_days INTEGER NOT NULL    -- per-event-class retention
);
CREATE INDEX idx_audit_org_ts   ON audit_log(org_id, ts);
CREATE INDEX idx_audit_event_ts ON audit_log(event, ts);
```

**Append-only:** no UPDATE/DELETE except a periodic purge job that only removes rows past
`ts < now() - retention_ttl_days`. This gives SOC 2 "log retention — no gaps" + the purge is
auditable (it writes a `audit_log.purged` meta-row).

### 3.3 SaaS-wide aggregation / product analytics store

A separate, **PII-free** store for dashboards. Two options, pick one:

- **(A) SQLite `analytics.db`** (simplest, self-hosted, same VPS) — tables: `metric_rollups`
  (key/value/time), `usage_daily` (org-level GB/count). Read by `saas-admin-api`'s new
  `/admin/v1/analytics/*` endpoints. No PII ever written here.
- **(B) Supabase table** (reuses the existing Supabase stack at `supabase.majico.xyz`) — a
  `product_analytics` table with `org_id, metric, value, bucket, ts`. Lets the landing/app
  stack reuse the same GoTrue auth + RLS. Recommended once the Supabase waitlist is proven
  stable (HANDOFF §open-items).

**Recommendation: (A) for MVP** — keeps analytics co-located with admin-api, no new external
dependency, trivially GDPR-clean (no PII, easy to delete). Upgrade to (B) if we need
cross-region replication or the analytics volume exceeds a single SQLite file.

### 3.4 Retention policy (the compliance core)

| Data class | Store | TTL | Rationale |
|---|---|---|---|
| Structured audit log | `audit_log` | **90 days** (auth) / **365 days** (org/proj/instance/host changes) / **3 years** (GDPR export/delete evidence) | SOC 2 CC6.7 (audit trail retention); GDPR "data kept no longer than necessary" for most events; 3y for legal-process defense. |
| Per-instance runtime audit | `registry-audit.jsonl` | 7 days file / 10k in-mem | instance-local, best-effort; real audit source of truth is the control plane. |
| Aggregated metrics | `analytics.db` | **indefinite (PII-free)** | no PII → no deletion obligation; can keep forever for trend analysis. |
| Backup ledger rows | `backups` table in `admin.db` | 90 days after `deleted_at` | links to backup analytics; purge after 90 days. |

> A single purge job (run nightly in admin-api) deletes rows past TTL. Each purge writes an
> `audit_log` meta-row (`event=audit_log.purged, detail={class, before_ts, rows}`) so the
> retention itself is auditable. This satisfies "no gaps without evidence."

---

## 4. Who can see what (access control)

| Role | Can read structured audit log | Can read aggregated metrics | Can export | Notes |
|---|---|---|---|---|
| **Customer (org owner/admin)** | **own org's events only** (scoped by `org_id`), 90-day window | own org's usage metrics | own org | RBAC via the admin-api `require_org_role` seam. |
| **SaaS operator (platform admin)** | all orgs, full 90/365-day window | all metrics | all | `LIBREBASE_ADMIN_DASHBOARD_TOKEN` / `admin_enabled` guard in saas-admin-api. |
| **SaaS operator (support)** | own org only (no cross-tenant) | own org only | none | support role = customer role, cannot read other orgs. |
| **Auditor / SOC 2 reviewer** | full window, export | full | yes | via a dedicated read-only token, audit-activated. |

**Cross-tenant isolation:** the audit log query API is scoped by the caller's org. There is
no `org_id = NULL` path for customer queries — only the platform-admin scope sees
cross-org rows.

---

## 5. GDPR compliance checklist

| Obligation | How it's met | Owner |
|---|---|---|
| **Lawful basis** (Art 6) | Auth/usage analytics = Legitimate Interest (security + service integrity); marketing = consent (waitlist). | Product |
| **Data minimisation** (Art 5.1.c) | Audit stores only hashed identifiers + /24 IP + parsed UA bucket; metrics store is PII-free by construction. | Eng |
| **Purpose limitation** (Art 5.1.b) | Two stores: audit (security/compliance) vs metrics (product/analytics); never cross-write. | Eng |
| **Storage limitation** (Art 5.1.e) | TTL purge job (§3.4); 90-day default, 3y for legal-hold events. | Eng |
| **Right to erasure** (Art 17) | `gdpr.data_export_requested` + `gdpr.data_deleted` events; deleting a user → deletes `users` row + writes `user.deleted` audit; analytics store holds only aggregates, no per-user rows. | Eng/Legal |
| **Right to access** (Art 15) | `/org/v1/audit?from=&to=&event=` scoped to the org; export → JSONL. | Eng |
| **Data portability** (Art 20) | `/org/v1/export` returns all the user's account data (profile, projects, instances) + audit they triggered. | Eng |
| **Privacy by design** (Art 25) | PII stripping at the edge (in memory / first transform), before any persistence. | Eng |
| **Article 28 (processors)** | Hetzner is a sub-processor (EU-hosted, GDPR-relevant per §7). No other sub-processors. | Legal |
| **Breach notification** (Art 33) | Alert on >100 failed logins from one org in 5 min; auto-flag in saas-admin "Security" panel. | Eng |

> **Hetzner as sub-processor:** Hetzner's DE data centers + ISO 27001 + GDPR-relevant
> privacy policy make it an acceptable sub-processor. Backups inherit the instance's region
> (no cross-region replication by default). The DPA is covered under the Hetzner ToS.
> Snapshot/restore events are written to the `audit_log` (`instance.backup_snapshot` /
> `instance.backup_restore`, §2) so every backup operation is auditable end-to-end.

---

## 6. SOC 2 mapping

| SOC 2 CC | How analytics/compliance meets it | Evidence |
|---|---|---|
| **CC5.2 — System monitoring** | `host.cpu_percent`, `api.request_count/error_rate`, backup health → saas-admin dashboard. | `/admin/v1/analytics/...` endpoints |
| **CC6.1 — Logical access** | `auth.login_attempt/success`, role changes audit-logged. 2FA/MFA challenge events. | `audit_log` table |
| **CC6.2 — Security incident** | Spike in 5xx / failed logins → alert; audit_log.purged is auditable. | alerts + purge meta-row |
| **CC6.6 — User activity review** | Per-org audit query + export. | `audit_log_purged` evidence |
| **CC6.7 — Audit log retention** | structured audit log with TTL purge + purge-evidence meta-rows. | purge job logs |
| **CC7.1 — Security events** | backup failures, restore attempts, host provisioning events. | `audit_log` `backup.*` / `host.*` |
| **CC8.1 — Customer data** | cross-tenant isolation by org_id scoping; no PII in metrics store. | RBAC tests |

> For the **full SOC 2 artifact set** (policies, incident response runbooks, vendor
> assessments), deliverable owned by Legal/Operations — engineering provides the **controls
> and evidence** above.

---

## 7. Where analytics live today (code anchors)

| Surface | Files | Role |
|---|---|---|
| Per-instance request analytics | `lis/routes/analytics/{engine.py,handler.py,test_analytics.py}` | in-process aggregates (total/error_rate/top_routes + p50/p95); PII-safe; OOS-5, 18 tests ✓ |
| Per-instance audit trail | `lis/routes/registry/{audit_log.py,audit_store.py}` | structured JSONL, 10k in-mem cap + file sink, IP parsed |
| Control plane audit | *NEW* `admin-api/migrations/023_audit_log.sql` + `admin-api/scripts/audit.py` | structured, append-only, TTL-purged, hashed PII |
| Product metrics store | *NEW* `admin-api/migrations/024_analytics.sql` (`analytics.db`) | PII-free roll-ups |
| SaaS-admin analytics API | *NEW* `saas-admin-api/scripts/admin_dashboard_server.py` (`GET /admin/v1/analytics/*`) | serves operator + (scoped) customer dashboards |
| SaaS-admin dashboard UI | *NEW* `data-saas-admin/app/dashboard/analytics/page.tsx` + `data-saas-admin/app/dashboard/security/page.tsx` | operator analytics + audit viewer |
| Waitlist (consent analytics) | Supabase `librebase_waitlist` table | marketing funnel (consent-based); GDPR consent tracked |

---

## 8. Implementation phases

### Phase A — Foundation (audit store + PII stripping)

1. Migration `023_audit_log.sql` (§3.2) + purge job.
2. `audit.py` helper: `log_event(org_id, event, actor, ...)` that hashes email/IP/UAs.
3. Wire into existing admin-api auth + org/instance/host handlers (log `auth.*`, `org.*`,
   `instance.*`, `host.*`).
4. Migration `024_analytics.sql` (§3.3, option A) + roll-up writer fed by host-agent heartbeats.

### Phase B — Product dashboards (data-saas-admin)

1. saas-admin-api: `/admin/v1/analytics/overview`, `/admin/v1/analytics/usage?org=`,
   `/admin/v1/analytics/metrics?route=&window=`.
2. data-saas-admin: new `/dashboard/analytics` page (usage, MRR, error-rate, top routes) +
   `/dashboard/security` page (audit log viewer with org scoping + export).

### Phase C — Customer self-serve

1. Studio: project → **Analytics** tab (per-project usage + backup quota) + **Security**
   tab (own audit events, export request, data deletion request).
2. `GET /org/v1/orgs/{id}/audit` (scoped) + `POST /org/v1/orgs/{id}/export` +
   `POST /org/v1/orgs/{id}/gdpr/delete`.

### Phase D — Compliance hardening

1. Cross-tenant isolation tests (support role cannot read another org's audit).
2. PII-in-pipeline test (assert raw email/IP never reach the analytics store).
3. TTL purge test (rows past TTL are removed; purge is logged).
4. Vendor assessment hand-off for Hetzner DPA.

---

## 9. Files to create / modify

| File | Action |
|---|---|
| `plans/analytics-compliance.md` | **this doc** |
| `admin-api/migrations/023_audit_log.sql` | create — audit_log table + TTL |
| `admin-api/migrations/024_analytics.sql` | create — analytics.db schema (PII-free roll-ups) |
| `admin-api/scripts/audit.py` | create — `log_event`, PII hashing helpers |
| `admin-api/scripts/admin_server.py` | wire audit events into auth/org/instance/host routes |
| `saas-admin-api/scripts/admin_dashboard_server.py` | add `/admin/v1/analytics/*`, `/admin/v1/audit/*` |
| `data-saas-admin/lib/admin-client.ts` | add analytics types + `getAnalytics()` |
| `data-saas-admin/app/dashboard/analytics/page.tsx` | **new** — product analytics dashboard |
| `data-saas-admin/app/dashboard/security/page.tsx` | **new** — audit log viewer (operator, scoped) |
| `host-agent/service.py` | report host.cpu + aggregate per-org usage to analytics writer |
| `tests/test_audit_privacy.py` | **new** — PII never persists; cross-tenant isolation |
| `tests/test_analytics.py` (admin) | **new** — rollup correctness |

---

## 10. Decision log / open questions

| # | Question | Decision |
|---|---|---|
| 1 | Audit store = `admin.db` vs separate? | Separate section in `admin.db` (same SQLite volume, indexed, TTL-purged). Keeps one DB to sync to the dashboard. |
| 2 | PII stripping: hash vs omit? | **Hash** (SHA-256) the email/IP so events stay correlatable for security review without storing plaintext. |
| 3 | Metrics store: SQLite vs Supabase? | SQLite `analytics.db` for MVP (PII-free, no new dep). Re-evaluate when usage >1M rows/day. |
| 4 | Retention: uniform 90 days? | **No** — 90 days for auth (least need), 365 for infra changes (change mgmt), 3y for GDPR-legal events. Purge is auditable. |
| 5 | Customer access to raw audit? | Yes, scoped to their org, 90-day window, JSONL export. Supports "right to access" + internal security reviews. |
| 6 | Real-time vs batch analytics? | Batch (per-heartbeat for host metrics; per-request for auth/audit). Real-time dashboard via 15s polling (matching the existing AutoRefresh pattern in data-saas-admin). |
