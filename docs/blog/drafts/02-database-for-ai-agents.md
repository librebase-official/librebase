# Why AI agents need a database stack that keeps up

**Keyword:** database for ai agents  
**Intent:** informational

Agents open many short sessions, call APIs at machine speed, and expect Auth on every request. A monolith tuned for human dashboards often fails that pattern: heavy memory, opaque health, and APIs that assume a single interactive user.

What agents actually need:

1. **Small footprint** — dense hosts, many projects, less RAM waste.
2. **Auth and RLS in the path** — not bolted on after the first breach.
3. **Machine APIs** — REST and MCP so agents can query and operate without a human clicking Studio.
4. **Honest status** — degraded modes labeled, not painted green.

Librebase is a Postgres-compatible platform aimed at that workload: written in Li for a native, low-overhead runtime, with Studio for humans and MCP for agents.

**CTA:** [librebase.xyz](https://librebase.xyz)
