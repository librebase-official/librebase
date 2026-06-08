#!/usr/bin/env bash
# Time cold start: pull + run for licontainer vs Docker.
set -euo pipefail

IMAGE="${1:-hello-world}"

echo "==> licontainer cold start"
START=$(date +%s%N)
lictl pull "$IMAGE"
lictl run --name cold-lc "$IMAGE" echo done
END=$(date +%s%N)
LC_MS=$(( (END - START) / 1000000 ))
echo "licontainer: ${LC_MS} ms"
lictl stop cold-lc 2>/dev/null || true

if command -v docker >/dev/null 2>&1; then
  echo "==> Docker cold start"
  docker rmi "$IMAGE" 2>/dev/null || true
  START=$(date +%s%N)
  docker pull "$IMAGE"
  docker run --rm --name cold-dk "$IMAGE" echo done
  END=$(date +%s%N)
  DK_MS=$(( (END - START) / 1000000 ))
  echo "Docker: ${DK_MS} ms"
else
  echo "Docker not installed — skipping comparison"
fi
