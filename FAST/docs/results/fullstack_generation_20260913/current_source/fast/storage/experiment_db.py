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
-- **主键里必须有 round_index。**
--
-- 原来是 (run_id, label, layer) + INSERT OR REPLACE，于是第 N 轮**覆盖**第
-- N-1 轮：这块板子记的是最终状态，不是轨迹。而它存在的理由正是「完整记录
-- 优化轨迹和参数」——分层重入下同一个候选会被反复规划/实现，覆盖掉的恰好
-- 是「这一层改了之后指标怎么动」，也就是归因唯一的依据。
CREATE TABLE IF NOT EXISTS stage_outputs (
    run_id       TEXT NOT NULL,
    round_index  INTEGER NOT NULL DEFAULT 0,
    label        TEXT NOT NULL,
    layer        TEXT NOT NULL,
    status       TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    error        TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (run_id, round_index, label, layer),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS attributions (
    run_id      TEXT NOT NULL,
    round_index INTEGER NOT NULL DEFAULT 0,
    label       TEXT NOT NULL,
    attribution TEXT NOT NULL,
    decision    TEXT NOT NULL,
    summary     TEXT,
    evidence    TEXT,
    mutations   TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (run_id, round_index, label),
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




def _objectives_of_row(row: dict[str, Any]):
    from fast.agents.codesign import (
        DesignObjectives,
        effective_clock_ns,
        throughput_mac_per_s,
    )

    cycles = row.get("predicted_cycles")
    # **实测到的那一段用实测值。** 计划里的 `predicted_clock_ns` 是模型算的，
    # 而 µArch 的变异改的是 RTL——RTL 变了模型不知道。只有变异被接受、且它
    # 改的模块在时钟模型里（队列/除法器/阵列）时才替换。
    clock = row.get("predicted_clock_ns")
    measured = row.get("measured_critical_path_ns")
    if row.get("mutation_accepted") and row.get("mutation_component") and measured:
        clock = effective_clock_ns(
            num_rows=row.get("num_rows") or 32,
            pe_per_row=row.get("pe_per_row") or 4,
            queue_depth=row.get("queue_depth") or 0,
            divider_stages=row.get("divider_stages") or 8,
            measured={row["mutation_component"]: measured},
        )
    return DesignObjectives(
        latency_ns=cycles * clock if cycles and clock else None,
        power_mw=row.get("predicted_power_mw"),
        area_um2=row.get("predicted_area_um2"),
        throughput_mac_per_s=throughput_mac_per_s(
            clock_ns=clock, num_rows=row.get("num_rows"),
            pe_per_row=row.get("pe_per_row"), utilisation=row.get("pe_utilization"),
        ),
        clock_ns=clock,
    )


def _as_columns(objectives) -> dict[str, Any]:
    return {
        "energy_j": objectives.energy_j,
        "energy_efficiency_tasks_per_j": objectives.energy_efficiency_tasks_per_j,
        "performance_evidence": "L1-model; functional RTL check does not validate performance",
        "energy_scope": "partial-model:execute-array-dynamic+sram-leakage",
        "latency_ns": objectives.latency_ns,
        "power_mw": objectives.power_mw,
        "area_um2": objectives.area_um2,
        "throughput_mac_per_s": objectives.throughput_mac_per_s,
    }

def objective_of(row: dict[str, Any]) -> float | None:
    """一行轨迹的目标值：面积约束下的吞吐（有效 MAC/s）。

    算不出来就返回 None，**不要补默认值**——补出来的数会让这个点在排序里
    占据它没有的位置。
    """
    from fast.agents.codesign import throughput_mac_per_s

    return throughput_mac_per_s(
        clock_ns=row.get("predicted_clock_ns"),
        num_rows=row.get("num_rows"),
        pe_per_row=row.get("pe_per_row"),
        utilisation=row.get("pe_utilization"),
    )

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

    def record_stage(self, run_id: str, label: str, layer: str, payload: Any,
                     *, round_index: int = 0) -> None:
        if payload is None:
            return
        with self._connect() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO stage_outputs
                   (run_id, round_index, label, layer, status, payload_json, error)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (run_id, round_index, label, layer,
                 getattr(getattr(payload, "status", None), "value", "unknown"),
                 canonical_json(payload), getattr(payload, "error", None)),
            )

    def record_attribution(self, run_id: str, label: str, critique: Critique,
                           *, round_index: int = 0) -> None:
        with self._connect() as connection:
            connection.execute(
                """INSERT OR REPLACE INTO attributions
                   (run_id, round_index, label, attribution, decision, summary, evidence, mutations)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (run_id, round_index, label, critique.attribution.value, critique.decision.value,
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

    def trajectory(self, run_id: str) -> list[dict[str, Any]]:
        """这次循环走过的每一轮：计划、实测、归因，按轮排。

        这是**共享板**的主查询——提案 Table II 里 Orchestrator 的输出写的是
        "Prompts, shared state"，Fig. 1 里 Evaluator 挂着 "Shared Data"。
        它有两个消费者：组装 Critic 的 prompt（跨轮对比归因的依据），以及
        回答「这次循环最好的点是哪个」。
        """
        return self.query(
            """SELECT a.round_index, a.label, a.attribution, a.decision, a.summary,
                      json_extract(c.payload_json, '$.num_rows')        AS num_rows,
                      json_extract(c.payload_json, '$.pe_per_row')      AS pe_per_row,
                      json_extract(c.payload_json, '$.queue_depth')     AS queue_depth,
                      json_extract(c.payload_json, '$.divider_stages')   AS divider_stages,
                      json_extract(c.payload_json, '$.predicted_area_um2')  AS predicted_area_um2,
                      json_extract(c.payload_json, '$.predicted_clock_ns')  AS predicted_clock_ns,
                      json_extract(c.payload_json, '$.predicted_power_mw')  AS predicted_power_mw,
                      json_extract(c.payload_json, '$.predicted_cycles')    AS predicted_cycles,
                      json_extract(e.payload_json, '$.fidelity')        AS fidelity,
                      json_extract(e.payload_json, '$.functional_passed') AS functional_passed,
                      json_extract(e.payload_json, '$.pe_utilization')  AS pe_utilization,
                      json_extract(e.payload_json, '$.area')            AS area,
                      json_extract(e.payload_json, '$.cycles')          AS cycles,
                      json_extract(m.payload_json, '$.accepted')        AS mutation_accepted,
                      json_extract(m.payload_json, '$.component')       AS mutation_component,
                      json_extract(m.payload_json, '$.measured_critical_path_ns')
                                                                        AS measured_critical_path_ns
               FROM attributions a
               LEFT JOIN stage_outputs c
                      ON c.run_id = a.run_id AND c.round_index = a.round_index
                     AND c.label = a.label AND c.layer = 'compiler'
               LEFT JOIN stage_outputs e
                      ON e.run_id = a.run_id AND e.round_index = a.round_index
                     AND e.label = a.label AND e.layer = 'evaluator'
               LEFT JOIN stage_outputs m
                      ON m.run_id = a.run_id AND m.round_index = a.round_index
                     AND m.label = a.label AND m.layer = 'uarch_mutation'
               WHERE a.run_id = ?
               ORDER BY a.round_index""",
            (run_id,),
        )

    #: 只有真跑过 RTL 的那一档才算"验证过"。L0/L1 的 functional_passed 恒为
    #: False——那是"这一档答不了"，不是"这个设计不对"。
    VERIFIED_FIDELITY = "L2-rtl-simulation"

    def pareto_front(self, run_id: str, specs=None, objective=None) -> list[dict[str, Any]]:
        """Function-checked designs' model-predicted energy/latency frontier.

        L2 functional evidence gates admission; it does not turn model cycles,
        partial power or area into independent PPA measurements. Evidence scope
        is attached to each row. Violated and unverified active constraints are
        excluded and reported by ``infeasible``.
        """
        from fast.agents.codesign import DesignObjectives, constraint_violations, dominates

        rows = [
            row for row in self.trajectory(run_id)
            if row.get("fidelity") == self.VERIFIED_FIDELITY and row.get("functional_passed")
        ]
        scored = []
        for row in rows:
            objectives = _objectives_of_row(row)
            if not objectives.complete_for(objective):
                continue
            broken = constraint_violations(objectives, specs) if specs is not None else ()
            scored.append((row, objectives, broken))

        feasible = [item for item in scored if not item[2]]
        survivors = [
            (row, objectives) for row, objectives, _ in feasible
            if not any(dominates(other, objectives, objective) for _, other, _ in feasible)
        ]

        # **前沿上不放重复点。** 相等的两个点互不支配（`dominates` 要求至少
        # 一个严格更好），所以它们全都"活"了下来——实测一次 4 轮的设计完全
        # 相同，前沿就报了 4 个一模一样的行。那不是四个可选方案，是一个。
        #
        # 保留最早那一轮，并记下它被复现了几次：同一个设计点被反复到达是
        # 有信息的（说明循环在原地打转），但它不该占四行。
        unique: dict[tuple, dict] = {}
        for row, objectives in survivors:
            key = (objectives.latency_ns, objectives.power_mw,
                   row.get("num_rows"), row.get("pe_per_row"), row.get("queue_depth"))
            if key in unique:
                unique[key]["reached_in_rounds"].append(row["round_index"])
                continue
            unique[key] = {
                **row, **_as_columns(objectives),
                "reached_in_rounds": [row["round_index"]],
            }
        return sorted(unique.values(), key=lambda row: row["latency_ns"])

    def infeasible(self, run_id: str, specs) -> list[dict[str, Any]]:
        """被约束挡掉的点，带上**哪一条**约束挡的。"""
        from fast.agents.codesign import constraint_violations

        out = []
        for row in self.trajectory(run_id):
            if row.get("fidelity") != self.VERIFIED_FIDELITY:
                continue
            objectives = _objectives_of_row(row)
            broken = constraint_violations(objectives, specs)
            if broken:
                out.append({**row, **_as_columns(objectives), "violations": list(broken)})
        return out

    def best_verified(self, run_id: str, specs=None) -> dict[str, Any] | None:
        """前沿上延迟最低的那个点。

        **它只是前沿的一个入口，不是"答案"**——真正的输出是
        `pareto_front()` 那张表。留这个方法是为了给"这次跑出了什么"一个
        一句话的回答。
        """
        front = self.pareto_front(run_id, specs)
        return front[0] if front else None

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
