"""Admin API Docker image must include every local module the entrypoint imports."""
from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT / "admin-api" / "Dockerfile"
ENTRYPOINT = ROOT / "admin-api" / "scripts" / "admin_server.py"
SCRIPTS_DIR = ROOT / "admin-api" / "scripts"


def _local_script_imports() -> set[str]:
    tree = ast.parse(ENTRYPOINT.read_text())
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module.split(".")[0])
    # stdlib / third-party only in admin_server top-level imports besides scripts/
    script_modules = {p.stem for p in SCRIPTS_DIR.glob("*.py")}
    return names & script_modules


def _paths_copied_by_dockerfile() -> set[Path]:
    text = DOCKERFILE.read_text()
    copied: set[Path] = set()
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("COPY "):
            continue
        # COPY src dest
        m = re.match(r"COPY\s+(\S+)\s+(\S+)", line)
        if not m:
            continue
        src, dest = m.group(1), m.group(2).rstrip("/")
        src_path = ROOT / src
        if src_path.is_dir():
            if dest.endswith("scripts") or dest == "./scripts/":
                for py in src_path.glob("*.py"):
                    copied.add(Path("scripts") / py.name)
            else:
                for py in src_path.rglob("*.py"):
                    rel = py.relative_to(src_path)
                    copied.add(Path(dest.replace("./", "")) / rel)
        elif src_path.is_file():
            copied.add(Path(dest.replace("./", "")) / src_path.name)
    return copied


class TestAdminDockerfile(unittest.TestCase):
    def test_dockerfile_copies_all_entrypoint_script_modules(self) -> None:
        required = _local_script_imports()
        self.assertIn("mail_api", required)
        self.assertIn("mail_pack", required)
        copied = _paths_copied_by_dockerfile()
        missing = sorted(
            mod
            for mod in required
            if Path("scripts") / f"{mod}.py" not in copied
        )
        self.assertEqual(
            missing,
            [],
            f"admin-api/Dockerfile missing COPY for: {', '.join(missing)}",
        )

    def test_dockerfile_declares_bind_all_interfaces(self) -> None:
        text = DOCKERFILE.read_text()
        self.assertIn("LIBREBASE_ADMIN_BIND=0.0.0.0", text)


if __name__ == "__main__":
    unittest.main()
