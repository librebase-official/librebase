"""Integration test — admin-api OAuth provider config with KMS-sealed secrets."""

from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "admin-api" / "scripts"


def load_server():
    spec = importlib.util.spec_from_file_location("admin_server", SCRIPTS / "admin_server.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestAdminProviders(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = load_server()
        cls._tmp = tempfile.TemporaryDirectory()

        from kms.server import KmsHandler
        from kms.store import KmsStore

        cls.kms_db = KmsStore(Path(cls._tmp.name) / "kms.db")
        KmsHandler.db = cls.kms_db
        KmsHandler.service_role = "kms-role"
        cls.kms = ThreadingHTTPServer(("127.0.0.1", 0), KmsHandler)
        cls.kms_port = cls.kms.server_address[1]
        Thread(target=cls.kms.serve_forever, daemon=True).start()

        cls.admin_db = cls.mod.LiorgDb(Path(cls._tmp.name) / "org.db")
        cls.mod.LiorgHandler.db = cls.admin_db
        cls.mod.LiorgHandler.jwt_secret = "admin-secret"
        os.environ["LIBREBASE_KMS_URL"] = f"http://127.0.0.1:{cls.kms_port}"
        os.environ["LIBREBASE_KMS_SERVICE_ROLE"] = "kms-role"
        cls.admin = ThreadingHTTPServer(("127.0.0.1", 0), cls.mod.LiorgHandler)
        cls.admin_port = cls.admin.server_address[1]
        Thread(target=cls.admin.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.admin.shutdown()
        cls.admin.server_close()
        cls.kms.shutdown()
        cls.kms.server_close()
        cls.admin_db.close()
        cls.kms_db.close()
        os.environ.pop("LIBREBASE_KMS_URL", None)
        os.environ.pop("LIBREBASE_KMS_SERVICE_ROLE", None)
        cls._tmp.cleanup()

    def _req(self, method, path, body=None, token=None):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        req = Request(
            f"http://127.0.0.1:{self.admin_port}{path}",
            data=json.dumps(body).encode() if body is not None else None,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(req) as r:
                return r.status, json.loads(r.read() or b"{}")
        except Exception as e:  # noqa: BLE001
            if hasattr(e, "code"):
                return e.code, json.loads(e.read() or b"{}")
            raise

    def test_provider_lifecycle_with_kms_seal(self) -> None:
        st, setup = self._req(
            "POST",
            "/org/v1/setup",
            {"name": "Acme", "ownerEmail": "o@a.test", "password": "hunter2hunter2"},
        )
        self.assertEqual(st, 201, setup)
        token, org = setup["token"], setup["orgId"]

        now = self.mod.utc_now()
        self.admin_db.execute(
            "INSERT INTO projects (id, org_id, name, instance_id, deployment_mode, region, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("proj_1", org, "app", "inst_x", "dedicated", "local", now, now),
        )

        st, prov = self._req(
            "POST",
            f"/org/v1/orgs/{org}/projects/proj_1/providers",
            {
                "provider": "github",
                "clientId": "cid-123",
                "clientSecret": "s3cret-value",
                "redirectUris": ["https://app.example.com/auth/v1/callback"],
            },
            token,
        )
        self.assertEqual(st, 200, prov)
        self.assertEqual(prov["clientId"], "cid-123")
        self.assertNotIn("clientSecret", prov)  # masked

        st, lst = self._req("GET", f"/org/v1/orgs/{org}/projects/proj_1/providers", token=token)
        self.assertEqual(st, 200)
        self.assertEqual(len(lst), 1)

        st, full = self._req(
            "GET", f"/org/v1/orgs/{org}/projects/proj_1/providers/github", token=token
        )
        self.assertEqual(st, 200, full)
        self.assertIn("clientSecretEnc", full)
        self.assertIn("kmsKeyId", full)

        plain = self.mod.kms_unseal(full["kmsKeyId"], full["clientSecretEnc"])
        self.assertEqual(plain, "s3cret-value")

        st, _ = self._req(
            "DELETE", f"/org/v1/orgs/{org}/projects/proj_1/providers/github", token=token
        )
        self.assertEqual(st, 200)
        st, lst = self._req("GET", f"/org/v1/orgs/{org}/projects/proj_1/providers", token=token)
        self.assertEqual(len(lst), 0)


if __name__ == "__main__":
    unittest.main()
