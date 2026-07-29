# What is an agentic database?

**Keyword:** agentic database  
**Intent:** informational

An agentic database is built so autonomous clients can operate it: create projects, check health, run SQL-shaped workflows, and respect Auth/RLS — without assuming a human in the Studio UI.

That usually means:

- **MCP or equivalent** tool surface
- **REST** for app and agent HTTP clients
- **Security defaults** (Auth, RLS) that survive automated writers
- **Operational honesty** so agents do not retry against a lying healthy flag

Librebase ships MCP alongside REST and Studio. Agents get tools; humans get the console.

**CTA:** [Join waitlist](https://librebase.xyz/#waitlist)
