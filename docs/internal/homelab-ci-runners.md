# Homelab GitHub Actions runners (Librebase)

GitHub-hosted runners cannot reach `https://stage.librebase.xyz/` on the Fritz LAN. Use the org scale set **`librebase-homelab`** on homelab k3s.

## Workflow labels

```yaml
runs-on: [self-hosted, librebase-homelab, linux]
```

Optional repo variable: `LIBREBASE_SELF_HOSTED_RUNNER=true` (mirror Majico’s `MAJICO_SELF_HOSTED_RUNNER` pattern when you wire homelab-only jobs).

## Infra

Install and tokens: [cap-jmk-launchpad/homelab-k3s — `docs/github-actions-homelab-runners.md`](https://github.com/cap-jmk-launchpad/homelab-k3s/blob/main/docs/github-actions-homelab-runners.md).

Build/push to GHCR in `.github/workflows/staging-deploy.yml` can stay on `ubuntu-latest`; use homelab runners for kubectl, integration tests against stage, or LAN-only services.
