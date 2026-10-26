"""Studio compose LIBREBASE_VERSION must track repo VERSION."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
COMPOSE_ENV = ROOT / "data-studio-ui" / "compose.env"
STUDIO_COMPOSE = ROOT / "data-studio-ui" / "docker-compose.yml"


class TestComposeVersion(unittest.TestCase):
    def test_compose_env_matches_version_file(self) -> None:
        text = COMPOSE_ENV.read_text(encoding="utf-8")
        m = re.search(r"^LIBREBASE_VERSION=(\S+)", text, re.M)
        self.assertIsNotNone(m, "compose.env missing LIBREBASE_VERSION")
        self.assertEqual(m.group(1), VERSION)

    def test_studio_compose_default_matches_version(self) -> None:
        text = STUDIO_COMPOSE.read_text(encoding="utf-8")
        m = re.search(
            r"LIBREBASE_VERSION:\s*\$\{LIBREBASE_VERSION:-(\d+\.\d+\.\d+)\}",
            text,
        )
        self.assertIsNotNone(
            m,
            "docker-compose.yml must default LIBREBASE_VERSION from VERSION via ${LIBREBASE_VERSION:-X.Y.Z}",
        )
        self.assertEqual(m.group(1), VERSION)

    def test_li_ci_pins_are_40_char_hex(self) -> None:
        import subprocess

        for dep in ("lidb", "lis"):
            sha = subprocess.check_output(
                ["python3", "scripts/resolve-li-ci-pin.py", dep],
                cwd=ROOT,
                text=True,
            ).strip()
            self.assertEqual(len(sha), 40)
            self.assertRegex(sha, r"^[0-9a-f]{40}$")


if __name__ == "__main__":
    unittest.main()
