#!/usr/bin/env bash
# Anonymous shallow fetch of li-langverse lidb/lis from GitLab at a pinned full SHA.
set -euo pipefail

usage() {
  echo "usage: $0 <lidb|lis> <40-char-sha> <dest-dir>" >&2
  exit 2
}

[[ $# -eq 3 ]] || usage
REPO="$1"
SHA="$2"
DEST="$3"

case "$REPO" in
  lidb | lis) ;;
  *) usage ;;
esac

if [[ ! "$SHA" =~ ^[0-9a-f]{40}$ ]]; then
  echo "error: SHA must be 40 hex characters" >&2
  exit 2
fi

URL="https://gitlab.lilangverse.xyz/li-langverse/${REPO}.git"
rm -rf "$DEST"
mkdir -p "$DEST"
cd "$DEST"
git init -q
git remote add origin "$URL"
if ! git fetch --depth 1 origin "$SHA"; then
  git fetch origin "$SHA"
fi
git checkout -q FETCH_HEAD
echo "Checked out ${REPO} @ ${SHA} from GitLab"