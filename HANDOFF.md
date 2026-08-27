# Librebase — Agent Handoff

Last updated: 2026-08-15 (Stripe billing backend + waitlist fix).

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
| `li-langverse/lic` | GitLab (private) | gitlab.lilangverse.xyz/li-langverse/lic | pure-Li compiler. MR #1516 (`feat/li-kms-crypto`) **merged** (commit `b1d60e14`) + MR #1519 (no-downstream-deps rule) **merged** (`d60ecabf`) on 2026-08-16. |
| `li-langverse/li-kms` | **PUBLIC** | github.com | pure-Li KMS self-contained: `src/kms_*.li`, runtime crypto externs + Monocypher, `seam/kms-runtime-seam.li` (KMS extern decls), `make test`/`verify`. Tests verified on toolchain (selftests exit 0, HTTP API round-trips). |
| `li-langverse/lic-sprint` | GitLab (private) | gitlab.lilangverse.xyz/li-langverse/lic-sprint | goal-sprint repo. **MR #1 open** (2026-08-16): WP-B8 agentic surface in `li-mail-gateway` (agentic.li + routes + TTS ops + docs; selftest exit 0 on lic). |

`librebase` last commits (main): `9c6e68d` (billing quotas) … `4f7a949` (console-sso OAuth).
`librebase-landing` last: `ffb6e16` (console links). `lic` branch head: `aa4693f` (tcp_recv test).

## Deployed topology (VPS)

**Production — VPS #2 `87.106.2.129`**, user `root`, SSH alias `librebase-vps2`.
DNS: `librebase.xyz` + `app.librebase.xyz` → `87.106.2.129`.

Containers (docker-compose):
- `librebase_web_1` — Next.js Studio console, `:3005` → **`app.librebase.xyz`**.
- `librebase_admin_1` — Python admin-api, `:54330` (127.0.0.1 only), on shared network `librebase-net`.

**Backup — VPS #1 `87.106.233.16`**, user `root`, SSH alias `librebase-vps` (key `~/.ssh/librebase_vps`).
SSH key currently rejected — needs root password to re-add. Reserved as personal backup server.

Staging (isolated, 2026-08-20): separate stack on same VPS, separate Postgres DB + JWT secrets:
- `supabase-staging-db` — standalone `postgres:16-alpine`, `:54332` → `:5432` (container).
- `librebase_staging_admin` — staging admin-api (dual-backend, Postgres via `LIBREBASE_DB_DSN`), `:54331` → `:54330`.
- `librebase_staging_web` — staging studio console, `:3007` → `:3005`.
- `librebase-staging-kms` — staging KMS, `:54340`.
- nginx: **`app-stage.librebase.xyz`** → `127.0.0.1:3007` (studio) + `/admin-api/` → `127.0.0.1:54331`.
- Staging compose: `/opt/librebase-admin-staging/docker-compose.staging.yml`. Staging deploy script: `deploy/deploy-staging.py` (`python3 deploy/deploy-staging.py [--rebuild]`).

Paths on VPS:
- `/opt/librebase/` — studio source (rsync'd from `data-studio-ui/`).
- `/opt/librebase-landing/` — landing source.
- `/opt/librebase-admin/` — admin-api source **+** `docker-compose.yml` (VPS-only, holds secrets).
- nginx config: `/etc/nginx/conf.d/librebase.xyz.conf` (apex→3006, app→3005, both certbot TLS).

Supabase (self-hosted on the VPS, shared prod): podman compose project `supabase` in
`/opt/majico-supabase/supabase-src/docker/` — 12 containers (`supabase-kong` 8000/8443,
`supabase-rest`=PostgREST v14, `supabase-auth`=GoTrue, db, storage, …). Public domain
`supabase.majico.xyz` → nginx `/etc/nginx/conf.d/supabase.majico.xyz.conf` → Kong. **2026-08-15:**
`proxy_pass` was pointed at the `127.0.0.1:30100` SSH reverse-tunnel (stale, PGRST301 "None of
the keys was able to decode the JWT") and is now back to the local Kong `127.0.0.1:8000`
(backup conf: `supabase.majico.xyz.conf.bak-20260815`). Credentials: `/root/majico-supabase-credentials.env`
(`JWT_SECRET`, `ANON_KEY`, `SERVICE_ROLE_KEY`; all signed with the SAME `JWT_SECRET` as
`docker/.env`). Librebase waitlist + sail.black use `LIBREBASE_SUPABASE_URL=…majico.xyz` +
service-role key; those keys verify fine against the local Kong/PostgREST.

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
- **MCP server**: `mcp/librebase_mcp/__main__.py` — 15 tools (org/projects/instances/members/hosts + `auth_provider_list`/`auth_provider_upsert`). Stdio JSON-RPC, no SDK. Env: `LIBREBASE_ADMIN_URL`, `LIBREBASE_MCP_KEY`.
- **Billing/entitlement**: `organizations.edition` (feature gates) + `organizations.plan`
  (`suspended`/`starter` 1-inst/$29 /`pro` 3-inst/$69 /`unlimited` /`self-host`). Quota
  enforced in `POST .../instances`. `POST .../discounts/redeem` maps codes
  (`TEST-UNLIMITED`, `EARLY-ADOPTER`, …) → plan. Default-closed: new orgs are `suspended`.
- **Stripe billing** (admin-api, stdlib-only urllib — no SDK): `POST /org/v1/orgs/{o}/billing/session`
  (checkout, plans `starter`/`pro`), `.../billing/portal`, `GET .../billing`, and the signed
  webhook `POST /org/v1/billing/webhook` (`checkout.session.completed` → plan + `edition=cloud-paid`;
  `customer.subscription.updated/deleted` → keep/sub/plan in sync). `011_stripe.sql` adds
  `stripe_customer_id/subscription_id/price_id/status`. Overage metering: on instance launch,
  best-effort `stripe_report_usage()` only when `LIBREBASE_STRIPE_METERED_PRICE` is set.
  Env: `LIBREBASE_STRIPE_API_KEY`, `LIBREBASE_STRIPE_WEBHOOK_SECRET`,
  `LIBREBASE_STRIPE_PRICE_STARTER/PRO`, `LIBREBASE_STRIPE_SUCCESS_URL/CANCEL_URL/PORTAL_RETURN_URL`,
  `LIBREBASE_STRIPE_API_URL` (test override), keys live in VPS admin compose.
- **Waitlist**: Studio `app/api/waitlist/route.ts` writes Supabase `librebase_waitlist`
  (`LIBREBASE_SUPABASE_URL`/`SERVICE_ROLE_KEY`). Landing proxies through its own
  `app/api/waitlist/route.ts` → `https://app.librebase.xyz/api/waitlist` (env `LIBREBASE_WAITLIST_UPSTREAM`).
- **KMS** (`kms/` Python interim + pure-Li in `lic`): envelope AES-GCM + Ed25519; exploit tests in `tests/test_kms_exploits.py`.
- **Landing**: `/` marketing, `/benchmark` (full report + motion video), `/blog`. Private repo.

## Data / test accounts

- admin-api DB is fresh (SQLite volume). Test org: `org_49ed5174e613`
  (email `julian.m.kleber@gmail.com`), plan `unlimited`, edition `cloud-paid`.
- No instances/projects/hosts currently (test data cleaned up).

## Open items / next steps

1. ~~**Stripe billing**~~ Backend done (2026-08-15): checkout/portal/webhook/metering + `011_stripe.sql`.
   Not yet wired into Stripe dashboard webhook URL, and prices/success URLs must be set in the
   VPS admin compose. UI still open (item 3).
2. **Delete endpoints** for instances/projects/hosts (admin-api only has launch/stop + provider delete).
3. **"Upgrade plan" UI** in `/admin` console (redeem endpoint + new `billing/session` exist, no UI).
4. **Hetzner provisioning** (Phase 1): `li-hetzner` (HTTPS client extern done in `lic`), host agent, `admin-api/hetzner.py`.
5. **Instance lifecycle** (Phase 3): scheduler→region, subdomain/ACME, custom domain.
6. **OAuth end-user runtime** (Phase 4): full GoTrue `/auth/v1/*`, SDK link/unlink (registry + PKCE already in `lis`).
7. **Landing deploy key**: use a GitHub deploy key for the private landing repo instead of a PAT on the VPS.
8. **MCP**: add instance/project/host `delete` tools once admin-api has delete endpoints.
9. ~~**lic rule MR**~~ Merged (#1519). Rule committed on `main` (commit `d60ecabf`).

## li-kms verification + carve (2026-08-16)

- Verified on the lic toolchain (homelab, `feat/li-kms-crypto` worktree + built
  `li_rt` runtime incl. `li_rt_cuda_infer.o` for the LIG symbols): all 4 Li
  selftests exit 0; `kms_http` serves health/404; `kms_server` round-trips
  encrypt→decrypt and sign→verify. Toolchain note: native link needs
  `li_rt_cuda_infer.o` in libli_rt.a (CMake target omits it), `LI_NATIVE_RT=1`,
  `LI_RT_LIB`/`LI_RT_LIBS` = libli_rt.a.
- Removed from `lic` MR #1516 (commit `85a6463e`): `examples/kms_*.li`,
  `runtime/li_rt_crypto.{c,h}`, `runtime/vendor/monocypher/`, KMS extern decls
  in `std/runtime/seam.li`, `runtime/CMakeLists.txt` entries. **Kept** in lic:
  `tcp_recv` full-request read (+ `net_trusted` regression), rng `int`→`ptr` fix,
  `bytes_slice_i`/`bytes_append_i` surface.
- li-kms repo owns the removed seam decls (`seam/kms-runtime-seam.li`) and a
  toolchain-free `make verify` C parity harness.

## Mail service status (2026-08-17)

- `dev@librebase.xyz` provisioned (mbx_000059 / dom_000049) + **email service unblocked**.
  Deployed `ghcr.io/li-langverse/li-mail-gateway:unblocked` — 1/1 on blackpearl, 0 restarts.
  `/v1/mail/*` control plane + `/v1/mail/auth/verify` are live; webmail/mcp/operator-admin tiers
  reach them via the gateway svc.
- Blocker that was hit: lic codegen hardcodes `-march=native` (AVX-512 on Zen4 engine) → SIGILL
  on blackpearl (Ryzen 5500U). Fixed by a compiler wrapper remapping to `-march=x86-64-v2`.
  Full recipe (build env, file moves, docker base + libpq5, deployment port/`curlPolicy` patches)
  is in project memory "unblocking li-mail-gateway".

## Gotchas / conventions (learned the hard way)

- zsh: `GID` is a **reserved var** (group id) — don't use it as a shell var name.
- `gcloud auth login` needs a browser; run it in the user's own terminal (gcloud on PATH via `/opt/homebrew/bin/gcloud` symlink to the Caskroom SDK).
- Studio client components must call `/api/admin/*` routes (Studio server proxies to admin-api); the browser can't reach the internal `librebase_admin_1:54330` hostname.
- OAuth callback: provider only echoes `state` + `code` — encode `{provider, next}` in state.
- Landing console links must be absolute (`CONSOLE_URL` → `app.librebase.xyz`), not relative.
- Waitlist: the landing app has its OWN `/api/waitlist` route that proxies to the Studio one —
  don't remove it. Supabase REST writes only work if nginx routes `supabase.majico.xyz` to the
  local Kong (`127.0.0.1:8000`), never to the `30100` SSH tunnel (that copy has a different JWT secret).
- `lic` is PR-only (do not self-merge). Build dir on macOS is `build-mac`; set `LI_NATIVE_RT=1 LI_RT_LIB=$PWD/build-mac/runtime/libli_rt.a LI_RT_LIBS=…` for native examples.
- Run admin tests: `cd librebase && .venv/bin/python -m unittest tests.test_admin_api tests.test_admin_providers tests.test_kms tests.test_kms_exploits tests.test_mcp` (cryptography is in `.venv`).
