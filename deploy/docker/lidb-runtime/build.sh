#!/usr/bin/env sh
set -e

ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
IMAGE="${LIBREBASE_RUNTIME_IMAGE:-librebase/lidb-runtime:dev}"

echo "Building ${IMAGE} from ${ROOT}"
docker build -f "${ROOT}/deploy/docker/lidb-runtime/Dockerfile" -t "${IMAGE}" "${ROOT}"
echo "Built ${IMAGE}"
echo "Load into kind: kind load docker-image ${IMAGE} --name librebase"
