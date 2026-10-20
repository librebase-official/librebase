"""Keep self-hosting docs aligned with llms.txt onboarding hints."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestSelfHostingDocs(unittest.TestCase):
    def test_self_hosting_doc_covers_headless_onboarding(self) -> None:
        doc = (ROOT / "docs" / "self-hosting.md").read_text()
        llms = (ROOT / "data-studio-ui" / "app" / "llms.txt" / "route.ts").read_text()
        for needle in (
            "/org/v1/setup",
            "mcp-keys/rotate",
            "lb_mcp_",
            "/api/mcp",
        ):
            self.assertIn(needle, doc, f"docs/self-hosting.md missing {needle}")
        self.assertTrue("self-hosting.md" in llms or "Self-host" in llms)
        self.assertIn("/org/v1/setup", llms)


if __name__ == "__main__":
    unittest.main()
