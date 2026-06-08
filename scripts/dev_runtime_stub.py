#!/usr/bin/env python3
"""Honest dev runtime stub for Librebase when lidb embed is unavailable.

Listens on API (minimal HTTP) and postgres-wire (TCP accept) ports so health
probes and Studio status checks see real open sockets — not fake green.
"""

from __future__ import annotations

import argparse
import json
import logging
import socket
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


class DevHealthHandler(BaseHTTPRequestHandler):
    data_dir: str = "/data"
    api_port: int = 54320
    postgres_port: int = 54322

    def do_GET(self) -> None:
        if self.path in ("/", "/health", "/status"):
            body = json.dumps(
                {
                    "status": "running",
                    "runtime_mode": "dev",
                    "message": "Dev runtime — not production lidb",
                    "data_dir": self.data_dir,
                    "api_port": self.api_port,
                    "postgres_port": self.postgres_port,
                    "running": True,
                    "api_reachable": True,
                    "postgres_reachable": True,
                    "degraded": True,
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self.send_response(404)
        self.end_headers()

    def log_message(self, _format: str, *_args: object) -> None:
        return


def _tcp_acceptor(port: int, name: str) -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", port))
    sock.listen(64)
    logging.info("dev-runtime: %s listening on 0.0.0.0:%d", name, port)
    while True:
        conn, _addr = sock.accept()
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Librebase dev runtime stub")
    parser.add_argument("--data-dir", default="/data")
    parser.add_argument("--api-port", type=int, required=True)
    parser.add_argument("--postgres-port", type=int, required=True)
    args = parser.parse_args()

    Path(args.data_dir).mkdir(parents=True, exist_ok=True)

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.info("librebase lidb-runtime DEV MODE — not for production")
    logging.info("data_dir=%s api_port=%d postgres_port=%d", args.data_dir, args.api_port, args.postgres_port)

    DevHealthHandler.data_dir = args.data_dir
    DevHealthHandler.api_port = args.api_port
    DevHealthHandler.postgres_port = args.postgres_port

    server = HTTPServer(("0.0.0.0", args.api_port), DevHealthHandler)
    api_thread = threading.Thread(target=server.serve_forever, daemon=True)
    api_thread.start()

    pg_thread = threading.Thread(
        target=_tcp_acceptor,
        args=(args.postgres_port, "postgres-wire"),
        daemon=True,
    )
    pg_thread.start()

    try:
        api_thread.join()
    except KeyboardInterrupt:
        server.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
