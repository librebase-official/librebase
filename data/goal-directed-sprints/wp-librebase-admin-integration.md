---
workflow_repo: librebase
branch: cursor/librebase-liorg-integration
phase: WP-5
---

# librebase WP-5 — Studio Librebase Admin integration

Replace JSON stores with **Librebase Admin** HTTP client (`LIBREBASE_ADMIN_URL`).

**Naming:** product surface is **Librebase Admin**, not `liorg` (not a linative lip package).

## Tasks

1. `data-studio-ui/lib/librebase-admin-client.ts` — Admin API client
2. Replace `instances-store.ts` / `projects-store.ts` JSON persistence with Admin API calls
3. Wire `OrgShell.tsx`: dynamic org from session
4. `/setup` → first-run self-host (Admin UI)
5. Wire entitlement gates in `project-runtime.ts`, `k8s-provisioner.ts`
6. `deploy/compose/` — `librebase-admin` service (port 54330)
7. Vitest smoke for admin client

## Completion gate

```bash
bash scripts/check-librebase-admin-gate.sh
```
