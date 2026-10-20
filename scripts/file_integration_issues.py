import subprocess
import sys
import os

BASE = "/Users/julian/Documents/coding-projects"
SCRIPT = os.path.join(BASE, "linear_issues.py")

def create(title, description, labels=""):
    cmd = [sys.executable, SCRIPT, "librebase", "create",
           "--title", title,
           "--description", description]
    if labels:
        cmd.extend(["--label", labels])
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60, cwd=BASE)
    out = r.stdout + r.stderr
    if r.returncode == 0:
        # Extract the issue id
        for line in out.split("\n"):
            if "Created" in line and "LIB-" in line:
                print(f"OK: {line.strip()}")
                return True
    print(f"FAIL ({r.returncode}): {out[-500:]}")
    return False

# LIB-76: Slack integration
create(
    "FEATURE GAP: Slack integration — ops alerts, incident channels, member notifications",
    """## Context

From the competitor integration scan: Slack is the #2 essential integration for dev platforms (Linear's integration ranking). It's the standard channel for ops alerts, incident response, and team notifications.

## What's missing

- No Slack app in LibreBase (our_positioning row 26: `slack-integration`, status=weak)
- No Slack slash commands
- No message→issue flow
- No instance health alerts to Slack
- No billing event notifications to Slack
- No audit log export to Slack

## Competitor reference points

- Linear: native Slack integration — create issues from messages, sync threads, slash commands
- Supabase: Slack notifications for database changes, project events
- Render: Slack alerts for deploy status, service health
- Railway: Slack integration for deploy events, service logs

## Suggested scope

1. Slack app (Bot token + App token) — register in LibreBase admin console
2. Channel subscription per org/project — pick which Slack channel gets which events
3. Event types to push: instance health (running/stopped/error), billing events, audit log entries, member invites, project lifecycle events
4. Slash commands: /librebase status, /librebase instances, /librebase projects
5. OAuth connect flow — user authorizes LibreBase to post to their Slack workspace
6. MCP tool: slack_channel_list, slack_subscribe, slack_unsubscribe

## Why now

Table-stakes triad (webhooks + Slack + observability) — Slack is the ops channel where instance health and billing alerts land. Without Slack, operators don't get timely alerts. This is the second of the three table-stakes integrations.""" ,
    "feature-gap,integrations,baseline,table-stakes"
)

# LIB-77: Observability/logging
create(
    "FEATURE GAP: Observability & logging — structured logs, Sentry/Datadog integration, instance health telemetry",
    """## Context

From the competitor integration scan: observability is the third of the table-stakes triad. Dev platforms surface observability via Sentry, Datadog, Logtail integrations. Operators expect structured logs, error tracking, and instance health dashboards.

## What's missing

- No structured logging surface (our_positioning row 33: `observability-logging`, status=weak)
- No Sentry integration
- No Datadog integration
- No Logtail integration
- No instance health telemetry beyond basic status in Studio
- MCP audit logging exists but instance telemetry is absent

## Competitor reference points

- Supabase: System logs in dashboard, log management, observability integrations
- Firebase: Google Cloud Logging, error reporting, Crashlytics
- Nhost: GraphQL query logging, error tracking
- Render: Service logs, deploy logs, health check logs
- Railway: Log tailing, service logs, observability
- Directus: Audit logs, operation logs, extensibility for external log sinks

## Suggested scope

1. Structured log sink — every instance writes structured JSON logs to a stream
2. Log levels: debug, info, warn, error — filterable per project
3. Error tracking integration — Sentry DSN per project (SDK auto-injects), Datadog API key, Logtail token
4. Instance health dashboard — uptime, latency, error rate, memory/CPU over time (not just "running/stopped")
5. Audit log export — every KMS decrypt, sign, key rotate, member invite, instance lifecycle event logged and exportable
6. MCP tool: log_list (recent logs), log_search (filter by level/instance/time), instance_health (metrics)
7. OTel export option — send traces/spans to an OTel collector URL

## Why now

Third of the table-stakes triad. Without observability, operators fly blind on instance health and can't debug agent-driven operations. This closes the triad (webhooks LIB-75, Slack LIB-76, observability).""",
    "feature-gap,integrations,baseline,table-stakes,observability"
)

# LIB-78: CI/CD hooks + deploy-from-CI
create(
    "FEATURE GAP: CI/CD integration — GitHub Actions hooks, deploy-from-CI, pipeline-triggered instance lifecycle",
    """## Context

From the competitor integration scan: CI/CD integration is expected by dev-platform buyers. Supabase, Render, Railway, and Vercel all surface CI/CD integration. LibreBase has a K8s deploy flow in Studio but no CI pipeline hooks.

## What's missing

- No GitHub Actions integration (our_positioning row 28: `ci-cd-integration`, status=weak)
- No CI pipeline hooks (webhook-triggered or API-triggered)
- No deploy-from-CI flow — agent/CI can't trigger instance launch/migration from a pipeline
- No deploy status webhook back to CI
- No GitHub App for LibreBase (only OAuth SSO for console auth)

## Competitor reference points

- Supabase: GitHub integration, deploy-from-GitHub, Vercel Marketplace one-click provisioning (POSTGRES_URL injection)
- Render: GitHub sync — connect repo, auto-deploy on push, preview deploys
- Railway: GitHub integration, deploy on push, GitHub Actions support
- Vercel: GitHub integration, deploy on push, preview branches, Marketplace
- PocketBase: GitHub Actions for CI/CD of admin UI + migrations

## Suggested scope

1. GitHub App (not just OAuth) — LibreBase registers as a GitHub App, teams install it
2. Repo webhook — push to main triggers: instance_launch + migration_apply + health_check
3. CI pipeline API — POST /org/v1/ci/deploy with { projectId, branch, instanceId } triggers a deploy run
4. Deploy status webhook back to GitHub — commit status on the triggering commit
5. MCP tool: ci_deploy_trigger, ci_deploy_status, ci_pipeline_list
6. Optional: GitHub Actions marketplace action (librebase deploy) — `uses: librebase/deploy@v1`

## Why now

After the table-stakes triad (webhooks, Slack, observability), CI/CD is the next integration gap vs. Supabase/Appwrite/Nhost. It's the deploy-from-code story that dev-platform buyers expect.""" ,
    "feature-gap,integrations,ci-cd,deploy"
)

# LIB-79: Sentry integration (error tracking)
create(
    "FEATURE GAP: Sentry integration — error tracking for agent-driven debugging via MCP",
    """## Context

From the competitor integration scan: Sentry is essential for agent-driven debugging. Sentry has its own MCP server (mcp.sentry.dev) and a Linear Sentry Agent pattern that watches for errors. LibreBase has no Sentry integration today.

## What's missing

- No Sentry integration (our_positioning references Sentry as missing observability)
- No error tracking for instances
- No Sentry DSN per project
- No integration with Sentry's MCP server (mcp.sentry.dev)

## Competitor reference points

- Supabase: Sentry integration available, error tracking
- Vercel: Sentry integration native (Sentry is a Vercel partner)
- Firebase: Crashlytics (Google-owned error tracking)
- Most modern dev platforms: one-click Sentry connect

## Suggested scope

1. Sentry DSN per project — project admin connects a Sentry project, gets a DSN
2. Auto-instrument instance SDK — when LIBREBASE_SENTRY_DSN is set, instance auto-reports errors to Sentry
3. MCP tool: sentry_dsn_list, sentry_dsn_create, sentry_dsn_delete (manage Sentry connections per project)
4. Cross-reference: Sentry MCP server (mcp.sentry.dev) can read Sentry issues — an agent with both LibreBase MCP and Sentry MCP can correlate instance health with error traces

## Why now

Sentry is the standard error tracking tool for dev teams. Its own MCP server means agents can already query Sentry — LibreBase should be the platform that feeds errors into Sentry, not a blind spot. Second-wave integration after the table-stakes triad.""" ,
    "feature-gap,integrations,observability,error-tracking"
)

# LIB-80: Vercel deploy integration
create(
    "FEATURE GAP: Vercel deploy integration — Marketplace listing, one-click provisioning, POSTGRES_URL injection",
    """## Context

From the competitor integration scan: Vercel is both a deploy target and a distribution channel (Vercel Marketplace). Supabase has Vercel Marketplace with one-click provisioning and POSTGRES_URL injection. LibreBase has neither.

## What's missing

- No Vercel Marketplace listing (our_positioning references Vercel as missing in partner ecosystem)
- No one-click provisioning on Vercel
- No POSTGRES_URL / connection string injection to Vercel env vars
- No deploy-from-Vercel flow

## Competitor reference points

- Supabase: Vercel Marketplace — search "Supabase", one-click provision, POSTGRES_URL auto-injected into Vercel project env
- Vercel: AI SDK + MCP via AI SDK (Vercel is an AI SDK player)
- Railway: Vercel-like deploy story but no Marketplace

## Suggested scope

1. Vercel Marketplace listing — "LibreBase" appears in Vercel Marketplace, user clicks "Add to project"
2. On-provision: create a LibreBase project + instance, inject connection string as Vercel env var (LIBREBASE_URL / POSTGRES_URL)
3. OAuth connect — user authorizes LibreBase to manage Vercel project env vars
4. MCP tool: vercel_project_list, vercel_deploy_trigger (trigger a Vercel deployment from LibreBase)

## Why now

Vercel Marketplace is a distribution channel, not just an integration. Supabase gets new users via Marketplace searches. LibreBase's agent-native story could be surfaced similarly — "connect your Vercel project to LibreBase for managed Postgres." This is a growth-channel integration, second wave after CI/CD.""" ,
    "feature-gap,integrations,marketplace,deploy,vercel"
)

# LIB-81: Partner marketplace / extensibility
create(
    "FEATURE GAP: Partner marketplace & extensibility — third-party app/extension catalog, plugin system",
    """## Context

From the competitor integration scan: BaaS platforms increasingly offer marketplaces (Supabase Marketplace, Firebase Extensions, Vercel Marketplace). LibreBase's MCP server is a different wedge (agent-native extensibility) but there's no user-facing app/extension catalog.

## What's missing

- No plugin/extension marketplace (our_positioning row 34: `marketplace-extensibility`, status=weak)
- No third-party app catalog
- No one-click install of extensions (auth hooks, storage transforms, custom migrations, observability sinks)
- No partner ecosystem program

## Competitor reference points

- Supabase: Dashboard Integrations + Partner Catalog + Vercel Marketplace + Stripe Projects — full ecosystem
- Firebase: Extensions (one-click install of pre-built functionality: email, BigQuery export, etc.)
- Vercel: Marketplace (deploy templates, integrations)
- Directus: Marketplace for extensions, bundles
- Appwrite: Marketplace for functions, plugins

## Suggested scope

1. Extension registry — LibreBase-maintained + third-party extensions listed in Studio
2. Extension install flow — install an extension to a project (e.g., "Sentry error sink", "Slack alert broadcaster", "GitHub deploy hook")
3. Extension authoring — SDK for writing LibreBase extensions (type: webhook-sink, oauth-provider, observability-sink, deploy-hook)
4. MCP tool: extension_list, extension_install, extension_uninstall — agents can install extensions via MCP
5. Partner program (future) — partners list their extensions in the catalog

## Why now

Marketplace is a stickiness feature — once teams have extensions installed, they're harder to leave. It also solves the "what integrations do we have?" problem by making them discoverable. This is the ecosystem play after the individual integrations are built.""" ,
    "feature-gap,integrations,marketplace,ecosystem,extensions"
)

# LIB-82: Stripe usage metering (billing gap)
create(
    "FEATURE GAP: Stripe usage metering — per-instance usage-based billing (vs. current plan-based only)",
    """## Context

From the competitor integration scan: Stripe billing is the payment backbone. LibreBase has Stripe checkout/portal/webhook/metering but metering is best-effort (our_positioning row 19: `billing-metering`, status=weak). Competitors with usage-based pricing (Supabase project-based, Firebase MAU-based, Neon compute-hours) offer more flexible billing models.

## What's missing

- Metering is best-effort, not comprehensive (our_positioning row 19: `billing-metering`, status=weak)
- No per-instance usage tracking (storage bytes, compute seconds, API calls)
- No usage-based pricing tier (current plans are flat: starter $29, pro $69, unlimited)
- No meter registry — what are we measuring?

## Competitor reference points

- Supabase: project-based billing, usage metrics in dashboard
- Firebase: MAU-based pricing, usage dashboard
- Neon: compute-hours billing, branching usage
- AWS: granular metering via CloudWatch + Marketplace

## Suggested scope

1. Meter registry — define meters: instance-hours, storage-bytes, API-call-count, bandwidth-bytes
2. Per-instance metering — each instance reports usage to Stripe metering API
3. Usage-based pricing tier — optional: pay per usage above plan allowance
4. Usage dashboard — show usage per project/instance over time, projected bill
5. MCP tool: usage_list, usage_get (per instance/project), usage_project_summary

## Why now

Billing is already strong (Stripe checkout/portal/webhook), but the metering gap means teams on the unlimited plan don't get visibility into usage, and teams on starter/pro can't be charged for overage. This is a billing maturity gap, not a missing integration.""" ,
    "feature-gap,integrations,billing,stripe,usage-metering"
)

# LIB-83: GitHub App + issue/PR sync
create(
    "FEATURE GAP: GitHub App + issue/PR sync — GitHub as dev-platform integration (not just OAuth SSO)",
    """## Context

From the competitor integration scan: GitHub is Linear's #1 essential integration (PR workflows, code review, sync issues, Linear Agent). It's also essential for a dev-platform BaaS — Supabase, Render, Railway all have GitHub Apps, not just OAuth. LibreBase has GitHub OAuth for console auth but no issue/PR integration layer.

## What's missing

- GitHub OAuth SSO works (our_positioning auth row) but no GitHub App
- No issue sync (create LibreBase project from GitHub repo issue?)
- No PR↔instance linking (deploy from PR, preview instance per PR)
- No GitHub App installation flow

## Competitor reference points

- Supabase: GitHub integration, deploy-from-GitHub
- Render: GitHub sync — connect repo, auto-deploy, preview deploys
- Railway: GitHub integration, deploy on push
- Vercel: GitHub integration, preview branches

## Suggested scope

1. GitHub App (not just OAuth) — LibreBase registers as a GitHub App, teams install it on repos
2. Repo connection per project — link a GitHub repo to a LibreBase project
3. PR preview instances — open a PR, get a preview LibreBase instance (branch = PR head)
4. Issue→project flow (optional) — GitHub issue labeled "enhancement" can trigger project create
5. MCP tool: github_repo_list, github_connect, github_disconnect, pr_preview_instance

## Why now

GitHub App is the dev-platform integration that turns LibreBase from "backend you manage in a console" into "backend your CI/CD pipeline talks to." It's the second-wave integration after CI/CD hooks (LIB-78).""" ,
    "feature-gap,integrations,github,ci-cd,dev-platform"
)

# LIB-84: Billing plan upgrade UI
create(
    "FEATURE GAP: Billing plan upgrade UI — finish the 'Upgrade plan' flow that's still open",
    """## Context

From the competitor integration scan: billing is strong (Stripe checkout/portal/webhook/metering) but the UI for 'upgrade plan' is still open (our_positioning row 10: `billing-plans`, status=neutral). The backend is done — checkout, portal, webhook, metering, discount codes — but the user-facing flow to upgrade from starter to pro or unlimited is incomplete.

## What's missing

- 'Upgrade plan' UI is still open (HANDOFF.md open items + our_positioning billing-plans)
- No in-Studio flow to switch plans
- No price display in Studio (prices must be set in VPS admin compose per HANDOFF.md)
- No success URL configured

## What's done

- Stripe checkout session creation
- Stripe portal (billing portal for customers)
- Stripe webhook (checkout.session.completed, customer.subscription.*)
- Metering (best-effort)
- Discount codes (TEST-UNLIMITED, EARLY-ADOPTER, etc.)

## Suggested scope

1. Studio page: /billing or /settings/billing — show current plan, usage, upcoming invoice
2. Upgrade button — opens Stripe checkout for target plan
3. Price display — pull prices from admin compose config (not hardcoded)
4. Success/cancel URLs — configured in Stripe product settings
5. Plan change webhook — on subscription change, update org edition/features

## Why now

Billing backend is done. The UI gap means users can't upgrade without going to the Stripe portal manually. This is a UX completion item, not a new integration.""" ,
    "feature-gap,billing,ui,stripe"
)

# LIB-85: MCP tool count expansion (15 → 30+)
create(
    "MCP GAP: Expand MCP tool count from 15 to 30+ — add billing, usage, logs, health, granular CRUD tools",
    """## Context

The MCP route at app.librebase.xyz/api/mcp implements 17 tools (15 resource + 2 public auth) but the server info reports toolCount. Competitor MCP servers have 13-100+ tools:

- Supabase MCP: 13+ tools (DB query/manage, auth, storage, edge functions, project settings) + open-source Evals framework
- Neon MCP: 12+ categories (projects, branches, endpoints, snapshots, schema, SQL+migrations, auth, data API, observability, docs, functions, storage) + 15 diagnostic checks
- Harper: auto-generates tools from app schema — effectively unlimited, with RBAC at tools/list level

LibreBase today has 15 tools: org_whoami, project_list/create, auth_provider_list/upsert, instance_list/get/create/launch/stop, member_list/invite/update_role, host_list/create, key_list/create/get/decrypt/rotate/update/delete.

Missing tool categories that competitors have:
- Billing/usage: usage_list, usage_get, billing_invoice_list
- Logs/health: log_list, log_search, instance_health
- Schema: run_sql, describe_table, list_tables, schema_migrate, insert/update/delete
- Evals: eval_list, eval_run (agent eval on LibreBase)

## Suggested scope

Phase 1 (data tools): run_sql, describe_table, list_tables, insert/update/delete — database-level MCP tools (the #1 MCP gap)
Phase 2 (ops tools): log_list, log_search, instance_health, usage_list — observability + billing
Phase 3 (schema tools): schema_migrate, eval_list, eval_run — Neon-style migration + Supabase-style evals

This is MCP GAP-3 from the existing issue set (LIB-66). Treat this as the umbrella issue; individual tool additions get their own sub-issues.""" ,
    "feature-gap,mcp,tooling,agent-api"
)

print("\n=== Filing complete ===")
print("LIB-75: Webhooks system (table-stakes triad)")
print("LIB-76: Slack integration (table-stakes triad)")
print("LIB-77: Observability & logging (table-stakes triad)")
print("LIB-78: CI/CD integration + deploy-from-CI")
print("LIB-79: Sentry integration (error tracking)")
print("LIB-80: Vercel deploy + Marketplace listing")
print("LIB-81: Partner marketplace & extensibility")
print("LIB-82: Stripe usage metering (billing gap)")
print("LIB-83: GitHub App + issue/PR sync")
print("LIB-84: Billing plan upgrade UI")
print("LIB-85: MCP tool count expansion 15→30+")
