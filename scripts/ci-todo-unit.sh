#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../apps/todo-app"
npm install
node test/unit.mjs
