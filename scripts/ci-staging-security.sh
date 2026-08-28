#!/usr/bin/env bash
# Defensive staging security: TLS hostname, public JSON leaks, auth walls, headers.
# No exploits, payloads, fuzzers, or attack procedures.
set -euo pipefail
cd "$(dirname "$0")/.."
export LIBREBASE_STAGING_CHECKS=1
python3 -m unittest discover -s tests/staging -p "test_staging_security.py"
