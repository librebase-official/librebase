# LibreBase — Soul

**LibreBase** is the open knowledge base and competitive intelligence platform — the
Supabase-shaped open data platform people use to store, structure, and surface
research, market data, and org knowledge without lock-in.

**librebase.xyz** is the public face (landing, marketing, benchmarks). **app.librebase.xyz**
is the **Librebase Studio** web console where orgs, projects, and databases actually live.

---

## What it is

- **Open data platform** — Supabase-shaped stack (orgs → instances → projects → databases),
  self-hostable, GPL-3.0-or-later.
- **Powered by `lidb`** — the database/runtime core. Lidb and Librebase Studio are the
  monetized product surfaces.
- **Librebase Studio** — the web console for org/project/database workflows. Your day-to-day
  interface to the platform.
- **Open by default** — knowledge should be findable, attributable, and freely reusable.
  The core (`lis` supervisor/registry, `lidb`) stays general-purpose and linative; the
  commercial Librebase layer sits on top.

---

## What it is not

- Not a locked-in SaaS data silo. Self-hostable, exportable, portable.
- Not a general-purpose org/catalog library. **Librebase Admin** is product code in this
  repo — not `liorg` or any lip package.
- Not finished. Billing/entitlement gates are planned; marketing says *aim/target* until
  CI benches publish green rows. Honesty over invented metrics.

---

## The north stars

|| Star | Meaning |
|-----|-------|---------|
| **Open** | Knowledge free to find, attribute, and reuse. GPL core; commercial layers optional. |
| **Lean** | Dedicated instance ≤ 64 MB RSS steady state (north star; ≤ 256 MB current gate). |
| **Fast** | Supabase-class core-path latency/throughput vs Postgres 16 on equal hardware. |
| **Honest** | No fake green status. No invented MB numbers. No "as fast as Supabase" without evidence. |
| **Simple** | Org → Instance → Project. Dedicated (1:1) and shared (1:N) both supported. |

---

## The feeling

LibreBase is the tool you point at a messy pile of market research, competitor intel,
structured data, and org knowledge and turn it into something a team can actually use —
without handing the keys to a vendor. It should feel like a small, honest database
platform that respects your data and your freedom to leave.

The aesthetic: spare, purposeful, no-drama. When it works, you don't notice it — your
data is just there, queryable, shareable, and yours.

---

## For agents and contributors

See `.cursor/rules/librebase-product.mdc` for product context, monetization intent,
instance/project model, and build boundaries.

**Key bounds to remember:**
- `lidb` + Librebase Studio = paid/commercial surfaces. Gate paid capabilities; don't
  expose them without entitlement.
- Keep the open `lis` core separable from the commercial Librebase layer.
- `licontainer/` is **pure Li only** — no Rust, no C, no Python. `def` only, `extern def`
  for trusted FFI.
- `registry-min.toml` excludes Studio — Studio is opt-in/commercial-shaped.
- License: GPL-3.0-or-later; commercial packaging may diverge for paid tiers.

---

*LibreBase — open knowledge, owned by the people who use it.*
