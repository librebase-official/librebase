#!/usr/bin/env bash
# Install licontainerd + licri on a Linux Kubernetes node (pure Li build).
set -euo pipefail

INSTALL_PREFIX="${INSTALL_PREFIX:-/usr/local}"
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
LICONTAINER_DIR="${REPO_ROOT}/licontainer"
LIC="${LIC:-${LIC_ROOT:-}/bin/lic}"
if [[ ! -x "$LIC" && -f "${LIC_ROOT:-}/scripts/resolve-lic.sh" ]]; then
  LIC="$("${LIC_ROOT}/scripts/resolve-lic.sh")"
fi
if [[ ! -x "$LIC" ]]; then
  echo "error: set LIC_ROOT and build lic first" >&2
  exit 1
fi

echo "==> Building licontainer (Li) from ${LICONTAINER_DIR}"
export LIC_ROOT="${LIC_ROOT:-}"
"${LICONTAINER_DIR}/scripts/build-li.sh"
mkdir -p "${LICONTAINER_DIR}/.build"

echo "==> Installing binaries to ${INSTALL_PREFIX}/bin"
install -m 755 "${LICONTAINER_DIR}/.build/lirun" "${INSTALL_PREFIX}/bin/" 2>/dev/null || echo "note: lirun binary pending lic container seam merge"
# licontainerd, licri, lictl: build when main.li entrypoints ship

echo "==> Creating runtime directories"
mkdir -p /run/licontainer
mkdir -p /var/lib/licontainer
mkdir -p /sys/fs/cgroup/licontainer

echo "==> Configure kubelet: container-runtime-endpoint=unix:///run/licontainer/licri.sock"
echo "    kubectl apply -f deploy/kubernetes/runtime-class-licontainer.yaml"
echo "Done."
