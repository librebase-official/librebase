#!/usr/bin/env bash
# Measure PSS RSS for licontainer vs Docker running the same image.
set -euo pipefail

IMAGE="${1:-hello-world}"
REPLICAS="${2:-3}"

echo "==> licontainer RSS (${REPLICAS} containers)"
for i in $(seq 1 "$REPLICAS"); do
  lictl run --name "rss-lc-$i" "$IMAGE" sleep 300 &
done
sleep 2
LC_TOTAL=0
for pid in $(pgrep -f "lirun" 2>/dev/null || true); do
  if [ -f "/proc/$pid/smaps_rollup" ]; then
    pss=$(grep -i Pss /proc/"$pid"/smaps_rollup | awk '{sum+=$2} END {print sum+0}')
    LC_TOTAL=$((LC_TOTAL + pss))
  fi
done
echo "licontainer total PSS: ${LC_TOTAL} kB"
lictl ps 2>/dev/null | tail -n +2 | awk '{print $1}' | xargs -r lictl stop 2>/dev/null || true

if command -v docker >/dev/null 2>&1; then
  echo "==> Docker RSS (${REPLICAS} containers)"
  for i in $(seq 1 "$REPLICAS"); do
    docker run -d --name "rss-dk-$i" "$IMAGE" sleep 300 >/dev/null
  done
  sleep 2
  DK_TOTAL=0
  for cid in $(docker ps -q --filter "name=rss-dk-"); do
    pid=$(docker inspect -f '{{.State.Pid}}' "$cid")
    if [ -f "/proc/$pid/smaps_rollup" ]; then
      pss=$(grep -i Pss /proc/"$pid"/smaps_rollup | awk '{sum+=$2} END {print sum+0}')
      DK_TOTAL=$((DK_TOTAL + pss))
    fi
  done
  echo "Docker total PSS: ${DK_TOTAL} kB"
  docker rm -f $(docker ps -aq --filter "name=rss-dk-") 2>/dev/null || true
else
  echo "Docker not installed — skipping comparison"
fi
