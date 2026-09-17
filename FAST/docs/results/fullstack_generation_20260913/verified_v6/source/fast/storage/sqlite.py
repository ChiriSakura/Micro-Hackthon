"""Small head-node metadata store; bulk artifacts remain outside SQLite."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3
from typing import Any

from fast.schemas.models import canonical_json, digest_json


_SCHEMA = """
CREATE TABLE IF NOT EXISTS stage_results (
    candidate_key TEXT NOT NULL,
    stage TEXT NOT NULL,
    input_digest TEXT NOT NULL,
    output_digest TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (candidate_key, stage, input_digest)
);
"""


class ExperimentStore:
    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def get(self, candidate_key: str, stage: str, input_digest: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM stage_results WHERE candidate_key=? AND stage=? AND input_digest=?",
                (candidate_key, stage, input_digest),
            ).fetchone()
        return None if row is None else json.loads(row[0])

    def put(self, candidate_key: str, stage: str, inputs: Any, output: Any) -> str:
        input_digest = digest_json(inputs)
        output_digest = digest_json(output)
        payload = canonical_json(output)
        with self._connect() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO stage_results
                   (candidate_key, stage, input_digest, output_digest, payload_json)
                   VALUES (?, ?, ?, ?, ?)""",
                (candidate_key, stage, input_digest, output_digest, payload),
            )
        return output_digest
