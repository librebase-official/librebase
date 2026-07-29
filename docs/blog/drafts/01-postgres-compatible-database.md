# What is a Postgres-compatible database?

**Keyword:** postgres compatible database  
**Intent:** informational

A Postgres-compatible database speaks the Postgres wire protocol (or a close dialect) so existing drivers, ORMs, and migration tools keep working. You get SQL you already know, plus whatever the vendor adds on top — Auth, REST, Realtime, Studio.

Compatibility is not a slogan. It means:

- Clients connect with standard Postgres tooling when the wire path is up.
- SQL dialects and types behave close enough that apps do not need a rewrite.
- Gaps (extensions, exotic types, admin features) are documented — not hidden behind a green badge.

Librebase aims at that shape: Postgres-compatible core, Auth/REST/Realtime for apps and agents, and a capability matrix that stays incomplete until tests pass.

**CTA:** [Join the Librebase waitlist](https://librebase.xyz/#waitlist)
