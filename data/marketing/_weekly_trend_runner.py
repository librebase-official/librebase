#!/usr/bin/env python3
"""Run the LibreBase weekly trend deep-dive scan."""
import sys, os, json

librebase_dir = os.path.expanduser("~/Documents/coding-projects/librebase")
sys.path.insert(0, os.path.join(librebase_dir, "data", "marketing"))
os.environ["LIBREBASE_COMPETITIVE_DB"] = os.path.join(
    librebase_dir, "librebase_competitive.db"
)

# Verify DB exists
db_path = os.environ["LIBREBASE_COMPETITIVE_DB"]
print(f"DB: {db_path} ({os.path.getsize(db_path):,} bytes)")
print()

from daily_research import run_trend_only_scan

print("=" * 70)
print("LIBREBASE WEEKLY TREND DEEP-DIVE")
print("=" * 70)
print()

result = run_trend_only_scan()

print()
print("=" * 70)
print("SCAN RESULT SUMMARY")
print("=" * 70)
print(f"  Trend findings discovered: {result.get('findings', 'N/A')}")
print(f"  Queries fired: {result.get('queries', 'N/A')}")
print(f"  Digest file: {result.get('digest_file', 'N/A')}")
print()
print("===== FINAL RESULT JSON =====")
print(json.dumps(result, indent=2))
