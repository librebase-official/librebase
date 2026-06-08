#!/usr/bin/env python3
"""Minimal lidb embed lifecycle stub for Librebase Studio.

Honest degraded mode when LIDB_ROOT is missing or lis db start is unavailable.
Studio project-runtime invokes: status | ensure | migrate
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any


def _port_open(host: str, port: int, timeout: float = 0.4) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _lidb_root() -> Path | None:
    raw = os.environ.get("LIDB_ROOT")
    if not raw:
        return None
    path = Path(raw)
    return path if path.is_dir() else None


def _lis_db_start(data_dir: str, api_port: int, postgres_port: int) -> tuple[bool, str]:
    """Attempt `lis db start` when lis is on PATH and LIDB_ROOT is set."""
    root = _lidb_root()
    if root is None:
        return False, "LIDB_ROOT not set or missing — degraded mode"

    env = os.environ.copy()
    env["LI_DATA_DIR"] = data_dir
    env["LIDB_ROOT"] = str(root)
    env["LIBREBASE_API_PORT"] = str(api_port)
    env["LIBREBASE_PG_PORT"] = str(postgres_port)

    try:
        result = subprocess.run(
            ["lis", "db", "start"],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except FileNotFoundError:
        return False, "lis CLI not found on PATH — degraded mode"
    except subprocess.TimeoutExpired:
        return False, "lis db start timed out"

    if result.returncode != 0:
        err = (result.stderr or result.stdout or "lis db start failed").strip()
        return False, err

    return True, "lis db start completed"


def cmd_status(data_dir: str, api_port: int, postgres_port: int) -> dict[str, Any]:
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    degraded = _lidb_root() is None
    port_up = _port_open("127.0.0.1", api_port)

    if port_up:
        return {
            "status": "running",
            "degraded": degraded,
            "message": "API port reachable",
            "data_dir": data_dir,
            "api_port": api_port,
            "postgres_port": postgres_port,
        }

    if degraded:
        return {
            "status": "stopped",
            "degraded": True,
            "message": "LIDB_ROOT not configured — runtime unavailable",
            "data_dir": data_dir,
            "api_port": api_port,
            "postgres_port": postgres_port,
        }

    return {
        "status": "stopped",
        "degraded": False,
        "message": "Database not running",
        "data_dir": data_dir,
        "api_port": api_port,
        "postgres_port": postgres_port,
    }


def cmd_ensure(data_dir: str, api_port: int, postgres_port: int) -> dict[str, Any]:
    current = cmd_status(data_dir, api_port, postgres_port)
    if current["status"] == "running":
        current["message"] = "Already running"
        return current

    ok, msg = _lis_db_start(data_dir, api_port, postgres_port)
    after = cmd_status(data_dir, api_port, postgres_port)
    after["launch_ok"] = ok
    after["message"] = msg if not ok else after.get("message", msg)
    return after


def cmd_migrate(data_dir: str, api_port: int, postgres_port: int) -> dict[str, Any]:
    status = cmd_status(data_dir, api_port, postgres_port)
    if status["status"] != "running":
        status["degraded"] = True
        status["message"] = "Cannot migrate — database not running"
        return status

    # Stub: real migrations wired when lidb embed ships in this repo.
    status["message"] = "Migrate stub — no pending migrations"
    status["migrated"] = True
    return status


COMMANDS = {
    "status": cmd_status,
    "ensure": cmd_ensure,
    "migrate": cmd_migrate,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Librebase lidb engine stub")
    parser.add_argument("command", choices=sorted(COMMANDS.keys()))
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--api-port", type=int, required=True)
    parser.add_argument("--postgres-port", type=int, required=True)
    args = parser.parse_args()

    handler = COMMANDS[args.command]
    payload = handler(args.data_dir, args.api_port, args.postgres_port)
    print(json.dumps(payload))
    return 0 if not payload.get("degraded") or args.command == "status" else 1


if __name__ == "__main__":
    sys.exit(main())
