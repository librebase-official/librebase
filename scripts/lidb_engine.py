#!/usr/bin/env python3
"""Minimal lidb embed lifecycle stub for Librebase Studio.

Honest degraded mode when LIDB_ROOT is missing or lis db start is unavailable.
Set LIDB_RUNTIME_MODE=dev to start the local dev stub when lidb is not installed.
Studio project-runtime invokes: status | ensure | migrate
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
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


def _dev_mode_enabled() -> bool:
    return os.environ.get("LIDB_RUNTIME_MODE", "").strip().lower() == "dev"


def _dev_stub_script() -> Path:
    return Path(__file__).resolve().parent / "dev_runtime_stub.py"


def _runtime_mode() -> str:
    if _lidb_root() is not None:
        return "production"
    if _dev_mode_enabled():
        return "dev"
    return "unavailable"


def _status_payload(
    data_dir: str,
    api_port: int,
    postgres_port: int,
) -> dict[str, Any]:
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    mode = _runtime_mode()
    api_up = _port_open("127.0.0.1", api_port)
    pg_up = _port_open("127.0.0.1", postgres_port)
    running = api_up and pg_up

    base: dict[str, Any] = {
        "data_dir": data_dir,
        "api_port": api_port,
        "postgres_port": postgres_port,
        "runtime_mode": mode,
        "running": running,
        "api_reachable": api_up,
        "postgres_reachable": pg_up,
    }

    if running:
        if mode == "dev":
            message = "Dev runtime — ports reachable (not production lidb)"
            degraded = True
        else:
            message = "API port reachable"
            degraded = False
        return {
            **base,
            "status": "running",
            "degraded": degraded,
            "message": message,
        }

    if mode == "unavailable":
        return {
            **base,
            "status": "stopped",
            "degraded": True,
            "message": "LIDB_ROOT not configured — runtime unavailable (set LIDB_RUNTIME_MODE=dev)",
        }

    if mode == "dev":
        return {
            **base,
            "status": "stopped",
            "degraded": True,
            "message": "Dev runtime not listening — launch or start container",
        }

    return {
        **base,
        "status": "stopped",
        "degraded": False,
        "message": "Database not running",
    }


def _start_dev_stub(data_dir: str, api_port: int, postgres_port: int) -> tuple[bool, str]:
    script = _dev_stub_script()
    if not script.is_file():
        return False, "dev_runtime_stub.py not found"

    if _port_open("127.0.0.1", api_port) and _port_open("127.0.0.1", postgres_port):
        return True, "Dev runtime already listening"

    env = os.environ.copy()
    env["LI_DATA_DIR"] = data_dir

    popen_kwargs: dict[str, Any] = {
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "env": env,
    }
    if sys.platform == "win32":
        popen_kwargs["creationflags"] = (
            subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        )
    else:
        popen_kwargs["start_new_session"] = True

    try:
        subprocess.Popen(
            [
                sys.executable,
                str(script),
                "--data-dir",
                data_dir,
                "--api-port",
                str(api_port),
                "--postgres-port",
                str(postgres_port),
            ],
            **popen_kwargs,
        )
    except OSError as exc:
        return False, f"Dev runtime start failed: {exc}"

    for _ in range(30):
        if _port_open("127.0.0.1", api_port) and _port_open("127.0.0.1", postgres_port):
            return True, "Dev runtime started"
        time.sleep(0.1)

    return False, "Dev runtime failed to bind ports"


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
    env["LI_API_PORT"] = str(api_port)
    env["LI_DB_PORT"] = str(postgres_port)
    # Prefer librebase profile when present; allow override via LI_PROFILE.
    env.setdefault("LI_PROFILE", "librebase")

    try:
        result = subprocess.run(
            ["lis", "db", "start", "--profile", env["LI_PROFILE"]],
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
        # Fallback if librebase profile missing on older lis
        if env["LI_PROFILE"] == "librebase" and "librebase" in err.lower():
            env["LI_PROFILE"] = "registry-min"
            try:
                result = subprocess.run(
                    ["lis", "db", "start", "--profile", "registry-min"],
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
            except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
                return False, str(exc)
            if result.returncode != 0:
                err = (result.stderr or result.stdout or "lis db start failed").strip()
                return False, err
            return True, "lis db start completed (profile=registry-min fallback)"
        return False, err

    return True, f"lis db start completed (profile={env['LI_PROFILE']})"


def cmd_status(data_dir: str, api_port: int, postgres_port: int) -> dict[str, Any]:
    return _status_payload(data_dir, api_port, postgres_port)


def cmd_ensure(data_dir: str, api_port: int, postgres_port: int) -> dict[str, Any]:
    current = cmd_status(data_dir, api_port, postgres_port)
    if current["status"] == "running":
        current["message"] = "Already running"
        return current

    if _lidb_root() is not None:
        ok, msg = _lis_db_start(data_dir, api_port, postgres_port)
    elif _dev_mode_enabled():
        ok, msg = _start_dev_stub(data_dir, api_port, postgres_port)
    else:
        ok, msg = False, "LIDB_ROOT not configured — set LIDB_RUNTIME_MODE=dev"

    after = cmd_status(data_dir, api_port, postgres_port)
    after["launch_ok"] = ok
    after["message"] = msg if not ok else after.get("message", msg)
    return after


def cmd_stop(data_dir: str, api_port: int, postgres_port: int) -> dict[str, Any]:
    """Best-effort stop of the local listener. Honest if we cannot kill it."""
    import signal

    killed: list[int] = []
    if sys.platform != "win32":
        try:
            listed = subprocess.run(
                ["lsof", "-ti", f"TCP:{api_port}", f"TCP:{postgres_port}", "-sTCP:LISTEN"],
                capture_output=True,
                text=True,
                check=False,
            )
            for raw in (listed.stdout or "").split():
                try:
                    pid = int(raw)
                except ValueError:
                    continue
                try:
                    os.kill(pid, signal.SIGTERM)
                    killed.append(pid)
                except OSError:
                    continue
        except FileNotFoundError:
            killed = []

    time.sleep(0.2)
    after = cmd_status(data_dir, api_port, postgres_port)
    after["stopped_pids"] = killed
    if after["status"] != "running":
        after["message"] = "Runtime stopped" if killed else "Runtime was not listening"
        after["status"] = "stopped"
        return after
    after["degraded"] = True
    after["message"] = "Asked the process to stop; ports are still open"
    return after


def cmd_migrate(data_dir: str, api_port: int, postgres_port: int) -> dict[str, Any]:
    status = cmd_status(data_dir, api_port, postgres_port)
    if status["status"] != "running":
        status["degraded"] = True
        status["message"] = "Cannot migrate — database not running"
        return status

    if status.get("runtime_mode") == "dev":
        status["message"] = "Dev runtime — migrate noop"
        status["migrated"] = True
        return status

    # Stub: real migrations wired when lidb embed ships in this repo.
    status["message"] = "Migrate stub — no pending migrations"
    status["migrated"] = True
    return status


def _exit_code(payload: dict[str, Any], command: str) -> int:
    if command == "status":
        return 0
    if payload.get("status") == "running":
        return 0
    return 0 if not payload.get("degraded") else 1


COMMANDS = {
    "status": cmd_status,
    "ensure": cmd_ensure,
    "stop": cmd_stop,
    "migrate": cmd_migrate,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Librebase lidb engine")
    parser.add_argument("command", choices=sorted(COMMANDS.keys()))
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--api-port", type=int, required=True)
    parser.add_argument("--postgres-port", type=int, required=True)
    args = parser.parse_args()

    handler = COMMANDS[args.command]
    payload = handler(args.data_dir, args.api_port, args.postgres_port)
    print(json.dumps(payload))
    return _exit_code(payload, args.command)


if __name__ == "__main__":
    sys.exit(main())
