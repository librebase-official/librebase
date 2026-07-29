#!/usr/bin/env python3
"""Run Wave A parity contracts against a lis/lidb stack.

Exit codes:
  0 — all required contracts pass, OR skipped because Li is unavailable
  1 — one or more required contracts failed
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.parity.contracts import Result, run_all  # noqa: E402


def _lidb_available() -> bool:
    raw = os.environ.get("LIDB_ROOT", "").strip()
    if not raw:
        return False
    return Path(raw).is_dir()


def _lis_available() -> bool:
    if shutil.which("lis"):
        return True
    lis_root = os.environ.get("LIS_ROOT", "").strip()
    if lis_root and (Path(lis_root) / "bin" / "lis").exists():
        return True
    return False


def _write_report(payload: dict) -> None:
    out = Path(os.environ.get("PARITY_REPORT", ROOT / "tests" / "parity" / "last-report.json"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    force = os.environ.get("PARITY_FORCE", "").strip() == "1"
    if not force and (not _lidb_available() or not _lis_available()):
        payload = {
            "status": "skipped",
            "reason": "no_lidb" if not _lidb_available() else "no_lis",
            "message": "Set LIDB_ROOT and ensure lis on PATH (or LIS_ROOT) to run Wave A",
            "results": [],
        }
        _write_report(payload)
        print(json.dumps(payload, indent=2))
        return 0

    results: list[Result] = run_all()
    required_fail = [r for r in results if r.status == "fail" and r.id != "P-RT-01"]
    soft = [r for r in results if r.id == "P-RT-01"]
    payload = {
        "status": "failed" if required_fail else "passed",
        "passed": sum(1 for r in results if r.status == "pass"),
        "failed": sum(1 for r in results if r.status == "fail"),
        "skipped": sum(1 for r in results if r.status == "skip"),
        "results": [
            {"id": r.id, "status": r.status, "detail": r.detail, "evidence": r.evidence}
            for r in results
        ],
        "soft": [{"id": r.id, "status": r.status, "detail": r.detail} for r in soft],
    }
    _write_report(payload)
    print(json.dumps(payload, indent=2))
    return 1 if required_fail else 0


if __name__ == "__main__":
    sys.exit(main())
