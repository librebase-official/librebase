#!/usr/bin/env python3
"""Sync the VERSION file to all package.json, li.toml, Chart.yaml, and MCP server files.

Usage:
    python3 scripts/sync-version.py          # sync VERSION → all packages
    python3 scripts/sync-version.py --bump patch  # bump VERSION then sync
    python3 scripts/sync-version.py --bump minor
    python3 scripts/sync-version.py --bump major
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
VERSION_FILE = REPO / "VERSION"

# Files to patch (relative to REPO)
PACKAGE_JSONS = [
    "data-studio-ui/package.json",
    "data-saas-admin/package.json",
    "packages/mcp/package.json",
    "packages/sdk/package.json",
    "apps/todo-app/package.json",
    "apps/todo-app-supabase/package.json",
]

LI_TOMLS = [
    "li.toml",
    "licontainer/packages/li-containerd/li.toml",
    "licontainer/packages/li-container-cri/li.toml",
    "licontainer/packages/li-container-run/li.toml",
    "licontainer/packages/li-container-cli/li.toml",
    "licontainer/packages/li-container-img/li.toml",
    "licontainer/packages/li-container/li.toml",
]

HELM_CHART = "deploy/helm/librebase-instance/Chart.yaml"

# Dockerfiles with LIBREBASE_VERSION build arg
DOCKERFILES = [
    "data-studio-ui/Dockerfile",
    "saas-admin-api/Dockerfile",
]

# Python MCP serverInfo version
MCP_PY = "mcp/librebase_mcp/__main__.py"
# JS MCP server version
MCP_JS = "packages/mcp/src/server.js"


def read_version() -> str:
    return VERSION_FILE.read_text().strip()


def bump_version(version: str, kind: str) -> str:
    parts = version.split(".")
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {version}")
    major, minor, patch = int(parts[0]), int(parts[1]), int(parts[2])
    if kind == "major":
        return f"{major + 1}.0.0"
    elif kind == "minor":
        return f"{major}.{minor + 1}.0"
    elif kind == "patch":
        return f"{major}.{minor}.{patch + 1}"
    raise ValueError(f"Unknown bump kind: {kind}")


def patch_package_json(path: Path, version: str) -> bool:
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError):
        return False
    if data.get("version") == version:
        return False
    data["version"] = version
    path.write_text(json.dumps(data, indent=2) + "\n")
    return True


def patch_li_toml(path: Path, version: str) -> bool:
    if not path.exists():
        return False
    content = path.read_text()
    new_content = re.sub(
        r'^(version\s*=\s*)"[^"]*"',
        f'\\1"{version}"',
        content,
        flags=re.MULTILINE,
    )
    if new_content == content:
        return False
    path.write_text(new_content)
    return True


def patch_helm_chart(path: Path, version: str) -> bool:
    if not path.exists():
        return False
    content = path.read_text()
    new_content = content
    new_content = re.sub(
        r'^(version:\s*)"[^"]*"',
        f'\\1"{version}"',
        new_content,
        count=1,
        flags=re.MULTILINE,
    )
    new_content = re.sub(
        r'^(appVersion:\s*)"[^"]*"',
        f'\\1"{version}"',
        new_content,
        count=1,
        flags=re.MULTILINE,
    )
    new_content = re.sub(
        r'^(version:\s+)\S+',
        f'\\g<1>{version}',
        new_content,
        count=1,
        flags=re.MULTILINE,
    )
    if new_content == content:
        return False
    path.write_text(new_content)
    return True


def patch_mcp_python(path: Path, version: str) -> bool:
    if not path.exists():
        return False
    content = path.read_text()
    new_content = re.sub(
        r'("version":\s*")\d+\.\d+\.\d+(")',
        f'\\g<1>{version}\\g<2>',
        content,
        count=1,
    )
    if new_content == content:
        return False
    path.write_text(new_content)
    return True


def patch_mcp_js(path: Path, version: str) -> bool:
    if not path.exists():
        return False
    content = path.read_text()
    new_content = re.sub(
        r'(version:\s*")\d+\.\d+\.\d+(")',
        f'\\g<1>{version}\\g<2>',
        content,
        count=1,
    )
    if new_content == content:
        return False
    path.write_text(new_content)
    return True


def patch_dockerfile(path: Path, version: str) -> bool:
    """Update the LIBREBASE_VERSION default in Dockerfile ARG/ENV lines."""
    if not path.exists():
        return False
    content = path.read_text()
    # Match: ARG LIBREBASE_VERSION=X.Y.Z or ENV LIBREBASE_VERSION=$LIBREBASE_VERSION
    # We only patch the ARG default value
    new_content = re.sub(
        r'(ARG LIBREBASE_VERSION=)\S+',
        f'\\g<1>{version}',
        content,
    )
    if new_content == content:
        return False
    path.write_text(new_content)
    return True


def patch_layout_version(path: Path, version: str) -> bool:
    """Update the hardcoded LIBREBASE_VERSION const in layout.tsx."""
    if not path.exists():
        return False
    content = path.read_text()
    new_content = re.sub(
        r'(const LIBREBASE_VERSION = ")\d+\.\d+\.\d+(")',
        f'\\g<1>{version}\\g<2>',
        content,
    )
    if new_content == content:
        return False
    path.write_text(new_content)
    return True


def main() -> int:
    bump = None
    if "--bump" in sys.argv:
        idx = sys.argv.index("--bump")
        if idx + 1 < len(sys.argv):
            bump = sys.argv[idx + 1]
        else:
            print("Error: --bump requires patch|minor|major", file=sys.stderr)
            return 1

    version = read_version()
    if bump:
        version = bump_version(version, bump)
        VERSION_FILE.write_text(version + "\n")
        print(f"Bumped VERSION → {version}")

    patched = 0
    repo = REPO

    for rel in PACKAGE_JSONS:
        if patch_package_json(repo / rel, version):
            print(f"  patched {rel}")
            patched += 1

    for rel in LI_TOMLS:
        if patch_li_toml(repo / rel, version):
            print(f"  patched {rel}")
            patched += 1

    if patch_helm_chart(repo / HELM_CHART, version):
        print(f"  patched {HELM_CHART}")
        patched += 1

    if patch_mcp_python(repo / MCP_PY, version):
        print(f"  patched {MCP_PY}")
        patched += 1

    if patch_mcp_js(repo / MCP_JS, version):
        print(f"  patched {MCP_JS}")
        patched += 1

    for rel in DOCKERFILES:
        if patch_dockerfile(repo / rel, version):
            print(f"  patched {rel}")
            patched += 1

    layout_tsx = repo / "data-studio-ui/app/layout.tsx"
    if patch_layout_version(layout_tsx, version):
        print(f"  patched data-studio-ui/app/layout.tsx")
        patched += 1

    print(f"Version synced to {patched} files: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
