# Why memory footprint matters for agent backends

**Keyword:** low memory database  
**Intent:** informational

Every agent session that holds a connection or process burns RAM. Multiply by concurrent agents and shared staging boxes, and a “small” API that sits on a heavyweight runtime becomes the bill.

Lower footprint helps when you:

- Colocate many projects on one host
- Run local or edge-adjacent boxes
- Keep CI and smoke stacks cheap

Librebase’s Li-native path **aims** for a lean dedicated instance around **64 MB RSS** steady state and **Supabase/Postgres-class** latency and throughput on the core OLTP path. Those numbers are engineering targets with bench gates ([lidb footprint](https://github.com/li-langverse/lidb/blob/main/docs/footprint.md)) — not a promise until the published harness is green. Track performance claims the same way we track features: evidence first.

**CTA:** [librebase.xyz](https://librebase.xyz)
