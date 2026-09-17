"""让 LLM 花 Compiler Agent（planner）的搜索预算。

## 切法和 Kernel Agent 完全一样，这是刻意的

    LLM        只说下一步试哪几个设计点
    CoOptimizer 独占可行性、打分、frontier

如果 LLM 能碰可行性判据或打分，规则版和 LLM 版就不是在同样的条件下比了——
它可能靠放宽约束来「赢」。锁住那三样，两种 proposer 就**只在「会不会选」
这一个维度上**有差别，对照实验才成立。

## 和 Kernel proposer 的一个关键差别：空间不可枚举

Kernel 的空间是 23 个标签，非法提议在测量前被拒，幻觉零成本。
协同设计空间是 11 个维度的笛卡尔积——**枚举不出来**，所以校验换成
「每个字段必须落在 `CoDesignSpace` 允许的取值集合里」，越界的字段被拒并
记进 `rejected`，理由说明是哪个字段。

## 提示里必须带实测的换算率

不给换算率，模型答不出「多 2 个 bank 值得多 3 万 um^2 吗」。这些数字全部
来自 Nangate45 实测，出处见 `hardware/README.md`。
"""

from __future__ import annotations

import json
import re

from fast.agents.codesign import CoDesignPoint, CoDesignSpace
from fast.agents.templates import ARRAY_CRITICAL_PATH_NS
from fast.schemas.models import ArchSpecs, KernelResult

# 和 `cooptimizer.SRAM_CHOICES` 一致。三档对应真实可拼出的宏组合。
SRAM_CHOICES: tuple[int, ...] = (65_536, 131_072, 262_144)


PLAN_PROMPT = """You are the Compiler Agent (the planner) in a hardware/software \
co-design loop for dynamic sparse attention. You choose which complete design \
points to evaluate next. A design point fixes BOTH the software schedule and the \
hardware parameters, because they are coupled: the array shape limits parallelism, \
SRAM capacity limits tile size, and queue depth and bank count set both the cycle \
count and the clock.

Explore the latency-energy Pareto front, minimising BOTH seconds per task and
joules per task. Energy = power_mW * 1e-3 * seconds; efficiency = tasks/J.
Keep both fast/high-energy and slow/low-energy trade-offs. Area and frequency
are constraints. Do not use EDP or area as substitutes for these two axes.
The current energy model is partial; model results are not independent evidence.

## The workload you are designing for

sparse method: {method}
measured sparsity: {sparsity:.4f}
block occupancy: {occupancy:.4f}
tile-local load imbalance (32-row tile): {imbalance}

## Budgets you must design inside

area <= {max_area:,.0f} um^2
clock >= {target_mhz:.0f} MHz
PE count <= {max_pe}
SRAM <= {max_sram} bytes
{power_line}

## Measured trade-offs (Nangate45, yosys + OpenSTA + Verilator)

These are measurements, not estimates. Use them; do not re-derive them.

Execution array critical path: {array_ns} ns ({array_mhz:.0f} MHz). That is the
ceiling — no design runs faster than this.

Work queue (queue_depth) buys PE utilisation and costs BOTH area and clock:
  depth  area um^2   critical path   utilisation (xm)
      0      8,899      2.273 ns             0.708
      2     26,392      2.528 ns             0.832
      4     42,826      2.760 ns             0.864
      8     74,421      3.140 ns             0.867   <- slower than depth 0 overall
     16    134,870      (untrusted)          0.867
Utilisation saturates below 1. Past depth 4 you pay clock for nothing.

Divider (divider_stages) sets a floor on the clock and costs area:
  stages  area um^2   critical path
       0      2,081     14.780 ns   <- upstream DynaX; 68 MHz, unusable
       1      2,887     10.895 ns
       4      4,160      3.269 ns
       8      5,412      1.980 ns   <- below the array, no longer the bottleneck
      12      6,368      1.546 ns   <- deeper than the array: pure cost

Bank count sets the memory stall factor. It depends on the sparse method,
because bank conflicts depend on the index DISTRIBUTION, not the count:
  banks     xm     nm    topk  sanger
      4   3.05   2.17    2.69    2.25
      8   2.14   1.19    1.79    1.28
     16   1.53   1.08    1.34    1.08
     32   1.13   1.01    1.19    1.07
Bank logic area is nearly free (about 10,000 um^2 across the whole 4->32 range).

SRAM is priced from real macros: about 4.0-5.4 um^2 per byte.
  64 KB ->   262,497 um^2
 128 KB ->   524,995 um^2
 256 KB -> 1,049,989 um^2   <- larger than both arrays combined (~740,000)

## The legal values for each field

{space}

## What has been evaluated so far

{history}

Choose {count} design points that are NOT already evaluated.

Reply with ONLY a JSON array, no prose, no code fence. Each element:
  {{"tile_q": <int>, "tile_k": <int>, "tile_d": <int>, "parallelism": <int>,
    "double_buffer": <true|false>, "num_rows": <int>, "pe_per_row": <int>,
    "reg_width": <int>, "data_width": <int>, "sram_bytes": <int>,
    "queue_depth": <int>, "divider_stages": <int>, "bank_count": <int>,
    "rationale": "<cites a specific number from the tables above>"}}

Every field must come from the legal values listed. Every rationale must cite a
measured number or state plainly that the region is unexplored."""


class LLMPlanProposer:
    """Lets a language model spend the planner's search budget, under the same gate."""

    def __init__(self, llm, *, model_name: str = "llm", fallback=None,
                 calibration_hints: bool = True):
        self.llm = llm
        self.name = f"llm-plan:{model_name}"
        self.calibration_hints = calibration_hints
        if fallback is None:
            from fast.agents.cooptimizer import GuidedProposer

            fallback = GuidedProposer()
        self.fallback = fallback
        self.rejected: list[str] = []
        self.llm_batches = 0
        self.fallback_batches = 0
        self.calls: list[dict] = []

    def propose(
        self,
        kernel: KernelResult,
        specs: ArchSpecs,
        space: CoDesignSpace,
        history: tuple,
        count: int,
    ) -> tuple[CoDesignPoint, ...]:
        prompt = self._prompt(kernel, specs, space, history, count)
        try:
            reply = self.llm.prompt(prompt)
            text = reply.result if hasattr(reply, "result") else str(reply)
            success = getattr(reply, "success", True)
            self.calls.append({"prompt": prompt, "response": text, "success": success})
        except Exception as exc:  # a proposer outage must not end the search
            self.calls.append({"prompt": prompt, "success": False,
                               "error": f"{type(exc).__name__}: {exc}"})
            self.rejected.append(f"llm call failed: {type(exc).__name__}: {exc}")
            self.fallback_batches += 1
            return self.fallback.propose(kernel, specs, space, history, count)

        if not success:
            self.rejected.append(f"llm returned failure: {getattr(reply, 'stderr', '')[:200]}")
            self.fallback_batches += 1
            return self.fallback.propose(kernel, specs, space, history, count)

        points = self._parse(text, space, specs, history, count)
        if not points:
            self.rejected.append(f"llm proposed nothing usable; falling back to {type(self.fallback).__name__}")
            self.fallback_batches += 1
            return self.fallback.propose(kernel, specs, space, history, count)
        self.llm_batches += 1
        return points

    # -- prompt ------------------------------------------------------------

    def _prompt(self, kernel, specs, space, history, count) -> str:
        profile = kernel.profile
        imbalance = (
            f"{profile.tile_imbalance_for(32):.3f}" if profile is not None
            else "not measured (the kernel reported no profile)"
        )
        power_line = (
            f"power <= {specs.max_power_mw:.0f} mW" if specs.max_power_mw is not None
            else "power: no budget set"
        )
        template = PLAN_PROMPT
        if not self.calibration_hints:
            start = template.index("## Measured trade-offs")
            end = template.index("## The legal values")
            template = template[:start] + (
                "No default design or pre-ranked calibration table is supplied. "
                "Explore from the legal domains and use evaluator feedback.\n\n"
            ) + template[end:]
        return template.format(
            method=kernel.sparse_method,
            sparsity=kernel.actual_sparsity,
            occupancy=kernel.block_occupancy,
            imbalance=imbalance,
            max_area=specs.max_area_um2,
            target_mhz=specs.target_mhz,
            max_pe=specs.max_pe,
            max_sram=specs.max_sram_bytes,
            power_line=power_line,
            array_ns=ARRAY_CRITICAL_PATH_NS,
            array_mhz=1000.0 / ARRAY_CRITICAL_PATH_NS,
            space=_space_table(space, specs),
            history=_history_table(history),
            count=count,
        )

    # -- parsing and validation -------------------------------------------

    def _parse(self, text, space, specs, history, count) -> tuple[CoDesignPoint, ...]:
        payload = _extract_json_array(text)
        if payload is None:
            self.rejected.append(f"reply was not a JSON array: {text.strip()[:160]}")
            return ()

        seen = {_key(item.point) for item in history}
        picked: list[CoDesignPoint] = []
        for entry in payload:
            if not isinstance(entry, dict):
                self.rejected.append(f"entry is not an object: {str(entry)[:120]}")
                continue
            point = self._as_point(entry, space, specs)
            if point is None:
                continue
            if _key(point) in seen:
                self.rejected.append(f"{_short(point)}: already evaluated")
                continue
            seen.add(_key(point))
            picked.append(point)
            if len(picked) == count:
                break
        return tuple(picked)

    def _as_point(self, entry: dict, space: CoDesignSpace,
                  specs: ArchSpecs) -> CoDesignPoint | None:
        """把一条 JSON 变成设计点，**逐字段对着允许集合校验**。

        协同设计空间枚举不出来（11 个维度的笛卡尔积），所以校验不能像
        Kernel 那样查一张标签表。逐字段校验的好处是拒绝理由能指到具体字段，
        模型下一轮能改对地方；只说「非法」它只会重猜。
        """
        fields = {
            "tile_q": space.tile_q, "tile_k": space.tile_k, "tile_d": space.tile_d,
            "parallelism": space.parallelism, "num_rows": space.num_rows,
            "pe_per_row": space.pe_per_row, "reg_width": space.reg_width,
            # 这两个不在 CoDesignSpace 里：位宽由 ArchSpecs 限定（它是目标
            # 工艺的性质，不是搜索维度），SRAM 档位由可用的宏尺寸决定。
            "data_width": specs.data_widths, "sram_bytes": space.sram_bytes,
            "queue_depth": space.queue_depth, "divider_stages": space.divider_stages,
            "bank_count": space.bank_count,
        }
        values: dict[str, object] = {}
        for name, allowed in fields.items():
            if name not in entry:
                self.rejected.append(f"missing field {name}")
                return None
            try:
                value = int(entry[name])
            except (TypeError, ValueError):
                self.rejected.append(f"{name}={entry[name]!r} is not an integer")
                return None
            if value not in allowed:
                self.rejected.append(
                    f"{name}={value} is not one of {sorted(allowed)}"
                )
                return None
            values[name] = value

        double = entry.get("double_buffer")
        if not isinstance(double, bool):
            self.rejected.append(f"double_buffer={double!r} is not a boolean")
            return None
        if double not in space.double_buffer:
            self.rejected.append(f"double_buffer={double} is not allowed by the space")
            return None
        return CoDesignPoint(double_buffer=double, **values)  # type: ignore[arg-type]


def _space_table(space: CoDesignSpace, specs: ArchSpecs) -> str:
    rows = []
    for name in ("tile_q", "tile_k", "tile_d", "parallelism", "double_buffer",
                 "num_rows", "pe_per_row", "reg_width", "queue_depth",
                 "divider_stages", "bank_count"):
        rows.append(f"  {name:<16s} {list(getattr(space, name))}")
    rows.append(f"  {'data_width':<16s} {list(specs.data_widths)}")
    rows.append(f"  {'sram_bytes':<16s} {list(space.sram_bytes)}")
    return "\n".join(rows)


def _history_table(history: tuple) -> str:
    if not history:
        return "  (nothing evaluated yet)"
    rows = ["  point                                      feasible  cycles      area um^2   MHz"]
    for item in history[-12:]:
        point, metrics = item.point, item.metrics
        if not metrics:
            rows.append(f"  {_short(point)} evaluated; feedback withheld for ablation")
            continue
        state = "yes" if item.feasible else f"NO: {item.violations[0][:40]}" if item.violations else "NO"
        rows.append(
            f"  {_short(point):<42s} {state:<9s} {metrics['cycles']:>10,.0f}"
            f"  {metrics['area']:>10,.0f}  {metrics['max_frequency_mhz']:>4.0f}"
            f" latency_s={metrics.get('seconds')} energy_J={metrics.get('energy_j')}"
        )
    return "\n".join(rows)


def _short(point: CoDesignPoint) -> str:
    return (
        f"{point.num_rows}x{point.pe_per_row} rw{point.reg_width} "
        f"q{point.queue_depth} d{point.divider_stages} b{point.bank_count} "
        f"s{point.sram_bytes // 1024}K t{point.tile_q}/{point.tile_k}/{point.tile_d}"
    )


def _key(point: CoDesignPoint) -> tuple:
    return tuple(sorted(point.__dict__.items()))


def _extract_json_array(text: str):
    """Pull the JSON array out of a reply that may be fenced or prefaced.

    要求严格（prompt 说 ONLY a JSON array），解析宽容——模型偶尔加围栏或前言
    是最常见的偏差，为此丢掉一整轮提议不划算。
    """
    fenced = re.search(r"```(?:json)?\s*(.+?)```", text, re.S)
    if fenced:
        text = fenced.group(1)
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end <= start:
        return None
    try:
        payload = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, list) else None
