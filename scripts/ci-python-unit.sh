#!/usr/bin/env bash
# Top-level Python unit tests. Pentest, tests/e2e, and staging live in other jobs.
set -euo pipefail
cd "$(dirname "$0")/.."
files=()
for f in tests/test_*.py; do
  case "$f" in
    tests/test_security_pentest.py|tests/test_pentest_full.py) continue ;;
  esac
  files+=("$f")
done
echo "Python unit files: ${files[*]}"
python3 -m unittest "${files[@]}"
