#!/usr/bin/env bash
# Prefer GitHub CLI OAuth (repo scope) for git/API when GH_TOKEN is a read-only PAT.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
git config --global credential.https://github.com.helper "!${ROOT}/git-credential-github-oauth"

MARKER="# librebase-cloud-agent-github-oauth"
HOSTS="${GH_CONFIG_DIR:-$HOME/.config/gh}/hosts.yml"
if [[ -f "$HOSTS" ]]; then
  oauth="$(awk -F': ' '/oauth_token: / {print $2; exit}' "$HOSTS" | tr -d '"')"
  if [[ -n "$oauth" ]]; then
    export GH_TOKEN="$oauth"
    if ! grep -q "$MARKER" "${HOME}/.bashrc" 2>/dev/null; then
      cat >>"${HOME}/.bashrc" <<'EOF'

# librebase-cloud-agent-github-oauth
if [[ -f "${GH_CONFIG_DIR:-$HOME/.config/gh}/hosts.yml" ]]; then
  _lb_oauth="$(awk -F': ' '/oauth_token: / {print $2; exit}' "${GH_CONFIG_DIR:-$HOME/.config/gh}/hosts.yml" | tr -d '"')"
  [[ -n "$_lb_oauth" ]] && export GH_TOKEN="$_lb_oauth"
fi
EOF
    fi
  fi
fi
