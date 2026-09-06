"""The coupled software-hardware space the Compiler and µArch Agents share.

The proposal has these two agents "jointly explore the coupled software-hardware
space", which a pipeline cannot do: a schedule is only meaningful against the
array that runs it, and an array is only sized correctly against the schedule it
serves. Tile size is bounded by SRAM; parallelism is bounded by array rows; the
predict unit's width is dictated by the kernel's per-block budget.

So the constraints live here rather than inside either agent - a rule that spans
two layers belongs to neither - and the search proposes *pairs*.

The cost model is analytical and first-order. It exists because Verilator is not
built yet (plan stage 1), and it is labelled ``L1-analytical`` everywhere it
surfaces so no number from it is mistaken for simulation.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

from fast.agents.templates import (
    TemplateRegistry,
    array_area_units,
    required_col_select_bits,
    sram_area_units,
    topk_area_units,
)
from fast.schemas.models import (
    ArchSpecs,
    CompilerSchedule,
    HardwareCandidate,
    KernelProfile,
    KernelResult,
    Status,
)


@dataclass(frozen=True)
class CoDesignPoint:
    """One schedule paired with the hardware that would run it."""

    tile_q: int
    tile_k: int
    tile_d: int
    parallelism: int
    double_buffer: bool
    num_rows: int
    pe_per_row: int
    reg_width: int
    data_width: int
    sram_bytes: int
    queue_depth: int

    @property
    def mac_lanes(self) -> int:
        return self.num_rows * self.pe_per_row


@dataclass(frozen=True)
class CoDesignSpace:
    """What the joint search may vary. Small on purpose: every point is costed."""

    tile_q: tuple[int, ...] = (32, 64, 128)
    tile_k: tuple[int, ...] = (32, 64, 128)
    tile_d: tuple[int, ...] = (32, 64)
    parallelism: tuple[int, ...] = (2, 4, 8, 16)
    double_buffer: tuple[bool, ...] = (False, True)
    num_rows: tuple[int, ...] = (4, 8, 16, 32)
    pe_per_row: tuple[int, ...] = (4, 8, 16, 32)
    reg_width: tuple[int, ...] = (16, 32, 64)
    queue_depth: tuple[int, ...] = (0, 2, 4, 8, 16)

    def points(self, specs: ArchSpecs, sram_choices: tuple[int, ...] = (65536, 131072, 262144)):
        for tq in self.tile_q:
            for tk in self.tile_k:
                for td in self.tile_d:
                    for par in self.parallelism:
                        for rows in self.num_rows:
                            for cols in self.pe_per_row:
                                for regs in self.reg_width:
                                    for width in specs.data_widths:
                                        for sram in sram_choices:
                                            for queue in self.queue_depth:
                                                for buffered in self.double_buffer:
                                                    yield CoDesignPoint(
                                                        tile_q=tq, tile_k=tk, tile_d=td,
                                                        parallelism=par, double_buffer=buffered,
                                                        num_rows=rows, pe_per_row=cols,
                                                        reg_width=regs, data_width=width,
                                                        sram_bytes=sram, queue_depth=queue,
                                                    )


def working_set_bytes(point: CoDesignPoint) -> int:
    """Bytes a tile needs resident: one Q tile plus a K and a V tile."""
    per_element = point.data_width // 8
    tiles = point.tile_q + 2 * point.tile_k
    buffers = 2 if point.double_buffer else 1
    return tiles * point.tile_d * per_element * buffers


def violations(
    point: CoDesignPoint,
    kernel: KernelResult,
    specs: ArchSpecs,
    registry: TemplateRegistry | None = None,
    *,
    block_m: int = 64,
    kept_per_block: int = 16,
) -> tuple[str, ...]:
    """Every reason this pair could not be built or run as described.

    Checked here rather than in either agent because each rule ties a software
    choice to a hardware one.
    """
    problems: list[str] = []

    if point.parallelism > point.num_rows:
        problems.append(
            f"parallelism={point.parallelism} exceeds num_rows={point.num_rows}: "
            "the schedule asks for more independent row lanes than the array has"
        )
    if point.tile_k % point.reg_width != 0:
        problems.append(
            f"tile_k={point.tile_k} is not a multiple of regWidth={point.reg_width}: "
            "the K tile cannot be streamed through the register file without a partial pass"
        )
    needed = working_set_bytes(point)
    if needed > point.sram_bytes:
        problems.append(
            f"working set {needed} B exceeds sram_bytes={point.sram_bytes}"
            f"{' (double buffered)' if point.double_buffer else ''}"
        )
    if point.sram_bytes > specs.max_sram_bytes:
        problems.append(f"sram_bytes={point.sram_bytes} exceeds the budget {specs.max_sram_bytes}")
    if point.mac_lanes > specs.max_pe:
        problems.append(f"{point.mac_lanes} MAC lanes exceed the PE budget {specs.max_pe}")
    if point.data_width not in specs.data_widths:
        problems.append(f"data_width={point.data_width} is not among {specs.data_widths}")
    if kept_per_block > block_m:
        problems.append(f"kept_per_block={kept_per_block} exceeds the block width {block_m}")

    if registry is not None:
        array = registry.by_id("repe_array")
        if array is not None:
            problems.extend(array.admits(
                numRows=point.num_rows, peCountPerRow=point.pe_per_row,
                regWidth=point.reg_width, bits=point.data_width,
                colSelectBits=required_col_select_bits(block_m),
            ))
        topk = registry.by_id("topk")
        if topk is not None:
            problems.extend(topk.admits(m=block_m, n=kept_per_block, bits=point.data_width))

    area = area_units(point, block_m, kept_per_block)
    if area > specs.max_area_um2:
        problems.append(
            f"area {area:,.0f} um^2 exceeds the budget {specs.max_area_um2:,.0f} um^2"
        )
    return tuple(problems)


def area_units(point: CoDesignPoint, block_m: int, kept_per_block: int) -> float:
    """一个协同设计点的总面积，um^2（Nangate45）。

    三项里两项经过 yosys 实测标定（TopK、RePEArray），SRAM 那项是估计——
    yosys 没有存储器宏编译器，实测值反映的是综合流程缺一环。详见
    `fast/agents/templates.py` 的面积模型一节。
    """
    return (
        array_area_units(point.num_rows, point.pe_per_row, point.data_width, point.reg_width)
        + topk_area_units(block_m, kept_per_block, point.data_width)
        + sram_area_units(point.sram_bytes)
    )


def pe_utilisation(profile: KernelProfile | None, queue_depth: int) -> float:
    """How much of the array stays busy given the kernel's row-length spread.

    With dynamic sparsity every query row keeps a different number of values, so
    a lane handed a long row runs while its neighbours idle. A work queue lets a
    lane run ahead, amortising the spread.

    First-order model: utilisation = 1 / (1 + (imbalance - 1) / (1 + queue)).
    At queue 0 it degrades to 1/imbalance - the busiest lane sets the pace - and
    it approaches 1 as the queue grows. It is a model, not a measurement; the
    Verilator backend replaces it in stage 2.
    """
    if profile is None:
        return 0.75  # no profile: assume nothing about balance, and say so upstream
    imbalance = max(1.0, profile.load_imbalance)
    return 1.0 / (1.0 + (imbalance - 1.0) / (1.0 + queue_depth))


def estimate(
    point: CoDesignPoint,
    kernel: KernelResult,
    sequence_length: int,
    *,
    block_m: int = 64,
    kept_per_block: int = 16,
) -> dict[str, float]:
    """First-order cycles, traffic, area and EDP for one co-design point."""
    retained = max(0.0, 1.0 - kernel.actual_sparsity)
    dense_macs = sequence_length * sequence_length * point.tile_d
    sparse_macs = dense_macs * retained

    utilisation = pe_utilisation(kernel.profile, point.queue_depth)
    lanes = max(1, point.mac_lanes)
    cycles = sparse_macs / (lanes * max(utilisation, 1e-3))

    # Only occupied blocks are fetched; the rest are skipped whole.
    per_element = point.data_width // 8
    dram_bytes = kernel.block_occupancy * sequence_length * sequence_length * per_element

    area = area_units(point, block_m, kept_per_block)
    # Power tracks the lanes that actually switch, plus a memory term.
    power = lanes * utilisation * (point.data_width ** 2) * 1e-4 + point.sram_bytes * 1e-6
    energy = power * cycles
    return {
        "cycles": cycles,
        "pe_utilization": utilisation,
        "throughput": sequence_length / cycles if cycles else 0.0,
        "dram_bytes": dram_bytes,
        "area": area,
        "power": power,
        "edp": energy * cycles,
    }


def to_schedule(point: CoDesignPoint, rationale: tuple[str, ...], utilisation: float) -> CompilerSchedule:
    return CompilerSchedule(
        status=Status.PASSED,
        tile_q=point.tile_q,
        tile_k=point.tile_k,
        tile_d=point.tile_d,
        loop_order=("q", "k", "d"),
        data_layout="blocked-qkd-double" if point.double_buffer else "blocked-qkd",
        parallelism=point.parallelism,
        predicted_utilization=utilisation,
        predicted_bytes=working_set_bytes(point),
        rationale=rationale,
    )


def to_hardware(
    point: CoDesignPoint,
    template,
    *,
    block_m: int,
    kept_per_block: int,
    binary_point: int = 8,
) -> HardwareCandidate:
    """Instantiate the composed candidate, carrying the real module parameters."""
    return HardwareCandidate(
        status=Status.PASSED if template.verified else Status.FAILED,
        template_id=template.template_id,
        template_digest=template.digest,
        verified_template=template.verified,
        pe_rows=point.num_rows,
        pe_cols=point.pe_per_row,
        queue_depth=point.queue_depth,
        sram_bytes=point.sram_bytes,
        data_width=point.data_width,
        manifest_uri=template.manifest_uri,
        topk_m=block_m,
        topk_n=kept_per_block,
        binary_point=binary_point,
        reg_width=point.reg_width,
        col_select_bits=required_col_select_bits(block_m),
        area_units=area_units(point, block_m, kept_per_block),
        error=None if template.verified else (
            f"{template.template_id} has not passed the verification gate: {template.blocking_issue}"
        ),
    )
