#!/usr/bin/env bash
# Local e2e: tests/e2e Python suite (in-process / mocked cloud).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m unittest discover -s tests/e2e -p "test_*.py"
