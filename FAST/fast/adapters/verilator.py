"""Evaluation that actually simulates the RTL, and can therefore disagree.

``AnalyticalEvaluationAdapter`` carries a warning it cannot escape: it scores a
design with the same cost model the co-optimizer used to pick it, so agreement
is arithmetic rather than confirmation, and its ``functional_passed`` is the
constant ``False`` because a model cannot establish correctness. This adapter is
the other half. It elaborates the candidate's Chisel at the candidate's own
parameters, verilates it, and runs the golden testbench, so:

  * ``functional_passed`` becomes a measurement. It is ``True`` only when the
    simulation agreed with a reference on every checked cycle, and the reference
    is not this project's cost model -- it is ``torch.topk``, or a bit-exact
    mirror of the datapath, or a model of what a correct SRAM does.
  * ``fidelity`` says ``L2-rtl-simulation``, which travels with the result.
  * a *disagreement is possible*. Six defects in DynaX's release were found this
    way, two of which lint clean and only fail in simulation, plus one usage
    constraint (PrePEArray's pair ordering) that only a software reference could
    have settled.

What it is not: a performance model. Verilating one module and driving golden
vectors through it measures whether the arithmetic is right, not how many cycles
a full attention layer takes on an array of them. Cycle counts, area and power
therefore still come from the analytical model, and the evidence says so rather
than letting an L2 label imply that every field was simulated.

Cost: a run is a Slurm job -- JVM start, Chisel elaboration, Verilator build --
so it is minutes, not milliseconds. It is meant for confirming the design a
search selected, not for scoring every candidate inside the search loop. The
result cache makes a repeat of the same (template, parameters) free.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
import subprocess
import time

from fast.agents.templates import TemplateRecord
from fast.schemas.models import (
    EvaluationResult,
    ExperimentSpec,
    HardwareCandidate,
    Status,
)

# The last line of a testbench run: "PASSED: 0 mismatches across N ..." or
# "FAILED: k mismatches across N ...". Parsed rather than trusted to the exit
# code alone so a mismatch count reaches the evidence.
_VERDICT = re.compile(r"^(PASSED|FAILED): (\d+) mismatches across (\d+)", re.MULTILINE)


@dataclass(frozen=True)
class SimulationOutcome:
    """What one elaborate-verilate-simulate run produced."""

    passed: bool
    mismatches: int
    checked: int
    wall_seconds: float
    log_uri: str
    error: str | None = None


@dataclass(frozen=True)
class TemplateBench:
    """How to build and drive one template's simulation.

    A template is only simulatable if someone wrote a reference for it, so this
    mapping is the honest list of what L2 can currently reach. A candidate whose
    template is absent here is reported as skipped, never as passed.
    """

    elaborate_target: str
    top_module: str
    testbench: str
    golden_args: tuple[str, ...]
    sim_args: tuple[str, ...] = ()


# Keyed by template_id. Every entry corresponds to a bench that has run and
# agreed; see FAST/hardware/README.md for the reference each one uses.
DEFAULT_BENCHES: dict[str, TemplateBench] = {
    "topk": TemplateBench("TopK", "TopK", "tb_topk.cpp", (), ("16",)),
    "exp_unit": TemplateBench(
        "ExpUnit", "ExpUnitFixPoint", "tb_exp.cpp", ("--module", "ExpUnit")
    ),
    "psum_softmax": TemplateBench(
        "PSumSoftmax", "PSumSoftmax", "tb_psum_softmax.cpp", ("--module", "PSumSoftmax")
    ),
    "sram": TemplateBench("SRAM", "SRAM", "tb_sram.cpp", ("--module", "SRAM")),
    "repe": TemplateBench("RePE", "RePE", "tb_repe.cpp", ("--module", "RePE")),
    "prepe": TemplateBench(
        "PrePE_1_2", "PrePE_1_2", "tb_prepe.cpp",
        ("--module", "PrePE", "--out-bits", "12"),
    ),
    # The 1:2 path. The 1:4 array has its own bench and its own elaboration
    # target (PrePEArray14_T / tb_prepe_array14.cpp); both run in
    # slurm/rtl/fast_rtl_verify_all.slurm, and this table names the one an L2
    # evaluation of a `prepe_array` candidate reaches for.
    "prepe_array": TemplateBench(
        "PrePEArray_T", "PrePEArray_1_2", "tb_prepe_array.cpp",
        ("--module", "PrePEArray", "--height", "2", "--width", "8",
         "--out-bits", "12"),
    ),
    "repe_array": TemplateBench(
        "RePEArray_T", "RePEArray", "tb_repe_array.cpp",
        ("--module", "RePEArray", "--num-rows", "4", "--pe-count", "2",
         "--reg-width", "4"),
    ),
}


@dataclass
class VerilatorEvaluationAdapter:
    """Run a template's golden testbench and report what it found.

    Args:
        repo_root: the Micro-Hackthon checkout, so the adapter can find both
            ``slurm/rtl/fast_rtl_verify.slurm`` and ``FAST/hardware``.
        launcher: how to run the verification script. The default runs it
            through ``bash`` in the current allocation, which is what a driver
            already inside a Slurm job wants; ``("sbatch", "--wait")`` submits
            it as its own job instead. The script is not marked executable, so
            an interpreter has to be named either way.
        benches: overridable for testing.
    """

    repo_root: Path
    launcher: tuple[str, ...] = ("bash",)
    benches: dict[str, TemplateBench] = field(
        default_factory=lambda: dict(DEFAULT_BENCHES)
    )
    timeout_seconds: int = 3600
    env: dict[str, str] | None = None
    # (template_id, top_module) -> outcome. Elaboration is deterministic and the
    # golden vectors are seeded, so a repeat cannot differ.
    _cache: dict[tuple[str, str], SimulationOutcome] = field(
        default_factory=dict, repr=False
    )

    def bench_for(self, template: TemplateRecord | None) -> TemplateBench | None:
        if template is None:
            return None
        return self.benches.get(template.template_id)

    def simulate(self, bench: TemplateBench) -> SimulationOutcome:
        """Elaborate, verilate and run one testbench, returning what it found."""
        key = (bench.elaborate_target, bench.top_module)
        if key in self._cache:
            return self._cache[key]

        script = self.repo_root / "slurm" / "rtl" / "fast_rtl_verify.slurm"
        environment = dict(os.environ if self.env is None else self.env)
        environment.update(
            FAST_RTL_TARGET=bench.elaborate_target,
            FAST_RTL_TOP=bench.top_module,
            FAST_RTL_TB=bench.testbench,
            FAST_RTL_GOLDEN=" ".join(bench.golden_args),
            FAST_RTL_SIM=" ".join(bench.sim_args),
        )

        started = time.time()
        try:
            completed = subprocess.run(
                [*self.launcher, str(script)],
                capture_output=True, text=True,
                timeout=self.timeout_seconds, env=environment,
                cwd=str(self.repo_root),
            )
        except subprocess.TimeoutExpired:
            outcome = SimulationOutcome(
                passed=False, mismatches=-1, checked=0,
                wall_seconds=time.time() - started, log_uri="",
                error=f"simulation exceeded {self.timeout_seconds}s",
            )
            self._cache[key] = outcome
            return outcome

        text = completed.stdout + completed.stderr
        verdict = _VERDICT.search(text)
        if verdict is None:
            # No verdict line means the run never reached the simulator --
            # elaboration or the Verilator build failed. That is a real result
            # about the RTL, so it is reported rather than retried silently.
            outcome = SimulationOutcome(
                passed=False, mismatches=-1, checked=0,
                wall_seconds=time.time() - started, log_uri="",
                error=(
                    "no simulation verdict: "
                    + (text.strip().splitlines() or ["(no output)"])[-1][:200]
                ),
            )
        else:
            outcome = SimulationOutcome(
                passed=verdict.group(1) == "PASSED",
                mismatches=int(verdict.group(2)),
                checked=int(verdict.group(3)),
                wall_seconds=time.time() - started,
                log_uri=_run_directory(text),
            )
        self._cache[key] = outcome
        return outcome

    def evaluate(
        self,
        spec: ExperimentSpec,
        candidate: HardwareCandidate,
        *,
        template: TemplateRecord | None = None,
        analytical: EvaluationResult | None = None,
    ) -> EvaluationResult:
        """Confirm a candidate by simulation, folding in the analytical metrics.

        `analytical` supplies cycles, area and power, which a single-module
        simulation cannot produce. Passing it is optional; without it those
        fields stay ``None`` rather than being invented.
        """
        if candidate.status is not Status.PASSED:
            return _skipped(
                candidate.error or "hardware candidate gate failed",
                ("hardware.status", "hardware.verified_template"),
            )

        bench = self.bench_for(template)
        if bench is None:
            name = template.template_id if template else candidate.template_id
            return _skipped(
                f"no golden testbench exists for template '{name}'",
                ("template.template_id",),
            )

        outcome = self.simulate(bench)

        evidence = [
            f"model=L2-rtl-simulation (Chisel 3.6 -> Verilator, {bench.top_module})",
            f"reference={bench.testbench}",
            f"mismatches={outcome.mismatches} across {outcome.checked} checked units",
            # An L2 label must not imply more than was simulated. One module
            # driven by golden vectors settles arithmetic, not layer throughput.
            "cycles/area/power are NOT simulated: they remain L1-analytical",
        ]
        if template is not None and template.provenance != "dynax-upstream":
            evidence.append(
                f"provenance={template.provenance}: {template.patch_note[:160]}"
            )
        if analytical is not None:
            evidence.extend(analytical.evidence)

        if outcome.error is not None:
            return EvaluationResult(
                status=Status.FAILED, fidelity="L2-rtl-simulation",
                functional_passed=False,
                cycles=None, throughput=None, pe_utilization=None,
                area=None, power=None, edp=None,
                wall_seconds=outcome.wall_seconds, cloud_cost_usd=0.0,
                log_uri=outcome.log_uri,
                evidence=tuple(evidence), error=outcome.error,
            )

        return EvaluationResult(
            # A functional mismatch is a failed evaluation, not a passed one
            # with a flag set: nothing downstream should treat its cycle count
            # as meaningful.
            status=Status.PASSED if outcome.passed else Status.FAILED,
            fidelity="L2-rtl-simulation",
            functional_passed=outcome.passed,
            cycles=analytical.cycles if analytical else None,
            throughput=analytical.throughput if analytical else None,
            pe_utilization=analytical.pe_utilization if analytical else None,
            area=analytical.area if analytical else None,
            power=analytical.power if analytical else None,
            edp=analytical.edp if analytical else None,
            wall_seconds=outcome.wall_seconds,
            cloud_cost_usd=0.0,
            log_uri=outcome.log_uri,
            evidence=tuple(evidence),
            error=None if outcome.passed
            else f"{outcome.mismatches} functional mismatches against {bench.testbench}",
        )


def _skipped(error: str, evidence: tuple[str, ...]) -> EvaluationResult:
    return EvaluationResult(
        status=Status.SKIPPED, fidelity="none", functional_passed=False,
        cycles=None, throughput=None, pe_utilization=None,
        area=None, power=None, edp=None,
        wall_seconds=0.0, cloud_cost_usd=0.0, log_uri="",
        evidence=evidence, error=error,
    )


def _run_directory(text: str) -> str:
    """Recover the job's output directory from its own first line."""
    match = re.search(r"\bout=(\S+)", text)
    return match.group(1) if match else ""
