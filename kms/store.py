"""KMS key store — SQLite (KEK bootstrap + per-project keys with versions)."""

from __future__ import annotations

import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from . import crypto

DEFAULT_DB = Path.home() / ".local" / "share" / "librebase" / "kms.db"


def _now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class KmsStore:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._schema()
        self.kek = self._load_or_create_kek()

    def _schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS keys (
              key_id TEXT NOT NULL,
              project_id TEXT NOT NULL,
              version INTEGER NOT NULL,
              wrapped_dek TEXT NOT NULL,
              wrapped_sk TEXT NOT NULL,
              pk TEXT NOT NULL,
              created_at TEXT NOT NULL,
              PRIMARY KEY (key_id, version)
            );
            """
        )
        self.conn.commit()

    def _load_or_create_kek(self) -> bytes:
        row = self.conn.execute("SELECT v FROM meta WHERE k = 'kek'").fetchone()
        if row:
            return crypto.b64d(row["v"])
        kek = crypto.generate_kek()
        self.conn.execute(
            "INSERT INTO meta (k, v) VALUES ('kek', ?)", (crypto.b64e(kek),)
        )
        self.conn.commit()
        return kek

    def close(self) -> None:
        self.conn.close()

    # -- queries -----------------------------------------------------------
    def fetchone(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        return self.conn.execute(sql, params).fetchone()

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> None:
        self.conn.execute(sql, params)
        self.conn.commit()

    # -- key ops -----------------------------------------------------------
    def _default_key_id(self, project_id: str) -> str:
        return f"key_{project_id}"

    def create_key(self, project_id: str) -> dict[str, Any]:
        """Create (or return) the current key for a project."""
        key_id = self._default_key_id(project_id)
        rows = self.conn.execute(
            "SELECT * FROM keys WHERE key_id = ? ORDER BY version DESC", (key_id,)
        ).fetchall()
        if rows:
            return self._row(rows[0])
        return self._insert_version(project_id, key_id, 1)

    def _insert_version(self, project_id: str, key_id: str, version: int) -> dict[str, Any]:
        dek = crypto.generate_dek()
        sk, pk = crypto.generate_ed25519()
        now = _now()
        self.conn.execute(
            "INSERT INTO keys (key_id, project_id, version, wrapped_dek, wrapped_sk, pk, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                key_id,
                project_id,
                version,
                crypto.wrap(self.kek, dek),
                crypto.wrap(self.kek, sk),
                crypto.b64e(pk),
                now,
            ),
        )
        self.conn.commit()
        return self._row(self.conn.execute("SELECT * FROM keys WHERE key_id = ? AND version = ?", (key_id, version)).fetchone())

    def rotate(self, project_id: str, key_id: str) -> dict[str, Any]:
        row = self.conn.execute(
            "SELECT version FROM keys WHERE key_id = ? ORDER BY version DESC", (key_id,)
        ).fetchone()
        version = (row["version"] + 1) if row else 1
        return self._insert_version(project_id, key_id, version)

    def list_keys(self, project_id: str) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM keys WHERE project_id = ? ORDER BY key_id, version",
            (project_id,),
        ).fetchall()
        return [self._row(r) for r in rows]

    def get_key(self, key_id: str) -> sqlite3.Row | None:
        """Raw latest row (internal — has wrapped_dek/wrapped_sk/pk)."""
        return self.conn.execute(
            "SELECT * FROM keys WHERE key_id = ? ORDER BY version DESC", (key_id,)
        ).fetchone()

    def get_key_public(self, key_id: str) -> dict[str, Any] | None:
        row = self.get_key(key_id)
        return self._row(row) if row else None

    def delete_key(self, key_id: str) -> bool:
        cur = self.conn.execute("DELETE FROM keys WHERE key_id = ?", (key_id,))
        self.conn.commit()
        return cur.rowcount > 0

    # -- crypto ops --------------------------------------------------------
    def _dek(self, row: sqlite3.Row) -> bytes:
        return crypto.unwrap(self.kek, row["wrapped_dek"])

    def _sk(self, row: sqlite3.Row) -> bytes:
        return crypto.unwrap(self.kek, row["wrapped_sk"])

    def _pk(self, row: sqlite3.Row) -> bytes:
        return crypto.b64d(row["pk"])

    def encrypt(self, row: sqlite3.Row, plaintext: bytes) -> str:
        return crypto.seal(self._dek(row), plaintext)

    def decrypt(self, row: sqlite3.Row, ciphertext: str) -> bytes:
        return crypto.open_seal(self._dek(row), ciphertext)

    def sign(self, row: sqlite3.Row, message: bytes) -> str:
        return crypto.b64e(crypto.ed25519_sign(self._sk(row), message))

    def verify(self, row: sqlite3.Row, message: bytes, signature: str) -> bool:
        return crypto.ed25519_verify(self._pk(row), message, crypto.b64d(signature))

    @staticmethod
    def _row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "keyId": row["key_id"],
            "projectId": row["project_id"],
            "version": row["version"],
            "publicKey": row["pk"],
            "createdAt": row["created_at"],
        }
