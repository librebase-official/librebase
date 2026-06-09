#!/usr/bin/env bash
# Busybox OCI bundle integration test for Li lirun (Linux + LI_CONTAINER_INTEGRATION=1).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WS="$ROOT/packages/li.toml"
LIC="${LIC:-${LIC_ROOT:-}/bin/lic}"

if [[ "${LI_CONTAINER_INTEGRATION:-}" != "1" ]]; then
  echo "skip: set LI_CONTAINER_INTEGRATION=1 to run"
  exit 0
fi

if [[ "$(uname -s)" != "Linux" ]]; then
  echo "skip: Linux required"
  exit 0
fi

if [[ ! -x "$LIC" ]]; then
  if command -v lic >/dev/null 2>&1; then
    LIC="$(command -v lic)"
  else
    echo "error: set LIC_ROOT or put lic on PATH" >&2
    exit 1
  fi
fi

LIRUN="${LIRUN:-$ROOT/.build/lirun}"
mkdir -p "$(dirname "$LIRUN")"
echo "build: lirun -> $LIRUN"
"$LIC" build --allow-open-vc --no-lean-verify "$ROOT/packages/li-container-run/src/main.li" -o "$LIRUN"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
STATE_DIR="$TMP/state"
CGROUP_ROOT="$TMP/cgroup"
BUNDLE="$TMP/bundle"
ROOTFS="$BUNDLE/rootfs"
mkdir -p "$STATE_DIR" "$CGROUP_ROOT" "$ROOTFS/bin"

BUSYBOX="$ROOTFS/bin/busybox"
if [[ ! -x "$BUSYBOX" ]]; then
  curl -fsSL "https://busybox.net/downloads/binaries/1.35.0-x86_64-linux-musl/busybox" -o "$BUSYBOX"
  chmod 755 "$BUSYBOX"
fi
ln -sf busybox "$ROOTFS/bin/sh"

cat >"$BUNDLE/config.json" <<'EOF'
{
  "ociVersion": "1.0.2",
  "process": {
    "terminal": false,
    "user": { "uid": 0, "gid": 0 },
    "args": ["/bin/sh", "-c", "echo hello-licontainer > /tmp/out; sleep 0.1"],
    "env": ["PATH=/bin:/usr/bin"],
    "cwd": "/"
  },
  "root": { "path": "rootfs", "readonly": false },
  "hostname": "lirun-test",
  "mounts": [
    { "destination": "/proc", "type": "proc", "source": "proc" },
    { "destination": "/dev", "type": "tmpfs", "source": "tmpfs", "options": ["mode=755"] }
  ],
  "linux": {
    "namespaces": [
      { "type": "pid" }, { "type": "net" }, { "type": "mnt" },
      { "type": "uts" }, { "type": "ipc" }
    ],
    "resources": { "pids": { "limit": 64 } }
  }
}
EOF

export LI_CONTAINER_STATE_DIR="$STATE_DIR"
export LI_CONTAINER_CGROUP_ROOT="$CGROUP_ROOT"
export LI_CONTAINER_SKIP_SECCOMP=1

ID="test-busybox"
"$LIRUN" create --bundle "$BUNDLE" --id "$ID"
"$LIRUN" start --id "$ID"
sleep 0.2
OUT="$("$LIRUN" state --id "$ID")"
echo "$OUT" | grep -E 'running|stopped'
"$LIRUN" delete --id "$ID" --force"
echo "lirun integration: ok"
