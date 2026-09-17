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

from dataclasses import dataclass, field, replace
import json
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


@dataclass(frozen=True)
class PlanBench:
    """按计划的尺寸验证**整个** AttentionTile，而不是一个固定的小模板。

    ## 为什么固定小 bench 不够

    模板表里 `repe_array` 指向 `RePEArray_T`——4 行 x 2 PE。所以
    `functional_passed=True` 的意思是「**RePEArray 模板在 4x2 下正确**」，
    **不是**「规划出的 32x4 设计能跑」。归因拿这个当证据，会把一个从没被
    验证过的设计当成已验证的。

    这条路径验的是 planner 真正规划的那个尺寸：Chisel 的 `PLAN:` 目标造出
    完整的 tile，`tb_attention_tile.cpp` 拿真实 Q/K/V 和 PyTorch 的稀疏
    注意力逐维比。

    ## 它依赖一份形状匹配的抓取

    金标准是 `capture_attention_tile.py` 抓的真实 Q/K/V。抓取的形状必须和
    计划一致——不一致时**不要退而求其次找一份别的**：这一轮为此查错两轮，
    两次都表现为「已验证的路径突然全挂」，两次都不是被测对象的问题。
    找不到就明说验不了，然后退回模板 bench 并声明它验的是什么。
    """

    spec: str            # Elaborate 的 PLAN: 串
    tile_json: Path      # 形状匹配的抓取
    tile_q: int
    tile_k: int
    head_dim: int
    kept: int
    pe: int

    @property
    def passes(self) -> int:
        return -(-self.kept // max(self.pe, 1))
    #: 抓取自报的算法语义与内容摘要（`identity`），以及它来自哪个模型/层
    #: （`source`）。**形状匹配不能证明算法语义匹配**，所以这两块要一路
    #: 带到证据里，让读的人自己判断这次 L2 覆盖了什么。
    identity: dict = field(default_factory=dict)
    source: dict = field(default_factory=dict)


def plan_bench(plan, *, head_dim: int, capture_root: Path):
    """给一份计划找形状匹配的抓取，凑出一个 PlanBench。找不到就返回 None。"""
    from fast.agents.uarch import elaborate_spec

    if plan is None or plan.status is not Status.PASSED:
        return None
    candidates = sorted(
        Path(capture_root).glob("tile_*/tile.json"),
        key=lambda item: item.stat().st_mtime, reverse=True,
    )
    for path in candidates:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            kept = len(payload["expected_kept_idx"][0])
            rows = len(payload["expected_kept_idx"])
            dim = len(payload["q_ticks"][0])
            # **tile_k 也要对上。** 原来它是从计划取 `plan.block_m`，抓取里
            # 的那个值根本没参与匹配——于是一份 tile_k=32 的抓取能被用在
            # block_m=64 的计划上，而 testbench 按 kTileK 读 K/V 矩阵。
            tile_k = len(payload["k_ticks"])
        except (OSError, KeyError, ValueError, IndexError):
            continue
        # 四个维度都要对上。只对 kept 会让一份 tileQ 不同的抓取被当成匹配，
        # 而 testbench 是按 kTileQ 读矩阵的——读出来的是另一个形状的数。
        shape_matches = (
            kept == plan.kept_per_block and rows == plan.num_rows
            and dim == head_dim and tile_k == plan.block_m
        )
        if not shape_matches:
            continue
        return PlanBench(
            spec=elaborate_spec(plan, head_dim=head_dim),
            tile_json=path, tile_q=plan.num_rows, tile_k=tile_k,
            head_dim=head_dim, kept=plan.kept_per_block, pe=plan.pe_per_row,
            identity=payload.get("identity") or {},
            source=payload.get("source") or {},
        )
    return None


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
    # 抓取存放目录。给了就优先验**被规划的尺寸**而不是固定的小模板 bench。
    capture_root: Path | None = None
    # 模型的 head 维度。它是工作负载的性质不是设计的自由参数，所以必须显式
    # 给——传错会让匹配挑中一份形状不同的抓取。
    head_dim: int = 8
    launcher: tuple[str, ...] = ("bash",)
    benches: dict[str, TemplateBench] = field(
        default_factory=lambda: dict(DEFAULT_BENCHES)
    )
    timeout_seconds: int = 3600
    env: dict[str, str] | None = None
    # (template_id, top_module) -> outcome. Elaboration is deterministic and the
    # golden vectors are seeded, so a repeat cannot differ.
    #: 计划级 L2 的结果缓存，键含 RTL 指纹（见 `_evaluate_plan`）。
    _plan_cache: dict[tuple[str, str, str], EvaluationResult] = field(
        default_factory=dict, repr=False, compare=False
    )
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
        plan=None,
        kernel=None,
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

        # 优先验被规划的那个尺寸。
        planned = (
            plan_bench(plan, head_dim=self.head_dim, capture_root=self.capture_root)
            if self.capture_root is not None else None
        )
        if planned is not None:
            return self._evaluate_plan(planned, analytical, template)

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
            # **说清楚验的是什么尺寸。** 模板 bench 是 4x2 之类的小实例；
            # 把它当成「规划出的 32x4 设计已验证」，就是把一个从没被验证过
            # 的设计当成已验证的。
            f"verified_scope={bench.elaborate_target} (a fixed small instance), "
            f"NOT the planned design",
        ]
        if plan is not None and getattr(plan, "status", None) is Status.PASSED:
            evidence.append(
                f"no shape-matched capture for the planned "
                f"{plan.num_rows}x{plan.pe_per_row} kept={plan.kept_per_block} design; "
                f"run capture_attention_tile.py at that shape to reach L2 on it"
            )
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



    def _source_digest(self) -> str:
        """全部 Chisel 源文件的哈希。

        µArch 的变异改的是这些文件——尺寸规格不变而设计变了，所以它必须进
        缓存键。读不到就返回一个每次都不同的值，**宁可不命中缓存也不要误命中**。
        """
        import hashlib
        import uuid

        root = self.repo_root / "FAST" / "hardware" / "chisel" / "src"
        try:
            digest = hashlib.sha256()
            for path in sorted(root.rglob("*.scala")):
                digest.update(path.name.encode("utf-8"))
                digest.update(path.read_bytes())
            return digest.hexdigest()[:16]
        except OSError:
            return uuid.uuid4().hex[:16]

    def _evaluate_plan(self, bench, analytical, template) -> EvaluationResult:
        """跑被规划尺寸的整 tile 验证。

        走 `slurm/rtl/fast_attention_tile.slurm`——那个脚本已经做了全部的事
        （PLAN elaborate、按尺寸生成端口、形状匹配抓取、真实 Q/K/V 比对）。
        在这里重写一份只会分叉，而分叉的后果是「适配器说过了」而「脚本说没过」。
        """
        # **同一个设计不重建。** 实测一次 7 轮的运行里 6 轮有 4 轮用的是完全
        # 相同的计划，而每一轮都重新 elaborate + verilate + 编译 + 仿真一遍
        # ——那是整跑 30 分钟里的大头。
        #
        # 缓存键里**必须带 RTL 指纹**：µArch 的变异会改 Chisel 源文件，尺寸
        # 规格一个字没变但设计变了。只按规格缓存的话，一次成功的变异会被上
        # 一轮的结果盖住，而且看不出来——正是这个项目反复撞到的那种静默错误。
        key = (bench.spec, str(bench.tile_json), self._source_digest())
        if key in self._plan_cache:
            cached = self._plan_cache[key]
            return replace(cached, evidence=tuple(cached.evidence) + ("cache=hit",))

        script = self.repo_root / "slurm" / "rtl" / "fast_attention_tile.slurm"
        environment = dict(os.environ if self.env is None else self.env)
        environment.update(
            TILE_Q=str(bench.tile_q), TILE_K=str(bench.tile_k),
            TILE_HEADDIM=str(bench.head_dim), TILE_KEPT=str(bench.kept),
            TILE_PE=str(bench.pe), TILE_JSON=str(bench.tile_json),
        )
        started = time.time()
        try:
            completed = subprocess.run(
                [*self.launcher, str(script)], capture_output=True, text=True,
                timeout=self.timeout_seconds, env=environment, cwd=str(self.repo_root),
            )
            text = f"{completed.stdout}\n{completed.stderr}"
        except subprocess.TimeoutExpired:
            text = f"timed out after {self.timeout_seconds}s"

        verdict = re.search(r"^(PASSED|FAILED): (\d+)/(\d+)", text, re.M)
        passed = bool(verdict and verdict.group(1) == "PASSED")
        checked = int(verdict.group(3)) if verdict else 0
        matched = int(verdict.group(2)) if verdict else 0

        evidence = [
            f"model=L2-rtl-simulation of the PLANNED design ({bench.spec})",
            f"reference=tb_attention_tile.cpp against real TinyLlama Q/K/V "
            f"({bench.tile_json.name})",
            f"{matched}/{checked} output dimensions within tolerance",
            # 容差随趟数放宽是有依据的：每趟读一次 row_sum 各截断一次。
            #
            # **不再是单侧的。** 上游 `repe.scala` 的乘积截断是 floor，误差
            # 恒为负，那时「硬件永不偏大」是判据的核心；打上舍入补丁（缺陷 6）
            # 之后误差双侧，实测 495 偏小 : 583 偏大。这行字串曾经还写着
            # one-sided——描述和判据脱节，读的人会以为方向还在被检查。
            f"passes={bench.passes}, tolerance={bench.passes} tick(s), two-sided",
            "cycles/area/power are NOT simulated: they remain L1-analytical",
            f"verified_scope=the planned {bench.tile_q}x{bench.pe} "
            f"kept={bench.kept} design, end to end",
            # **说清楚这次 L2 到底证明了什么。**
            #
            # testbench 把抓取里的 `expected_kept_idx` **驱动进硬件**，再比
            # 输出。所以它验的是「给定保留列之后，执行通路算得对不对」——
            # 算法无关。而那些列是参照用它自己的选择算法挑的（当前抓取用的
            # 是固定 top-n），硬件**自己的**选择语义没有被验证：预测器重合度
            # 是同一份输出里的一个**度量**，不是判据。
            #
            # 计划的算法和参照的语义不同时（比如 xm:32:4:64 对 topk），这一点
            # 尤其要说——形状匹配不能证明语义匹配。
            f"reference_semantics={bench.identity.get('reference_semantics', 'not recorded')}"
            f" (verifies {bench.identity.get('verifies', 'unknown scope')};"
            f" does NOT verify {bench.identity.get('does_not_verify', 'unknown')})",
            f"capture_identity={bench.identity.get('content_sha256', 'not recorded')}"
            f" from {bench.source.get('model', 'unknown model')}"
            f" layer {bench.source.get('layer', '?')} head {bench.source.get('head', '?')}",
        ]
        if template is not None and getattr(template, "provenance", "") not in ("", "dynax-upstream"):
            evidence.append(f"provenance={template.provenance}")

        result = EvaluationResult(
            status=Status.PASSED,
            fidelity="L2-rtl-simulation",
            functional_passed=passed,
            cycles=analytical.cycles if analytical else None,
            throughput=analytical.throughput if analytical else None,
            pe_utilization=analytical.pe_utilization if analytical else None,
            area=analytical.area if analytical else None,
            power=analytical.power if analytical else None,
            edp=analytical.edp if analytical else None,
            wall_seconds=round(time.time() - started, 3),
            cloud_cost_usd=0.0,
            log_uri=_run_directory(text),
            evidence=tuple(evidence),
            error=None if passed else f"{checked - matched} dimension(s) outside tolerance",
        )
        self._plan_cache[key] = result
        return result

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
