from __future__ import annotations

import os
import unittest

from tests.admin_contract.harness import AdminServer, http_json


class TestHealthContract(unittest.TestCase):
    def test_health_ok_python(self) -> None:
        with AdminServer(runtime="python", port=54341) as srv:
            st, body = http_json("GET", f"{srv.base_url}/health")
            self.assertEqual(st, 200)
            self.assertTrue(body.get("ok"))
            self.assertEqual(body.get("service"), "librebase-admin")

    @unittest.skipUnless(os.environ.get("LIBREBASE_ADMIN_CONTRACT_LI") == "1", "set LIBREBASE_ADMIN_CONTRACT_LI=1")
    def test_health_ok_li(self) -> None:
        with AdminServer(runtime="li", port=54342) as srv:
            st, body = http_json("GET", f"{srv.base_url}/health")
            self.assertEqual(st, 200)
            self.assertTrue(body.get("ok"))
            self.assertEqual(body.get("service"), "librebase-admin")
            self.assertEqual(body.get("runtime"), "li")
