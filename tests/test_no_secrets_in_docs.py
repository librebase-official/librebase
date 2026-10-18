"""Fail if git-tracked docs embed live-looking Librebase MCP keys or Stripe secrets."""
from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MCP_LIVE = re.compile(r"lb_mcp_[A-Za-z0-9_-]{20,}")
STRIPE_LIVE = re.compile(r"sk_(live|test)_[A-Za-z0-9]{16,}")
WHSEC = re.compile(r"whsec_[A-Za-z0-9]{16,}")

DOC_SUFFIXES = {".md", ".mdc", ".txt", ".toml", ".yml", ".yaml", ".example"}


def _tracked_doc_files() -> list[Path]:
    out = subprocess.check_output(
        ["git", "-C", str(ROOT), "ls-files"],
        text=True,
    )
    paths: list[Path] = []
    for line in out.splitlines():
        p = ROOT / line
        if p.suffix.lower() in DOC_SUFFIXES or p.name in {"AGENTS.md", "HANDOFF.md", "README.md"}:
            paths.append(p)
    return paths


class NoSecretsInDocs(unittest.TestCase):
    def test_no_live_mcp_or_stripe_secrets(self) -> None:
        offenders: list[str] = []
        for path in _tracked_doc_files():
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for rx, label in (
                (MCP_LIVE, "mcp"),
                (STRIPE_LIVE, "stripe"),
                (WHSEC, "whsec"),
            ):
                for m in rx.finditer(text):
                    token = m.group(0)
                    if "..." in token or "xxx" in token.lower():
                        continue
                    rel = path.relative_to(ROOT).as_posix()
                    offenders.append(f"{rel}: {label} {token[:24]}…")
        self.assertEqual(
            offenders,
            [],
            "live-looking secrets in tracked docs:\n" + "\n".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
