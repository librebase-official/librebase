# Shiphook deployment

`.github/workflows/shiphook-deploy.yml` deploys `main` through Shiphook and waits for the returned deployment URL to answer `GET /health` with HTTP 200.

## GitHub setup

Add these **Actions secrets** to the repository (Settings → Secrets and variables → Actions):

- `SHIPHOOK_DEPLOY_URL`: Shiphook deploy webhook URL
- `SHIPHOOK_DEPLOY_TOKEN`: Shiphook sender/API token

The token is sent only as an `Authorization: Bearer` header. It is never written to logs or committed to the repository.

The workflow runs on pushes to `main` and can also be started manually with a deploy ref. It expects Shiphook to accept a JSON body containing `ref`, `commit`, `repository`, and `event`, and to return JSON containing a deployment URL in one of `deployment_url`, `url`, or `deploy_url`.

The returned deployment URL must expose:

```text
GET <deployment-url>/health → 200
```

A failed trigger, missing deployment URL, or health timeout fails the workflow. The workflow uses a concurrency lock so production deployments do not overlap.

## Test safely

1. Configure the secrets with a staging Shiphook routine first.
2. Run **Actions → Deploy via Shiphook → Run workflow** against the staging ref.
3. Confirm the job summary includes the commit and deployment URL.
4. Only then point `SHIPHOOK_DEPLOY_URL` at the production routine.

No live deployment was triggered while adding this workflow because the Shiphook URL and token are not available in the repository context.

## Message for Grok Bot

> Deploy Librebase from the public GitHub `main` branch through the Shiphook routine. After Shiphook returns the deployment URL, poll `<deployment-url>/health` until it returns HTTP 200. Report the GitHub commit, Librebase version, deployment URL, elapsed time, and any failed health checks to the Librebase team panel. Do not expose the Shiphook token. If the deployment or health check fails, keep the failure details and URL for investigation; do not retry indefinitely.
