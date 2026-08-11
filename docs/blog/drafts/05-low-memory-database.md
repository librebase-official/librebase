# Why memory footprint matters for agent backends

**Keyword:** low memory database  
**Intent:** informational

Every agent session that holds a connection or process burns RAM. Multiply by concurrent agents and shared staging boxes, and a “small” API that sits on a heavyweight runtime becomes the bill.

Lower footprint helps when you:

- Colocate many projects on one host
- Run local or edge-adjacent boxes
- Keep CI and smoke stacks cheap

Librebase’s Li-native path stays lean: a dedicated instance measures about **3.8 MB RSS** resident on Linux (published CI), with a product target of **64 MB** for a comfortable host, and **Postgres-class** latency and throughput on the core OLTP path. Those numbers are measured and covered by bench gates ([lidb footprint](https://github.com/li-langverse/lidb/blob/main/docs/footprint.md)) and the [marketing unlock checklist](../../../benchmarks/oltp-compare/MARKETING_UNLOCK.md), which is **UNLOCKED**. Caveats hold: the index is an in-memory ordered secondary (`sorted_tree`), not a Postgres disk B-tree, and figures come from Release `lidb_embed` runs. Track performance claims the same way we track features: evidence first.

**CTA:** [librebase.xyz](https://librebase.xyz)
