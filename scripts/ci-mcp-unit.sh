#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../packages/mcp"
npm install
node test/session.unit.mjs
node test/smoke.mjs
