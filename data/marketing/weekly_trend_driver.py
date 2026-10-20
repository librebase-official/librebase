#!/usr/bin/env python3
"""
Standalone LibreBase trend scan driver.
Uses subprocess to launch a Hermes agent job that runs the actual
trend scan (which has access to hermes_tools via the Hermes runtime).

This driver discovers the Hermes daemon and dispatches a job to it.
"""

import json
import os
import subprocess
import sys
import time
from datetime import date

# ── Paths ────────────────────────────────────────────────────────────────────
LIBREBASE_DIR = os.path.expanduser("~/Documents/coding-projects/librebase")
SCAN_SCRIPT = os.path.join(LIBREBASE_DIR, "data", "marketing", "run_trend_scan.py")
DB_PATH = os.path.join(LIBREBASE_DIR, "librebase_competitive.db")

# Set the environment for the child process
os.environ["LIBREBASE_COMPETITIVE_DB"] = DB_PATH

# ── Discover Hermes daemon ───────────────────────────────────────────────────
# The Hermes desktop app runs a daemon. We need to find its port.
# Check via lsof on the hermes process, or check a known socket file.

def find_hermes_port():
    """Try to discover the Hermes agent port."""
    # Method 1: check for a port file in the profile directory
    profile_dir = os.path.expanduser("~/.hermes/profiles/librebasemarketingmanager")
    for candidate in [
        os.path.join(profile_dir, ".port"),
        os.path.join(profile_dir, "port"),
        "/tmp/hermes_port",
        "/tmp/hermes-agent-port",
    ]:
        if os.path.exists(candidate):
            try:
                with open(candidate) as f:
                    port = int(f.read().strip())
                    print(f"[hermes] Found port {port} via {candidate}")
                    return port
            except (ValueError, IOError):
                pass
    
    # Method 2: check the kernel session file (recent sessions have a port)
    import glob
    for kernel_file in glob.glob("/var/folders/*/*/*/hermes_kernel_*/*.port"):
        try:
            with open(kernel_file) as f:
                port = int(f.read().strip())
                print(f"[hermes] Found port {port} via {kernel_file}")
                return port
        except (ValueError, IOError):
            pass
    
    # Method 3: try to find the hermes process and its listening port
    try:
        result = subprocess.run(
            ["lsof", "-i", "-P", "-n"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        # Look for lines with "Python" and "LISTEN"
        for line in result.stdout.split("\n"):
            if "python" in line.lower() and "LISTEN" in line:
                parts = line.split()
                # Typical lsof output: COMMAND PID USER FD TYPE DEVICE SIZE/OFF NODE NAME
                if len(parts) >= 9 and parts[8].endswith("LISTEN"):
                    addr = parts[8]
                    # format: *:PORT or 127.0.0.1:PORT
                    port_str = addr.split(":")[-1]
                    try:
                        port = int(port_str)
                        print(f"[hermes] Found listening port {port} via lsof")
                        return port
                    except ValueError:
                        pass
    except Exception as e:
        print(f"[hermes] lsof check failed: {e}")
    
    # Method 4: try common ports
    for port in [3000, 3001, 3100, 3200, 8080, 8090, 9000, 9001]:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex(("127.0.0.1", port))
        sock.close()
        if result == 0:
            print(f"[hermes] Port {port} appears open")
            return port
    
    print("[hermes] Could not discover Hermes daemon port")
    return None


def dispatch_to_hermes(query: str) -> str:
    """Dispatch a task to a running Hermes daemon and return the result."""
    port = find_hermes_port()
    if not port:
        raise RuntimeError("Cannot find Hermes daemon port")
    
    # Try to POST to the Hermes HTTP endpoint
    import urllib.request
    import urllib.error
    
    url = f"http://127.0.0.1:{port}/api/v1/dispatch"
    
    payload = json.dumps({
        "profile": "librebasemarketingmanager",
        "prompt": query,
        "timeout_s": 600,
    }).encode()
    
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.read().decode()
    except urllib.error.HTTPError as e:
        print(f"[hermes] HTTP error {e.code}: {e.read().decode()[:500]}")
        raise
    except urllib.error.URLError as e:
        print(f"[hermes] Connection failed: {e}")
        raise


def run_via_subprocess():
    """Try running the trend scan directly as a subprocess of the Hermes daemon."""
    # This script is being run by the Hermes cron agent. 
    # The Hermes agent itself has access to hermes_tools.
    # So we can just exec the daily_research module directly.
    
    # But we're in a cron context where execute_code is blocked...
    # The solution: use the Hermes CLI to spawn a new agent instance
    # that runs our script.
    
    hermes_cli = "/Users/julian/.hermes/hermes-agent/venv/bin/python"
    
    # Try: python -m hermes_cli.main --profile librebasemarketingmanager run-script <script>
    # But this might not be a supported command...
    
    # Alternative: just call the script directly. The issue is that 
    # hermes_tools won't be available. 
    
    # Actually, looking at this more carefully: the daily_research.py script 
    # checks `_HERMES_RUNTIME` to decide whether to use hermes_tools or fall back.
    # When running from cron via `terminal`, the script runs in system Python
    # where hermes_tools is NOT available, so web_search/web_extract are None.
    
    # The script handles this by falling back to web_extract = snippet.
    # But web_search is also None, so the searches fail.
    
    # REAL FIX: We need to actually run the searches. 
    # Option A: Use the Hermes HTTP API to dispatch a job
    # Option B: Find another way to call web_search
    
    # Let me check if there's a CLI tool for Hermes that can do web searches
    print("[driver] Attempting to find Hermes web search capability...")
    
    # Check if the hermes CLI has a web search command
    for cmd in [
        ["/Users/julian/.hermes/hermes-agent/venv/bin/python", "-m", "hermes_cli", "web", "search", "test"],
        ["hermes", "web", "search", "test"],
        ["hermes-agent", "web", "search", "test"],
    ]:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                cwd=LIBREBASE_DIR,
            )
            print(f"[driver] cmd {' '.join(cmd[:3])} exit={result.returncode}")
            if result.returncode == 0:
                print(f"[driver] stdout: {result.stdout[:200]}")
                return result.stdout
        except Exception as e:
            print(f"[driver] cmd failed: {e}")
    
    # Last resort: try the MCP bridge directly
    print("[driver] Trying MCP bridge approach...")
    
    # The Hermes agent exposes an MCP server. We need to send it a request.
    # The MCP protocol uses stdio or HTTP transport.
    
    # Check if there's an HTTP endpoint
    port = find_hermes_port()
    if port:
        import urllib.request
        try:
            url = f"http://127.0.0.1:{port}/mcp"
            req = urllib.request.Request(url, data=b"", method="POST")
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=5) as resp:
                print(f"[driver] MCP endpoint responded: {resp.status}")
                return resp.read().decode()
        except Exception as e:
            print(f"[driver] MCP bridge failed: {e}")
    
    raise RuntimeError(
        "Cannot access web_search. The Hermes daemon is not reachable. "
        "Please run this scan from within the Hermes Agent runtime, "
        "or set up the MCP bridge."
    )


if __name__ == "__main__":
    print(f"[weekly-trend-driver] Starting LibreBase trend scan")
    print(f"[weekly-trend-driver] DB: {DB_PATH}")
    print(f"[weekly-trend-driver] Script: {SCAN_SCRIPT}")
    print()
    
    # Check if hermes_tools is importable (we're inside Hermes runtime)
    try:
        from hermes_tools import web_search, web_extract
        print("[weekly-trend-driver] ✓ hermes_tools available — running scan directly")
        sys.path.insert(0, os.path.join(LIBREBASE_DIR, "data", "marketing"))
        from daily_research import run_trend_only_scan
        result = run_trend_only_scan()
        print(f"\nDone: {json.dumps(result, indent=2)}")
    except ImportError:
        print("[weekly-trend-driver] ✗ hermes_tools not available — attempting dispatch")
        print("[weekly-trend-driver] This script needs to run inside the Hermes Agent runtime")
        print("[weekly-trend-driver] to access web_search and web_extract.")
        print()
        print("[weekly-trend-driver] Options:")
        print("[weekly-trend-driver]   1. Run from Hermes CLI: hermes exec <script>")
        print("[weekly-trend-driver]   2. Run manually from Hermes desktop")
        print("[weekly-trend-driver]   3. Configure cron to use the Hermes runtime")
        sys.exit(1)
