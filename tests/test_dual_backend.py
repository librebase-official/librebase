"""Tests for dual-backend (SQLite + Postgres) support in LiorgDb.

Validates that:
  - The _psql() placeholder converter turns SQLite ? into Postgres %s.
  - Migration SQL files contain only Postgres-compatible DDL (no SQLite-isms).
  - LiorgDb.__init__ accepts either path or dsn.
"""

from __future__ import annotations

import importlib.util
import os
import re
from pathlib import Path
from unittest import mock

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "admin-api" / "scripts"
SERVER = SCRIPTS / "admin_server.py"
MIGRATIONS = Path(__file__).resolve().parents[1] / "admin-api" / "migrations"

SQLITE_ONLY_PATTERNS = [
    re.compile(r"INSERT\s+OR\s+IGNORE", re.I),
    re.compile(r"INSERT\s+OR\s+REPLACE", re.I),
    re.compile(r"last_insert_rowid", re.I),
    re.compile(r"\bPRAGMA\b", re.I),
    re.compile(r"\bVACUUM\b", re.I),
    re.compile(r"\bATTACH\s+DATABASE\b", re.I),
    re.compile(r"\bDETACH\s+DATABASE\b", re.I),
    re.compile(r"\bGLOB\b", re.I),
    re.compile(r"\bESCAPE\s+?", re.I),
]


def load_server():
    spec = importlib.util.spec_from_file_location("admin_server_dual", SERVER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _has_psycopg2():
    try:
        import psycopg2  # noqa: F401
        return True
    except ImportError:
        return False


LiorgDb = load_server().LiorgDb


class TestPsqlPlaceholderConversion:
    def test_converts_placeholders(self):
        sql = "SELECT * FROM users WHERE id = ? AND email = ?"
        assert LiorgDb._psql(sql) == "SELECT * FROM users WHERE id = %s AND email = %s"

    def test_no_placeholders_unchanged(self):
        sql = "SELECT * FROM users WHERE id = 'abc'"
        assert LiorgDb._psql(sql) == sql


class TestMigrationSqlPostgresCompatibility:
    @pytest.mark.parametrize(
        "mig_file",
        sorted(MIGRATIONS.glob("*.sql")),
        ids=lambda p: p.name,
    )
    def test_no_sqlite_only_patterns(self, mig_file):
        text = mig_file.read_text(encoding="utf-8")
        for pattern in SQLITE_ONLY_PATTERNS:
            assert not pattern.search(text), (
                f"{mig_file.name}: contains SQLite-only pattern {pattern.pattern!r}"
            )

    def test_migrations_use_standard_types(self):
        """Ensure we don't use SQLite-specific types like AUTOINCREMENT."""
        for mig in sorted(MIGRATIONS.glob("*.sql")):
            text = mig.read_text(encoding="utf-8")
            assert "AUTOINCREMENT" not in text, f"{mig.name}: uses AUTOINCREMENT"


class TestLiorgDbInit:
    def test_requires_path_or_dsn(self):
        with pytest.raises((AssertionError, TypeError)):
            LiorgDb()

    def test_path_works(self, tmp_path):
        db = LiorgDb(Path(tmp_path) / "test.db")
        assert db._backend == "sqlite"
        db.close()

    def test_dsn_routes_to_postgres(self):
        """With a dsn, _backend must be postgres (connect validated separately)."""
        spec = importlib.util.spec_from_file_location("admin_server_dual2", SERVER)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        with mock.patch("psycopg2.connect") as mock_connect:
            mock_conn = mock_connect.return_value
            db = mod.LiorgDb(dsn="postgresql://user:pass@localhost/db")
            assert db._backend == "postgres"
            assert db.conn is mock_conn
            db.close()

    @pytest.mark.skipif(
        not _has_psycopg2(),
        reason="psycopg2-binary not installed (no Postgres available)",
    )
    def test_postgres_migrations_and_crud(self):
        """Full migration + CRUD against a real Postgres instance."""
        dsn = os.environ.get("LIBREBASE_TEST_PG_DSN", "postgresql://postgres:postgres@localhost:5432/postgres")
        try:
            db = LiorgDb(dsn=dsn)
        except Exception as e:
            pytest.skip(f"Postgres not reachable at {dsn}: {e}")
        assert db._backend == "postgres"
        try:
            row = db.fetchone("SELECT 1 AS val")
            assert row is not None
            assert row["val"] == 1
            org_id = f"org_test_{__import__('time').time_ns()}"
            db.execute(
                "INSERT INTO organizations (id, name, slug, edition, created_at) "
                "VALUES (%s, %s, %s, %s, %s)",
                (org_id, "Test", f"test-{org_id}", "free", "2026-01-01"),
            )
            found = db.fetchone("SELECT * FROM organizations WHERE id = %s", (org_id,))
            assert found is not None
            assert found["id"] == org_id
            assert found["plan"] == "suspended"
            # idempotency: re-init should not error
            db2 = LiorgDb(dsn=dsn)
            db2.close()
        finally:
            db.close()
        print("Postgres end-to-end test passed")
