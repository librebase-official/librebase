---
workflow_repo: librebase
branch: cursor/librebase-liorg-integration
phase: WP-5
worker: librebase-liorg-klaut
---

# librebase WP-5 — Studio liorg integration

Replace JSON stores with liorg HTTP client (`LIBREBASE_ORG_URL`).

## Tasks

1. Add `data-studio-ui/lib/liorg-client.ts` — HTTP client for liorg API
2. Replace `instances-store.ts` / `projects-store.ts` JSON persistence with liorg calls
3. Wire `OrgShell.tsx`: dynamic org from session, org switcher
4. `/setup` → POST `/org/v1/setup` (self-host only)
5. Wire entitlement TODOs in `project-runtime.ts`, `k8s-provisioner.ts`
6. Add liorg service to `deploy/compose/` (port 54330)
7. Vitest smoke: login → create project → list projects

## Completion gate

```bash
bash scripts/check-librebase-liorg-gate.sh
```

Run from librebase repo root. liorg must be reachable at `LIBREBASE_ORG_URL`.
