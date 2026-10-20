#!/usr/bin/env python3
import sys, os, json

librebase_dir = os.path.expanduser("~/Documents/coding-projects/librebase")
sys.path.insert(0, os.path.join(librebase_dir, "data", "marketing"))
os.environ["LIBREBASE_COMPETITIVE_DB"] = os.path.join(
    librebase_dir, "librebase_competitive.db"
)

# ── Probe Hermes tools availability ──────────────────────────────────────────
try:
    from hermes_tools import web_search, web_extract
    print(f"[probe] hermes_tools available: web_search={bool(web_search)}, web_extract={bool(web_extract)}")
    print(f"[probe] web_search type: {type(web_search)}")
except ImportError as e:
    print(f"[probe] hermes_tools IMPORT FAILED: {e}")
    print("[probe] Trying alternative import paths...")

# Try to find Hermes installation
import subprocess
try:
    result = subprocess.run(["which", "hermes"], capture_output=True, text=True)
    print(f"[probe] which hermes: {result.stdout.strip() or 'NOT FOUND'}")
except Exception as e:
    print(f"[probe] which hermes failed: {e}")

# Check common locations
for p in [
    os.path.expanduser("~/.hermes"),
    "/usr/local/lib/node_modules/hermes-agent",
    "/opt/hermes-agent",
]:
    print(f"[probe] {p}: {'EXISTS' if os.path.exists(p) else 'missing'}")
    if os.path.exists(p):
        print(f"  contents: {os.listdir(p)[:10]}")

print("\n===== Python version =====")
import sys
print(f"Python {sys.version}")
