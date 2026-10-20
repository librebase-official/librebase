#!/usr/bin/env python3
"""Runner for the LibreBase weekly trend scan."""
import sys, os, json

librebase_dir = os.path.expanduser("~/Documents/coding-projects/librebase")
sys.path.insert(0, os.path.join(librebase_dir, "data", "marketing"))

from weekly_trend_scan import run

result = run()
print()
print("=== FINAL RESULT ===")
print(json.dumps(result, indent=2))
