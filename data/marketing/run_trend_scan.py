#!/usr/bin/env python3
import sys, os, json

librebase_dir = os.path.expanduser("~/Documents/coding-projects/librebase")
sys.path.insert(0, os.path.join(librebase_dir, "data", "marketing"))
os.environ["LIBREBASE_COMPETITIVE_DB"] = os.path.join(
    librebase_dir, "librebase_competitive.db"
)

from daily_research import run_trend_only_scan

result = run_trend_only_scan()
print()
print("===== FINAL RESULT =====")
print(json.dumps(result, indent=2))
