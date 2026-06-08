#!/usr/bin/env bash
# Export deploy/docker/lidb-runtime as OCI layout + optional squashfs via liimg/lictl.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE_NAME="${LIBREBASE_OCI_IMAGE:-ghcr.io/librebase-official/lidb-runtime:oci-squashfs}"
DOCKERFILE="${REPO_ROOT}/deploy/docker/lidb-runtime/Dockerfile"
LICONTAINER_DIR="${REPO_ROOT}/licontainer"

echo "==> Build lidb-runtime Docker image (source for OCI export)"
docker build -t librebase/lidb-runtime:export -f "$DOCKERFILE" "$REPO_ROOT"

echo "==> Export to OCI tarball"
OCI_TAR="${REPO_ROOT}/dist/lidb-runtime-oci.tar"
mkdir -p "${REPO_ROOT}/dist"
docker save librebase/lidb-runtime:export -o "$OCI_TAR"

echo "==> Import into licontainer store via liimg"
cd "$LICONTAINER_DIR"
cargo build --release
export LI_CONTAINER_STORE="${LI_CONTAINER_STORE:-/var/lib/licontainer}"
export LI_CONTAINER_SKIP_ENTITLEMENT=1

# Tag for liimg pull (uses local store layout)
./target/release/lictl pull "$IMAGE_NAME" --squashfs 2>/dev/null || \
  ./target/release/lictl pull "$IMAGE_NAME"

echo "==> Done"
echo "Image reference: $IMAGE_NAME"
echo "Set LIBREBASE_K8S_IMAGE=$IMAGE_NAME for Kubernetes manifests"
echo "Default documented in data-studio-ui/lib/k8s-manifests.ts (DEFAULT_OCI_SQUASHFS_IMAGE)"
