# Shiphook deployment

The GitHub Actions workflow calls a self-hosted Shiphook instance. Shiphook authenticates the request, runs its configured pull-and-deploy operation, and returns the deployment result synchronously as JSON.

## GitHub setup

Add these Actions secrets:

- `SHIPHOOK_DEPLOY_URL`: public HTTPS Shiphook webhook URL, including its configured path
- `SHIPHOOK_DEPLOY_TOKEN`: value configured as Shiphook `secret`

The workflow sends:

```http
POST <SHIPHOOK_DEPLOY_URL>?format=json
X-Shiphook-Secret: <secret>
Content-Type: application/json
```

```json
{
  "ref": "main",
  "repository": "librebase-official/librebase",
  "event": "github_actions"
}
```

Shiphook must run with the Librebase checkout and deploy script configured, for example:

```yaml
port: 3141
repoPath: /opt/librebase
path: /deploy
runScript: /opt/librebase/scripts/deploy-production.sh
runTimeoutMs: 1800000
```

The deploy script owns the application-specific work: build/restart containers, wait for health, verify the deployed commit/version, and exit nonzero on failure. Shiphook’s successful HTTP response then represents a successful deployment.

Expose port `3141` through HTTPS using nginx or another reverse proxy. Keep the Shiphook secret in GitHub Actions secrets or the server secret store; never put it in source, logs, Grok chat, or ordinary repository variables.

## Safe rollout

1. Configure a staging Shiphook instance and secret.
2. Run **Actions → Deploy via Shiphook → Run workflow** manually against staging.
3. Confirm the JSON response reports `ok: true` and inspect its deployment log.
4. Verify Studio, admin API, hosted MCP, version, and database health.
5. Configure separate production URL and secret only afterward.

The workflow serializes production deployments so two runs do not operate on the same target concurrently.

## Grok Bot instruction

> Trigger the Librebase Shiphook webhook for the `main` branch. Wait for the synchronous JSON response and report whether the deploy result has `ok: true`. Then verify Studio, admin API, hosted MCP, deployed commit, and Librebase version. Report duration and failure output when present. Never reveal the Shiphook secret.
