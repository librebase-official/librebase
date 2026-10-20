"""OSS compose must not expose Admin or KMS on the host (Studio loopback only)."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OSS_COMPOSE = ROOT / "deploy" / "compose" / "docker-compose.yml"
STUDIO_COMPOSE = ROOT / "data-studio-ui" / "docker-compose.yml"

# Host port mappings: "HOST:CONTAINER" or "IP:HOST:CONTAINER"
_PORT_MAP = re.compile(
    r'^\s*-\s*["\']?(?:(?P<host_ip>[\d.]+):)?(?P<host_port>\d+):(?P<container_port>\d+)["\']?\s*$'
)


def _port_mappings(compose_text: str) -> list[tuple[str | None, str, str]]:
    mappings: list[tuple[str | None, str, str]] = []
    for line in compose_text.splitlines():
        m = _PORT_MAP.match(line)
        if m:
            mappings.append(
                (m.group("host_ip"), m.group("host_port"), m.group("container_port"))
            )
    return mappings


class TestComposePortSecurity(unittest.TestCase):
    def test_oss_compose_uses_bridge_network_not_shared_netns(self) -> None:
        text = OSS_COMPOSE.read_text()
        self.assertNotIn('network_mode: "service:kms"', text)
        self.assertNotIn("network_mode: service:kms", text)
        self.assertIn("librebase-deploy-net", text)
        self.assertIn("LIBREBASE_ADMIN_URL: http://librebase-admin:54330", text)
        self.assertIn("LIBREBASE_KMS_URL: http://kms:54340", text)

    def test_oss_compose_publishes_only_studio_on_loopback(self) -> None:
        text = OSS_COMPOSE.read_text()
        mappings = _port_mappings(text)
        self.assertTrue(mappings, "expected at least one published port (Studio)")
        for host_ip, host_port, container_port in mappings:
            self.assertEqual(
                container_port,
                "3005",
                f"only Studio (3005) may be published, found container port {container_port}",
            )
            self.assertEqual(
                host_port,
                "3005",
                f"unexpected host port {host_port}",
            )
            self.assertEqual(
                host_ip,
                "127.0.0.1",
                f"Studio must bind 127.0.0.1 on host, got {host_ip!r}",
            )
        published_container_ports = {c for _, _, c in mappings}
        self.assertNotIn("54330", published_container_ports)
        self.assertNotIn("54340", published_container_ports)
        for host_ip, host_port, container_port in mappings:
            if host_ip is None:
                self.fail(
                    f"bare host port publish {host_port}:{container_port} "
                    "(must use 127.0.0.1:host:container)"
                )

    def test_studio_only_compose_does_not_publish_admin_or_kms(self) -> None:
        mappings = _port_mappings(STUDIO_COMPOSE.read_text())
        container_ports = {c for _, _, c in mappings}
        self.assertNotIn("54330", container_ports)
        self.assertNotIn("54340", container_ports)
        for host_ip, host_port, container_port in mappings:
            if container_port == "3005":
                self.assertEqual(host_ip, "127.0.0.1")


if __name__ == "__main__":
    unittest.main()
