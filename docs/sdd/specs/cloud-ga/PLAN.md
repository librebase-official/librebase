# Librebase Cloud — GA plan

Status: **locked** · Date: 2026-08-14 · Owner: Librebase

Self-operated cloud platform: provision Hetzner VMs to users, host
multi-tenant Librebase instances on them (Podman), ship a customer-facing KMS,
and let project owners configure OAuth providers (Supabase parity). Greenfield
(no users to migrate).

## Confirmed decisions

| Decision | Choice |
|---|---|
| VM substrate | Hetzner Cloud (multi-region: EU `fsn1`/`nbg1`/`hel1`, US `ash`/`hil`) |
| Tenancy | many VMs per org, many instances per VM (shared host, per-instance isolation) |
| Container runtime | Podman (on the VM) |
| Host agent | **pure Li** (`lic` binary) — thin supervisor |
| OAuth providers | GitHub + Google first; provider registry → full Supabase parity |
| KMS | Librebase's own, **customer-facing day one**: encrypt/decrypt + **sign/verify** + key lifecycle |
| Console auth | email/password + reset + TOTP + roles; console SSO (GitHub/Google) as follow-on |
| Domain | always-on `<project>.librebase.xyz`; optional custom domain |
| Control plane | Librebase-hosted (`admin-api`, interim Python, later Li) |
| Billing | Stripe (checkout + metering) |

## Architecture

```
Hetzner VMs (multi-region)
 └─ host agent (pure Li) ── Podman ── lidb-runtime instances (multi-tenant)
Control plane: admin-api (orgs/hosts/instances/projects/domains/entitlements/billing)
KMS (pure Li): customer keys, encrypt/decrypt, sign/verify, rotation
Edge: Traefik + ACME — default + custom domains → instance
Clients: SDK (signInWithOAuth) + Studio console
```

## Schema additions (`admin-api/migrations/`)

| Table | Fields |
|---|---|
| `hosts` (extend) | `server_id`, `ip`, `region`, `provider="hetzner"`, `status`, `mem_mb` |
| `instances` (extend) | `host_id`, `container_id`, `hostname`, `ports`, `status` |
| `domains` | `project_id`, `hostname`, `kind(default|custom)`, `status(pending|verified)`, `tls_ready` |
| `auth_providers` | `project_id`, `provider`, `client_id`, `client_secret_enc`, `redirect_uris`, `enabled` |
| `kms_keys` | `project_id`, `key_id`, `key_version`, `encrypted_dek` |
| `sessions` | console session + refresh (rotation, revocation) |
| `email_verifications`, `password_reset_tokens`, `mfa_secrets` | console auth |

## Phases (ordered, with dependencies)

### 1. Hetzner substrate + host agent
- `admin-api/hetzner.py`: create/destroy/list server, SSH keys, firewall, private net, regions.
- **Host agent (pure Li):** cloud-init → Podman + `lic` binary. Supervisor over Podman
  (`run`/`stop`/`health`/`status`) reporting to admin-api. **Lock the agent↔admin
  protocol first, then implement.**
- Register VMs into `hosts`; GHCR-publish `lidb-runtime` prod image.

### 2. KMS (customer-facing, full crypto)
- Envelope encryption: KEK (bootstrapped on first boot) → per-project DEKs
  (AES-256-GCM); **Ed25519 sign/verify** via the Li crypto seam.
- Customer API (pure Li): `create/list/rotate/delete key`, `encrypt/decrypt`,
  `sign/verify`, `get_public_key`, key versions; project + service-role scoped.
- Internal: encrypt `auth_providers.client_secret` with project DEK; KEK custody
  = key file + rotation + audit.
- **v1 scope:** symmetric envelope + Ed25519 sign/verify only (defer asymmetric
  encrypt / delegated envelopes).

### 3. Instance lifecycle + exposure (region + domain)
- Scheduler → host in chosen region (mem headroom); `stopped→running/degraded`.
- **Always-on default subdomain** `<project>.librebase.xyz` (Hetzner DNS + ACME).
- **Optional custom domain** (CNAME + ACME verification → TLS), second half.
- Traefik fronting; `domains` table + verification.

### 4. OAuth providers (end-user runtime)
- `lis/routes/auth/oauth.py` → provider registry (GitHub, Google → GitLab/Azure/Apple),
  per-project config, PKCE, per-project state store, redirect-URI validation;
  secrets via KMS; GoTrue `/auth/v1/*` completed.
- SDK: `signInWithOAuth({provider})`, `getProviders()`, link/unlink.

### 5. Console auth (operator sign-in)
Assumptions (flagged): console SSO later; no magic link; multi-org picker deferred.

- Session: access JWT + rotating refresh; `sessions` table (logout/revocation);
  per-request cookie resolution (drop `process.env.LIBREBASE_ADMIN_SESSION` hack);
  CSRF + `secure` cookies.
- Password: pbkdf2 → **Argon2id**; lockout + rate limiting; forgot/reset (email
  token via `smtp.py`); email verification on signup/invite.
- MFA: reuse `lis/routes/auth/mfa.py` TOTP + recovery codes.
- Console SSO (follow-on): GitHub/Google via the same provider registry + KMS;
  wire existing `users.oauth_sub`.
- Roles: enforce `owner/admin/member` granularity in admin-api + Studio.
- Invites: accept → set password + verify.
- Studio wiring: `lib/librebase-admin-client.ts` refresh/logout/role-guard;
  `app/login`, `app/setup`, `app/api/admin/*`.
- Signing: admin JWTs on a KMS-held, rotatable key.

### 6. Studio UI
- Project → **Auth → Providers**, **Domains**, **KMS keys**, **Create VM/instance
  (region)**; instance health/logs; console login/setup/org screens.

### 7. Billing
- Stripe checkout + metering (per-VM, per-instance mem/uptime);
  `cloud-free` vs `cloud-paid` gating on `instance.launch`/`host.create`.

### 8. Ops/security
- KEK rotation, secret audit, host monitoring, VM decommission (drain), login audit.

## Dependencies
`2 KMS` feeds `4 OAuth` and `5 console` (secrets + JWT keys). `1 substrate` feeds
`3 lifecycle`. `3` is a prerequisite for `4` (a project needs a running instance
for OAuth redirects). `6 UI` spans `2/3/4/5`. `7 billing` parallelizable.

## Touch points (repo → file)

| Area | Files |
|---|---|
| Control plane | `admin-api/scripts/admin_server.py`, `admin-api/scripts/hetzner.py` (new), `admin-api/migrations/*` |
| Host agent | net-new pure-Li binary + `deploy/docker/lidb-runtime` image |
| KMS | net-new pure-Li service (lis route or `li-kms` sibling) |
| Runtime auth | `lis/routes/auth/{oauth,handlers,mfa,smtp,store}.py` |
| SDK | `packages/sdk/src/index.js` |
| Studio | `data-studio-ui/app/(studio)/(cloud)/projects/[projectId]/settings/page.tsx`, `app/login`, `app/setup`, `app/api/admin/*`, `lib/{librebase-admin-client,entitlements,hosts-store,instances-store,domains-store,kms-store}.ts` |

## Risks
- **KMS sign/verify** is the largest new surface — v1 scope above keeps it shippable.
- **Pure-Li host agent** is the linchpin — lock its protocol before code.
- **Custom domains** — default subdomain first, custom second.
