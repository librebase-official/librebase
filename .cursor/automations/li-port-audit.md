# Automation prompt: Librebase Li backend port audit

Track progress of the **pure-Li control plane**: lidb (database), li-httpd (web server), Admin API in Li. Frontend stays JS.

**Schedule:** weekly Wed 09:00 UTC · **Repo:** `librebase-official/librebase`

**Skill:** `.cursor/skills/librebase-li-port/SKILL.md`

---

## Read first

1. `docs/sdd/specs/cloud-ga/PLAN.md` (Li-first mandate table)
2. `admin-api/li/README.md`
3. `docs/li-dependency-pins.md`
4. Sibling checkouts when present: `lidb`, `lis`, `li-httpd`, `li-kms`

---

## Audit matrix

| Surface | Interim | Li target | How to verify |
|---------|---------|-----------|---------------|
| Admin API | `admin-api/scripts/admin_server.py` | `admin-api/li/` | smoke `/health`, route table parity |
| DB embed | SQLite in Python | lidb via `src/seam.li` | migrate + SELECT via seam |
| HTTP serve | ThreadingHTTPServer | li-httpd / runtime tcp_* | listen + curl |
| KMS | `kms/` Python | `li-kms` | `make test` / `make test-http` |
| Data plane REST | lis Python routes | lis-rest + li-httpd | parity_runner |

Update `docs/audits/YYYY-MM-DD-li-port.md` with ✅/🟡/❌ and next PR slice. Prefer implementing the next unfinished route family over writing more plans.
