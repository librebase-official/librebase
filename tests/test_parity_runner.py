"""Parity runner skip path (no Li required)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "scripts" / "parity_runner.py"


class TestParityRunnerSkip(unittest.TestCase):
    def test_skips_without_lidb(self) -> None:
        env = {k: v for k, v in os.environ.items() if k not in ("LIDB_ROOT", "LIS_ROOT", "PARITY_FORCE")}
        result = subprocess.run(
            [sys.executable, str(RUNNER)],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "skipped")
        self.assertEqual(payload["reason"], "no_lidb")
        report = ROOT / "tests" / "parity" / "last-report.json"
        self.assertTrue(report.is_file(), "expected default last-report.json")
        on_disk = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(on_disk["status"], "skipped")


if __name__ == "__main__":
    unittest.main()
