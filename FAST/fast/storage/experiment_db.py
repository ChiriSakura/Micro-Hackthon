"""The shared experiment database: what the Critic attributes from.

Fig. 1 of the proposal puts a "Shared Data" store at the centre of the loop, and
Table II makes cross-layer attribution the Critic's action. Attribution is a join:
to say "this candidate's PE utilisation is low *because* the kernel left the rows
imbalanced" you need the kernel profile, the compiler schedule, the hardware
parameters and the evaluation sitting in one row.

This is deliberately separate from :class:`ExperimentStore`. That one is a
content-addressed cache whose job is to avoid re-running expensive work; this one
is an append-only record whose job is to be queried afterwards. Merging them
would make the cache's keys answer questions they were not designed for.

Rejected proposals are recorded too. A search that only stores what it measured
cannot answer "what did the agent consider and rule out", which is the first
question asked when a search goes somewhere strange.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Iterable

from fast.schemas.models import (
    CompilerSchedule,
    Critique,
    EvaluationResult,
    ExperimentSpec,
    HardwareCandidate,
    KernelMeasurement,
    KernelSearchReport,
    canonical_json,
    digest_json,
    to_primitive,
)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id        TEXT PRIMARY KEY,
    experiment_id TEXT NOT NULL,
    candidate_id  TEXT NOT NULL,
    spec_digest   TEXT NOT NULL,
    spec_json     TEXT NOT NULL,
    proposer      TEXT,
    host          TEXT,
    slurm_job_id  TEXT,
    started_at    TEXT NOT NULL,
    finished_at   TEXT
);

-- Every configuration any agent put forward, measured or not. `accepted=0`
-- rows are why a search went where it did.
CREATE TABLE IF NOT EXISTS proposals (
    run_id        TEXT NOT NULL,
    round         INTEGER NOT NULL,
    layer         TEXT NOT NULL,
    label         TEXT NOT NULL,
    proposed_by   TEXT NOT NULL,
    rationale     TEXT,
    expected_effect TEXT,
    accepted      INTEGER NOT NULL,
    reject_reason TEXT,
    created_at    TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS kernel_measurements (
    run_id           TEXT NOT NULL,
    label            TEXT NOT NULL,
    status           TEXT NOT NULL,
    perplexity       REAL,
    quality_loss     REAL,
    actual_sparsity  REAL,
    index_entropy    REAL,
    block_occupancy  REAL,
    load_imbalance   REAL,
    column_top5_mass REAL,
    profile_json     TEXT,
    wall_seconds     REAL,
    proposed_by      TEXT,
    error            TEXT,
    PRIMARY KEY (run_id, label),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

-- One row per downstream stage, keyed by the kernel label it descends from, so
-- the layers can be joined without guessing which candidate produced what.
CREATE TABLE IF NOT EXISTS stage_outputs (
    run_id       TEXT NOT NULL,
    label        TEXT NOT NULL,
    layer        TEXT NOT NULL,
    status       TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    error        TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (run_id, label, layer),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS attributions (
    run_id      TEXT NOT NULL,
    label       TEXT NOT NULL,
    attribution TEXT NOT NULL,
    decision    TEXT NOT NULL,
    summary     TEXT,
    evidence    TEXT,
    mutations   TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (run_id, label),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_measurements_sparsity
    ON kernel_measurements(actual_sparsity);
CREATE INDEX IF NOT EXISTS idx_stage_layer ON stage_outputs(layer);

-- The join the Critic attributes from: one row per candidate, every layer's
-- numbers side by side. A view, not a table, so it can never drift from
-- the rows it summarises.
CREATE VIEW IF NOT EXISTS cross_layer AS
SELECT
    m.run_id,
    r.experiment_id,
    m.label,
    m.quality_loss,
    m.actual_sparsity,
    m.block_occupancy,
    m.load_imbalance,
    m.column_top5_mass,
    json_extract(c.payload_json, '$.parallelism')            AS compiler_parallelism,
    json_extract(c.payload_json, '$.predicted_utilization')  AS compiler_predicted_utilization,
    json_extract(c.payload_json, '$.data_layout')            AS compiler_layout,
    json_extract(h.payload_json, '$.pe_rows')                AS pe_rows,
    json_extract(h.payload_json, '$.pe_cols')                AS pe_cols,
    json_extract(e.payload_json, '$.pe_utilization')         AS eval_pe_utilization,
    json_extract(e.payload_json, '$.cycles')                 AS eval_cycles,
    json_extract(e.payload_json, '$.edp')                    AS eval_edp,
    a.attribution,
    a.decision
FROM kernel_measurements m
JOIN runs r          ON r.run_id = m.run_id
LEFT JOIN stage_outputs c ON c.run_id = m.run_id AND c.label = m.label AND c.layer = 'compiler'
LEFT JOIN stage_outputs h ON h.run_id = m.run_id AND h.label = m.label AND h.layer = 'uarch'
LEFT JOIN stage_outputs e ON e.run_id = m.run_id AND e.label = m.label AND e.layer = 'evaluator'
LEFT JOIN attributions a  ON a.run_id = m.run_id AND a.label = m.label;
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExperimentDB:
    """Append-only shared state across agents, queryable by the Critic."""

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.executescript(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=30)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    # --- writing ----------------------------------------------------------

    def start_run(
        self,
        spec: ExperimentSpec,
        *,
        proposer: str = "",
        host: str = "",
        slurm_job_id: str | None = None,
    ) -> str:
        """Open a run and return its id; the digest makes reruns comparable."""
        run_id = f"{spec.experiment_id}/{spec.candidate_id}/{digest_json(spec)[:12]}"
        with self._connect() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO runs
                   (run_id, experiment_id, candidate_id, spec_digest, spec_json,
                    proposer, host, slurm_job_id, started_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (run_id, spec.experiment_id, spec.candidate_id, digest_json(spec),
                 canonical_json(spec), proposer, host, slurm_job_id, _now()),
            )
        return run_id

    def finish_run(self, run_id: str) -> None:
        with self._connect() as connection:
            connection.execute("UPDATE runs SET finished_at=? WHERE run_id=?", (_now(), run_id))

    def record_proposals(self, run_id: str, round_index: int, layer: str, candidates, *, accepted=True, reject_reason=None) -> None:
        rows = [
            (run_id, round_index, layer, item.label, item.proposed_by,
             json.dumps(list(item.rationale)), item.expected_effect,
             1 if accepted else 0, reject_reason)
            for item in candidates
        ]
        if not rows:
            return
        with self._connect() as connection:
            connection.executemany(
                """INSERT INTO proposals
                   (run_id, round, layer, label, proposed_by, rationale,
                    expected_effect, accepted, reject_reason)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                rows,
            )

    def record_rejections(self, run_id: str, round_index: int, layer: str, reasons: Iterable[str]) -> None:
        """A rejection has no candidate object; the reason is the record."""
        rows = [
            (run_id, round_index, layer, _label_from_reason(reason), "rejected",
             json.dumps([reason]), "", 0, reason)
            for reason in reasons
        ]
        if not rows:
            return
        with self._connect() as connection:
            connection.executemany(
                """INSERT INTO proposals
                   (run_id, round, layer, label, proposed_by, rationale,
                    expected_effect, accepted, reject_reason)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                rows,
            )

    def record_measurements(self, run_id: str, measurements: Iterable[KernelMeasurement]) -> None:
        rows = []
        for item in measurements:
            profile = item.profile
            rows.append((
                run_id, item.label, item.status.value, item.perplexity, item.quality_loss,
                item.actual_sparsity, item.index_entropy, item.block_occupancy,
                profile.load_imbalance if profile else None,
                profile.column_top5_mass if profile else None,
                canonical_json(profile) if profile else None,
                item.wall_seconds, item.proposed_by, item.error,
            ))
        if not rows:
            return
        with self._connect() as connection:
            connection.executemany(
                """INSERT OR REPLACE INTO kernel_measurements
                   (run_id, label, status, perplexity, quality_loss, actual_sparsity,
                    index_entropy, block_occupancy, load_imbalance, column_top5_mass,
                    profile_json, wall_seconds, proposed_by, error)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                rows,
            )

    def record_stage(self, run_id: str, label: str, layer: str, payload: Any) -> None:
        if payload is None:
            return
        with self._connect() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO stage_outputs
                   (run_id, label, layer, status, payload_json, error)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (run_id, label, layer,
                 getattr(getattr(payload, "status", None), "value", "unknown"),
                 canonical_json(payload), getattr(payload, "error", None)),
            )

    def record_attribution(self, run_id: str, label: str, critique: Critique) -> None:
        with self._connect() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO attributions
                   (run_id, label, attribution, decision, summary, evidence, mutations)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (run_id, label, critique.attribution.value, critique.decision.value,
                 critique.summary, json.dumps(list(critique.evidence)),
                 json.dumps(to_primitive(list(critique.mutations)))),
            )

    def record_search(self, report: KernelSearchReport, *, run_id: str | None = None) -> str:
        """Persist a whole kernel search: measurements, proposals, rejections."""
        run_id = run_id or self.start_run(report.spec, proposer=report.proposer)
        self.record_measurements(run_id, report.measurements)
        self.record_proposals(
            run_id, 0, "kernel",
            [_as_candidate(item) for item in report.measurements],
        )
        self.record_rejections(run_id, 0, "kernel", report.rejected)
        self.finish_run(run_id)
        return run_id

    # --- reading: what the Critic asks --------------------------------------

    def cross_layer(self, run_id: str | None = None) -> list[dict[str, Any]]:
        """One row per candidate with every layer's numbers side by side."""
        query = "SELECT * FROM cross_layer"
        params: tuple = ()
        if run_id:
            query += " WHERE run_id = ?"
            params = (run_id,)
        with self._connect() as connection:
            return [dict(row) for row in connection.execute(query, params)]

    def query(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        """Read-only escape hatch for attribution questions not covered above."""
        if not sql.lstrip().upper().startswith(("SELECT", "WITH")):
            raise ValueError("ExperimentDB.query is read-only; use the record_* methods to write")
        with self._connect() as connection:
            return [dict(row) for row in connection.execute(sql, params)]

    def frontier(self, run_id: str, epsilon: float) -> list[dict[str, Any]]:
        """Measured configurations inside the accuracy budget, sparsest first."""
        return self.query(
            """SELECT label, quality_loss, actual_sparsity, block_occupancy, load_imbalance
               FROM kernel_measurements
               WHERE run_id = ? AND status = 'passed' AND quality_loss <= ?
               ORDER BY actual_sparsity DESC""",
            (run_id, epsilon),
        )

    def rejected(self, run_id: str) -> list[dict[str, Any]]:
        return self.query(
            "SELECT round, label, reject_reason FROM proposals "
            "WHERE run_id = ? AND accepted = 0 ORDER BY round",
            (run_id,),
        )


def _as_candidate(measurement: KernelMeasurement):
    from fast.schemas.models import KernelCandidate

    return KernelCandidate(
        label=measurement.label,
        proposed_by=measurement.proposed_by or "unknown",
        rationale=measurement.rationale,
    )


def _label_from_reason(reason: str) -> str:
    """Rejections read "<label>: <why>", and a label contains colons of its own.

    Splitting on the first colon turns "xm:999:1:64: outside the space" into
    "xm", so the split is on the LAST ": " - the separator the writer used.
    """
    head, separator, _ = reason.rpartition(": ")
    if not separator:
        return "(unnamed)"
    head = head.strip()
    return head if head and " " not in head else "(unnamed)"
