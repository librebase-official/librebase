#!/usr/bin/env bash
# HTTP e2e against https://stage.librebase.xyz with verified TLS (no curl -k).
set -euo pipefail
cd "$(dirname "$0")/.."
export LIBREBASE_STAGING_CHECKS=1
python3 -m unittest discover -s tests/staging -p "test_staging_e2e.py"
