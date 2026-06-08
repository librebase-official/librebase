#!/usr/bin/env bash
# Install licontainerd + licri on a Linux Kubernetes node.
# Run as root on each node that should use the licontainer RuntimeClass.
set -euo pipefail

INSTALL_PREFIX="${INSTALL_PREFIX:-/usr/local}"
REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
LICONTAINER_DIR="${REPO_ROOT}/licontainer"

echo "==> Building licontainer from ${LICONTAINER_DIR}"
cd "${LICONTAINER_DIR}"
cargo build --release

echo "==> Installing binaries to ${INSTALL_PREFIX}/bin"
install -m 755 target/release/lirun "${INSTALL_PREFIX}/bin/"
install -m 755 target/release/licontainerd "${INSTALL_PREFIX}/bin/"
install -m 755 target/release/licri "${INSTALL_PREFIX}/bin/"
install -m 755 target/release/lictl "${INSTALL_PREFIX}/bin/"

echo "==> Creating runtime directories"
mkdir -p /run/licontainer
mkdir -p /var/lib/licontainer
mkdir -p /sys/fs/cgroup/licontainer

echo "==> Installing systemd units"
cat > /etc/systemd/system/licontainerd.service <<'EOF'
[Unit]
Description=licontainer daemon
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/licontainerd --socket /run/licontainer/licontainerd.sock
Restart=on-failure
RuntimeDirectory=licontainer

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/licri.service <<'EOF'
[Unit]
Description=licontainer CRI shim
After=licontainerd.service
Requires=licontainerd.service

[Service]
Type=simple
ExecStart=/usr/local/bin/licri --socket /run/licontainer/licri.sock
Restart=on-failure
RuntimeDirectory=licontainer

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable licontainerd licri
systemctl start licontainerd licri

echo "==> Configure kubelet (manual step):"
echo "    container-runtime-endpoint=unix:///run/licontainer/licri.sock"
echo "    Apply RuntimeClass: kubectl apply -f deploy/kubernetes/runtime-class-licontainer.yaml"
echo "Done."
