#!/usr/bin/env python3
"""Run the LibreBase daily competitor scan."""
import sys, os
sys.path.insert(0, os.path.expanduser("~/Documents/coding-projects/librebase"))
from data.marketing.daily_research import run_daily_scan

result = run_daily_scan(scope="all")
print("\n=== SCAN RESULT ===")
print(f"Findings: {result.get('findings', 0)}")
print(f"Queries: {result.get('queries', 0)}")
print(f"Digest file: {result.get('digest_file', 'N/A')}")
