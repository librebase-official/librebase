# Librebase — Agent Handoff

Last updated: 2026-08-15. Snapshot of everything so you can continue in your own harness.

## What this covers

A working Librebase platform MVP: public marketing site + Studio console + admin
control plane (Python, interim) + pure-Li KMS + MCP server + console auth
(GitHub/Google SSO) + billing plan model. Deployed live on an IONOS VPS.

---

## Repos

| Repo | Visibility | Remote | Notes |
|---|---|---|---|
| `librebase-official/librebase` | **PUBLIC** | github.com | Studio (`data-studio-ui`), admin-api, kms, mcp, deploy, docs |
| `librebase-official/librebase-landing` | **private** | github.com | Marketing/landing site (split out of studio) |
| `li-langverse/lic` | GitLab (private) | gitlab.lilangverse.xyz/li-langverse/lic | pure-Li compiler + KMS; branch `feat/li-kms-crypto`, MR #1516 |

`librebase` last commits (main): `9c6e68d` (billing quotas) … `4f7a949` (console-sso OAuth).
`librebase-landing` last: `ffb6e16` (console links). `lic` branch head: `aa4693f` (tcp_recv test).

## Deployed topology (VPS)

Host: **IONOS VPS `87.106.233.16`**, user `root`, SSH alias `librebase-vps` (key `~/.ssh/librebase_vps`).

Containers (podman-compose):
- `librebase_landing_1` — Next.js marketing, `:3006` → **`librebase.xyz`** (apex).
- `librebase_web_1` — Next.js Studio console, `:3005` → **`app.librebase.xyz`**.
- `librebase_admin_1` — Python admin-api, `:54330` (127.0.0.1 only), on shared network `librebase-net`.

Paths on VPS:
- `/opt/librebase/` — studio source (rsync'd from `data-studio-ui/`).
- `/opt/librebase-landing/` — landing source.
- `/opt/librebase-admin/` — admin-api source **+** `docker-compose.yml` (VPS-only, holds secrets).
- nginx config: `/etc/nginx/conf.d/librebase.xyz.conf` (apex→3006, app→3005, both certbot TLS).

DNS (IONOS API, zone `librebase.xyz`, zone id `6da55e19-5fd6-11f1-85a2-0a5864440eb6`):
`librebase.xyz` + `www` + `app` all → `87.106.233.16`. IONOS API creds live in
`/Users/julian/Documents/coding-projects/reeldemo.io/.env.local` (`IONOS_API_PREFIX`,
`IONOS_API_KEY`).

Also exists: homelab `engine` (`192.168.10.40`, user `s4il0r`, key `~/.ssh/homelab`)
— has a stale li-httpd + half-set-up K8s; **not** the production path anymore (apex was repointed to the VPS).

## Deploy procedure (the pattern that works)

```bash
# admin-api (source + secrets compose):
rsync -az --delete --exclude='__pycache__' --exclude='._*' \
  librebase/admin-api/ librebase-vps:/opt/librebase-admin/
rsync -az /tmp/lb-admin-compose.yml librebase-vps:/opt/librebase-admin/docker-compose.yml   # RESTORE after --delete
ssh librebase-vps 'cd /opt/librebase-admin && docker compose build --no-cache && docker compose up -d --force-recreate'

# studio:
rsync -az --delete --exclude=node_modules --exclude=.next --exclude=.git --exclude=.env --exclude='._*' --exclude=__pycache__ \
  librebase/data-studio-ui/ librebase-vps:/opt/librebase/
ssh librebase-vps 'cd /opt/librebase && docker compose build && docker compose up -d --force-recreate'

# landing:
rsync -az --delete --exclude=node_modules --exclude=.next --exclude=.git --exclude=.env --exclude='._*' \
  librebase-landing/ librebase-vps:/opt/librebase-landing/
ssh librebase-vps 'cd /opt/librebase-landing && docker compose build && docker compose up -d --force-recreate'
```

**Gotcha:** `rsync --delete` wipes the VPS-only `docker-compose.yml` (secrets) — always restore it after syncing admin-api. `.env` files are gitignored.

**Gotcha:** podman-compose caches image layers aggressively; when a `COPY`ed file
seems stale, use `docker compose build --no-cache`.

## Secrets (none in git)

| Secret | Where |
|---|---|
| `HETZNER_API_TOKEN` | `librebase/.env` (gitignored) |
| Google OAuth client ID/secret | VPS `/opt/librebase-admin/docker-compose.yml` (+ GCP project `commanding-iris-505518-d0`) |
| GitHub OAuth client ID/secret | same VPS compose |
| admin-api JWT secret | VPS compose (`LIBREBASE_ADMIN_JWT_SECRET`) |
| MCP key (test acct) | `lb_mcp_RLIiShwG6MdXL2_050H2YHDKYMXaTNbi-l6Z6dZxb5U` (in `/admin` console, rotatable) |
| IONOS DNS API | `reeldemo.io/.env.local` |
| gcloud auth | `~/.config/gcloud` (account `julian.m.kleber@gmail.com`) |

## Features + where

- **Console auth** (`admin-api/scripts/admin_server.py`): email/password (Argon2id),
  sessions + refresh, MFA TOTP, roles, rate-limit/lockout, password reset/verify.
- **OAuth SSO** (GitHub + Google): `/org/v1/auth/oauth/start` + `/callback` (admin-api),
  Studio `/api/admin/oauth/start` + `/oauth/callback`; **sign-up + sign-in** (auto-provisions user + personal org).
- **MCP server**: `mcp/librebase_mcp/__main__.py` — 13 tools (users/instances/projects/hosts). Stdio JSON-RPC, no SDK. Env: `LIBREBASE_ADMIN_URL`, `LIBREBASE_MCP_KEY`.
- **Billing/entitlement**: `organizations.edition` (feature gates) + `organizations.plan`
  (`suspended`/`starter` 1-inst/$29 /`pro` 3-inst/$69 /`unlimited` /`self-host`). Quota
  enforced in `POST .../instances`. `POST .../discounts/redeem` maps codes
  (`TEST-UNLIMITED`, `EARLY-ADOPTER`, …) → plan. Default-closed: new orgs are `suspended`.
- **KMS** (`kms/` Python interim + pure-Li in `lic`): envelope AES-GCM + Ed25519; exploit tests in `tests/test_kms_exploits.py`.
- **Landing**: `/` marketing, `/benchmark` (full report + motion video), `/blog`. Private repo.

## Data / test accounts

- admin-api DB is fresh (SQLite volume). Test org: `org_49ed5174e613`
  (email `julian.m.kleber@gmail.com`), plan `unlimited`, edition `cloud-paid`.
- No instances/projects/hosts currently (test data cleaned up).

## Open items / next steps

1. **Stripe billing** (last phase): checkout + metering; webhook sets `plan` (and `edition=cloud-paid`). Discount codes already stubbed.
2. **Delete endpoints** for instances/projects/hosts (admin-api only has launch/stop + provider delete).
3. **"Upgrade plan" UI** in `/admin` console (redeem endpoint exists, no UI).
4. **Hetzner provisioning** (Phase 1): `li-hetzner` (HTTPS client extern done in `lic`), host agent, `admin-api/hetzner.py`.
5. **Instance lifecycle** (Phase 3): scheduler→region, subdomain/ACME, custom domain.
6. **OAuth end-user runtime** (Phase 4): full GoTrue `/auth/v1/*`, SDK link/unlink (registry + PKCE already in `lis`).
7. **Landing deploy key**: use a GitHub deploy key for the private landing repo instead of a PAT on the VPS.
8. **MCP**: add instance/project/host `delete` tools once admin-api has delete endpoints.

## Gotchas / conventions (learned the hard way)

- zsh: `GID` is a **reserved var** (group id) — don't use it as a shell var name.
- `gcloud auth login` needs a browser; run it in the user's own terminal (gcloud on PATH via `/opt/homebrew/bin/gcloud` symlink to the Caskroom SDK).
- Studio client components must call `/api/admin/*` routes (Studio server proxies to admin-api); the browser can't reach the internal `librebase_admin_1:54330` hostname.
- OAuth callback: provider only echoes `state` + `code` — encode `{provider, next}` in state.
- Landing console links must be absolute (`CONSOLE_URL` → `app.librebase.xyz`), not relative.
- `lic` is PR-only (do not self-merge). Build dir on macOS is `build-mac`; set `LI_NATIVE_RT=1 LI_RT_LIB=$PWD/build-mac/runtime/libli_rt.a LI_RT_LIBS=…` for native examples.
- Run admin tests: `cd librebase && .venv/bin/python -m unittest tests.test_admin_api tests.test_admin_providers tests.test_kms tests.test_kms_exploits` (cryptography is in `.venv`).
