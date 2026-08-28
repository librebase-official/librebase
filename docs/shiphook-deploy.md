# Shiphook deployment integration

Librebase uses a self-hosted Shiphook instance for deployments:

```text
GitHub Actions or an authorized agent
  → POST <SHIPHOOK_DEPLOY_URL>?format=json
  → Shiphook pulls and runs the configured deploy script
  → Shiphook returns the deployment result
```

## Trigger configuration

Add these GitHub Actions secrets:

- `SHIPHOOK_DEPLOY_URL`: public HTTPS Shiphook URL, including its configured path
- `SHIPHOOK_DEPLOY_TOKEN`: Shiphook deployment secret

Requests use:

```http
X-Shiphook-Secret: <deployment-secret>
Content-Type: application/json
```

The JSON response contains `ok`; HTTP `200` alone does not mean deployment success.

## Server configuration

```yaml
port: 3141
repoPath: /opt/librebase
path: /
# Prefer bash so a lost execute bit cannot 444ms-fail the deploy (LIB-21 EACCES).
# If your Shiphook only accepts a single executable path, chmod +x the script
# after clone (`git ls-files -s` shows 100755) and keep core.fileMode true.
runScript: /bin/bash
runArgs: ["/opt/librebase/scripts/deploy-production.sh"]
runTimeoutMs: 1800000
```

The deploy script owns Librebase-specific build, restart, health, version, and commit checks. Expose Shiphook through HTTPS and keep the deployment secret in the server secret store.

One-time repair if spawn reports `EACCES`: `chmod +x /opt/librebase/scripts/deploy-production.sh` (and `git config core.fileMode true` in `/opt/librebase`). The next pull of a content change also restores the tracked 100755 mode.

## Deployment status feed

The deployment-status feed is a separate Shiphook feature, not a Librebase endpoint. It is read-only and protected by a dedicated feed token:

```http
GET <SHIPHOOK_EVENTS_URL>?limit=20
Authorization: Bearer <events-read-token>
```

It returns bounded, newest-first, sanitized deployment metadata and never exposes secrets, environment values, or raw command output. It cannot trigger deployments. The feed token is distinct from the deployment trigger secret.

## Safe rollout

1. Test Shiphook against staging.
2. Confirm the deployment response reports `ok: true`.
3. Verify Studio, admin API, hosted MCP, version, and database health.
4. Confirm the status feed reports the completed deployment.
5. Configure production only afterward.
