#!/usr/bin/env python3
"""Resolve lidb/lis CI pins from docs/li-dependency-pins.md (40-char SHAs only)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

PINS_DOC = Path(__file__).resolve().parents[1] / "docs" / "li-dependency-pins.md"
CI_ROW = re.compile(
    r"^\|\s*\*\*(?P<dep>lidb|lis)\*\*\s*\|[^|]*\|\s*`(?P<sha>[0-9a-f]{40})`\s*\|",
    re.I | re.M,
)


def resolve(dep: str) -> str:
    text = PINS_DOC.read_text(encoding="utf-8")
    for m in CI_ROW.finditer(text):
        if m.group("dep").lower() == dep.lower():
            return m.group("sha").lower()
    raise SystemExit(f"could not parse {dep} 40-char pin from CI pins table in {PINS_DOC}")


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in ("lidb", "lis"):
        raise SystemExit("usage: resolve-li-ci-pin.py <lidb|lis>")
    print(resolve(sys.argv[1]))


if __name__ == "__main__":
    main()
