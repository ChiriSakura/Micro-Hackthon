"""执行单元（RePEA）与 SRAM 的参照模型。

RePE 的控制排程源码和论文都没写，是从数据通路反推的——`RePEModel` 的
docstring 就是这份推导。往上 `RePERowModel` 加两处不同位置的延迟，
`RePEArrayModel` 加跨行的脉动斜移。

SRAM 的参照刻意**不是**这份 Verilog 的镜像，而是「一个正确的分 bank
同步读 SRAM 应该怎样」——正因如此它才能发现 bank 选择器的时序缺陷。
"""

from __future__ import annotations

import torch

from golden.exp_unit import exp_unit_reference
from golden.fixedpoint import fp_mul, wrap


def sram_cases(bank_count: int, bank_depth: int, bank_width: int, seed: int) -> list[dict]:
    """Per-cycle (addr, dataIn, writeEnable) stimulus with the expected read.

    The reference is what a banked synchronous-read SRAM *should* do -- a read
    issued at cycle t appears at t+1 -- not what this Verilog does. That is the
    point: SRAM.scala selects the output bank with the *current* bankAddr while
    SyncReadMem returns data for the *previous* address, so the two disagree the
    moment consecutive reads cross a bank boundary. `single_bank` and
    `bank_switch` differ only in that, which is what makes the pair decisive.

    expected_idx carries a per-cycle check flag: a cycle following a write has
    no defined read data (read enable is tied to !writeEnable), so it is skipped.
    """
    generator = torch.Generator().manual_seed(seed)
    offset_bits = (bank_depth - 1).bit_length()
    mask = (1 << bank_width) - 1

    def address(bank: int, offset: int) -> int:
        return (bank << offset_bits) | offset

    def payload(count: int) -> list[int]:
        # Kept under 2^62 so the golden file stays parseable as a signed long.
        raw = torch.randint(0, 1 << 30, (count, 2), generator=generator).tolist()
        return [((hi << 30) | lo) & mask for hi, lo in raw]

    values = payload(64)
    plans: list[tuple[str, list[tuple[int, int, int]]]] = []

    # Fill four offsets in bank 0, then read them back in order.
    single = [(address(0, i), values[i], 1) for i in range(4)]
    single += [(address(0, i), 0, 0) for i in range(4)] + [(0, 0, 0)]
    plans.append(("single_bank", single))

    # Same fill, one offset per bank, then read them back in order. Every read
    # after the first crosses a bank boundary.
    switch = [(address(b, 3), values[8 + b], 1) for b in range(bank_count)]
    switch += [(address(b, 3), 0, 0) for b in range(bank_count)] + [(0, 0, 0)]
    plans.append(("bank_switch", switch))

    # Read the same address repeatedly: no boundary crossing, so this must pass
    # even if bank selection is mistimed. It separates "the memory is wrong"
    # from "the bank multiplexer is mistimed".
    repeat = [(address(2, 7), values[16], 1)] + [(address(2, 7), 0, 0)] * 4
    plans.append(("repeat_read", repeat))

    # Interleaved writes and reads inside one bank.
    mixed = []
    for i in range(6):
        mixed.append((address(1, i), values[24 + i], 1))
        mixed.append((address(1, i), 0, 0))
        mixed.append((address(1, i), 0, 0))
    plans.append(("write_read_interleaved", mixed))

    cases = []
    for name, plan in plans:
        memory: dict[int, int] = {}
        inputs: list[int] = []
        expected: list[int] = []
        checks: list[int] = []
        previous: tuple[int, int, int] | None = None
        for addr, data, write_enable in plan:
            inputs.extend((addr, data, write_enable))
            if previous is not None and previous[2] == 0 and previous[0] in memory:
                expected.append(memory[previous[0]])
                checks.append(1)
            else:
                expected.append(0)
                checks.append(0)
            if write_enable:
                memory[addr] = data
            previous = (addr, data, write_enable)
        cases.append({"name": name, "input_ticks": inputs,
                      "expected_value_ticks": expected, "expected_idx": checks})
    return cases


# repe.scala: Enum(4) for the accumulator, Enum(2) for the exponential.
ACC_CLEAR, ACC_IDLE, ACC_ACCUMULATE, ACC_MOVE_OUT = 0, 1, 2, 3
EXP_IDLE, EXP_COMPUTE = 0, 1


class RePEModel:
    """Cycle-accurate mirror of one RePE.

    The control schedule is not documented anywhere -- neither the DynaX sources
    nor the paper state it -- so it is derived from what the datapath makes
    possible, and this model is the derivation written down:

      acc_clear       acc := 0
      acc_accumulate  a = q_in, b = reg_cols[sel_col], acc += a*b
                      -> the QK^T dot product for the key this PE selected
      exp_compute     score_exp := exp(acc), and io.out = score_exp
                      -> RePERow's adder over io.out is then the softmax
                         denominator, sum_j exp(s_j)
      acc_move_out    a = score_exp, acc := score_exp * b, io.out = the PREVIOUS
                      acc -> drains one AV product per cycle while loading the
                      next, so the row adder yields sum_j exp(s_j) * v_j[k]

    io.out is dual-purpose, which is the part worth stating: it carries
    score_exp in every state except acc_move_out, where it carries the
    accumulator. That single overload is what lets one adder tree produce both
    the softmax denominator and the AV numerator.
    """

    def __init__(self, bits: int, point: int, reg_width: int,
                 frac: int = 4, guard: int = 4) -> None:
        self.bits, self.point, self.reg_width = bits, point, reg_width
        self.frac, self.guard = frac, guard
        # `acc` and `score_exp` are Reg, not RegInit: repe.scala gives them no
        # reset value, so they start at whatever the simulator zeroes them to.
        self.acc = 0
        self.score_exp = 0

    def step(self, q_in: int, reg_cols: list[int], sel_col: int,
             acc_ctrl: int, exp_ctrl: int) -> int:
        columns = list(reg_cols) + [0]  # col_vec(regWidth) is the zero escape
        b = columns[sel_col] if sel_col <= self.reg_width else 0
        a = self.score_exp if acc_ctrl == ACC_MOVE_OUT else q_in
        mul = fp_mul(a, b, self.bits, self.point)

        out = self.acc if acc_ctrl == ACC_MOVE_OUT else self.score_exp

        if acc_ctrl == ACC_CLEAR:
            next_acc = 0
        elif acc_ctrl == ACC_ACCUMULATE:
            next_acc = wrap(self.acc + mul, self.bits)
        elif acc_ctrl == ACC_MOVE_OUT:
            next_acc = mul
        else:
            next_acc = self.acc

        next_score = self.score_exp
        if exp_ctrl == EXP_COMPUTE:
            next_score = exp_unit_reference(
                self.acc, self.bits, self.point, self.frac, self.guard
            )
            # exp_unit_reference returns the raw pattern; reinterpret as signed
            # so later multiplies see the same value the RTL's FixedPoint does.
            next_score = wrap(next_score, self.bits)

        self.acc, self.score_exp = next_acc, next_score
        return out


def repe_cases(bits: int, point: int, reg_width: int, seed: int) -> list[dict]:
    """Schedules that exercise each control state and each phase transition."""
    scale = 1 << point
    generator = torch.Generator().manual_seed(seed)

    def randcols() -> list[int]:
        return torch.randint(-scale, scale, (reg_width,), generator=generator).tolist()

    zeros = [0] * reg_width

    def attention(name: str, keys: list[list[int]], queries: list[int],
                  sel: int, values: list[list[int]], value_sel: int) -> tuple:
        """clear -> accumulate over the head dim -> exp -> stream AV products."""
        plan = [(0, 0, zeros, ACC_CLEAR, EXP_IDLE)]
        for q, column in zip(queries, keys):
            plan.append((q, sel, column, ACC_ACCUMULATE, EXP_IDLE))
        plan.append((0, 0, zeros, ACC_IDLE, EXP_COMPUTE))
        plan.append((0, 0, zeros, ACC_IDLE, EXP_IDLE))
        for column in values:
            plan.append((0, value_sel, column, ACC_MOVE_OUT, EXP_IDLE))
        plan.append((0, 0, zeros, ACC_IDLE, EXP_IDLE))
        return (name, plan)

    plans: list[tuple[str, list]] = []

    # Control states in isolation, before any composite schedule.
    plans.append(("clear_then_idle", [
        (scale, 0, [scale] * reg_width, ACC_CLEAR, EXP_IDLE),
        (scale, 0, [scale] * reg_width, ACC_IDLE, EXP_IDLE),
        (scale, 0, [scale] * reg_width, ACC_IDLE, EXP_IDLE),
    ]))

    # A dot product with an answer that is obvious by hand: 4 terms of 1.0*1.0,
    # drained through move_out so acc becomes observable on io.out.
    plans.append(("dot_product_ones", [
        (0, 0, zeros, ACC_CLEAR, EXP_IDLE),
        *[(scale, 0, [scale] + [0] * (reg_width - 1), ACC_ACCUMULATE, EXP_IDLE)
          for _ in range(4)],
        (0, reg_width, zeros, ACC_MOVE_OUT, EXP_IDLE),
        (0, reg_width, zeros, ACC_MOVE_OUT, EXP_IDLE),
    ]))

    # The zero escape: col_vec(regWidth) is a hardwired zero, and any selector
    # above it falls through to the same. This is how an X:N index buffer parks
    # a lane it has no key for, so it has to multiply to zero rather than alias
    # onto a real column.
    plans.append(("sel_col_escape", [
        (0, 0, zeros, ACC_CLEAR, EXP_IDLE),
        (scale, reg_width, [scale] * reg_width, ACC_ACCUMULATE, EXP_IDLE),
        (scale, reg_width + 1, [scale] * reg_width, ACC_ACCUMULATE, EXP_IDLE),
        (scale, reg_width - 1, [scale] * reg_width, ACC_ACCUMULATE, EXP_IDLE),
        (0, reg_width, zeros, ACC_MOVE_OUT, EXP_IDLE),
        (0, reg_width, zeros, ACC_MOVE_OUT, EXP_IDLE),
    ]))

    # Each lane of the column register file, selected in turn.
    plans.append(("every_column", [
        (0, 0, zeros, ACC_CLEAR, EXP_IDLE),
        *[(scale, i, [(i + 1) * 16 for i in range(reg_width)],
           ACC_ACCUMULATE, EXP_IDLE) for i in range(reg_width)],
        (0, reg_width, zeros, ACC_MOVE_OUT, EXP_IDLE),
        (0, reg_width, zeros, ACC_MOVE_OUT, EXP_IDLE),
    ]))

    # Full attention schedules: positive scores, negative scores, and a score
    # large enough that the exponential saturates.
    head_dim = 4
    plans.append(attention(
        "attention_positive",
        keys=[[scale // 2] * reg_width for _ in range(head_dim)],
        queries=[scale // 2] * head_dim, sel=3,
        values=[[(k + 1) * 32] * reg_width for k in range(4)], value_sel=3,
    ))
    plans.append(attention(
        "attention_negative",
        keys=[[-scale] * reg_width for _ in range(head_dim)],
        queries=[scale] * head_dim, sel=1,
        values=[[(k + 1) * 32] * reg_width for k in range(4)], value_sel=1,
    ))
    plans.append(attention(
        "attention_saturating",
        keys=[[3 * scale] * reg_width for _ in range(head_dim)],
        queries=[3 * scale] * head_dim, sel=0,
        values=[[64] * reg_width for _ in range(4)], value_sel=0,
    ))

    # The accumulator wraps rather than saturating -- 16 terms of 1.5*1.5 pass
    # Q8.8's +128 ceiling. Recorded as behaviour, not endorsed as correct.
    plans.append(("accumulator_wrap", [
        (0, 0, zeros, ACC_CLEAR, EXP_IDLE),
        *[(3 * scale // 2, 0, [3 * scale // 2] + [0] * (reg_width - 1),
           ACC_ACCUMULATE, EXP_IDLE) for _ in range(16)],
        (0, reg_width, zeros, ACC_MOVE_OUT, EXP_IDLE),
        (0, reg_width, zeros, ACC_MOVE_OUT, EXP_IDLE),
    ]))

    # Random control sequences: every state reachable from every other, which is
    # where a schedule assumption that happens to hold in the clean cases breaks.
    for index in range(3):
        plan = [(0, 0, zeros, ACC_CLEAR, EXP_IDLE)]
        controls = torch.randint(0, 4, (24,), generator=generator).tolist()
        exps = torch.randint(0, 2, (24,), generator=generator).tolist()
        sels = torch.randint(0, reg_width + 2, (24,), generator=generator).tolist()
        qs = torch.randint(-scale, scale, (24,), generator=generator).tolist()
        for step in range(24):
            plan.append((qs[step], sels[step], randcols(), controls[step], exps[step]))
        plans.append((f"random_{index}", plan))

    # RePE cannot be brought to a known state by reset: `acc` and `score_exp`
    # are Reg, not RegInit, so reset leaves them untouched, and acc_clear clears
    # only `acc` -- score_exp has no clear path at all. A case therefore starts
    # wherever the previous one left off unless it is driven to a known state
    # first. This preamble does that: clear the accumulator, then compute the
    # exponential of the zero it now holds, so score_exp = exp(0) = 1.0.
    #
    # The preamble's own two outputs still show the stale value, so they are
    # excluded from comparison via expected_idx; every later cycle is checked.
    preamble = [
        (0, 0, zeros, ACC_CLEAR, EXP_IDLE),
        (0, 0, zeros, ACC_IDLE, EXP_COMPUTE),
    ]

    cases = []
    for name, plan in plans:
        model = RePEModel(bits, point, reg_width)
        inputs: list[int] = []
        expected: list[int] = []
        for q_in, sel_col, columns, acc_ctrl, exp_ctrl in preamble + plan:
            inputs.extend([q_in, sel_col, acc_ctrl, exp_ctrl, *columns])
            expected.append(model.step(q_in, columns, sel_col, acc_ctrl, exp_ctrl))
        checks = [0] * len(preamble) + [1] * len(plan)
        cases.append({"name": name, "input_ticks": inputs,
                      "expected_value_ticks": expected, "expected_idx": checks})
    return cases


class RePERowModel:
    """Cycle-accurate mirror of one RePERow.

    The row registers everything on the way in -- `reg_q` from q_left,
    `reg_cols` from regs_top -- so its PEs see data one cycle after it is
    presented, and `row_sum` registers the adder tree, so a sum appears one
    cycle after the PE outputs that formed it. Two cycles of latency, in
    different places, which is exactly what a bench comparing only end values
    would fail to pin down.

    `io.clr` gates the row's own registers but NOT the PE control: repe_row.scala
    drives acc_ctrl and exp_ctrl to the PEs unconditionally, so a PE keeps
    accumulating through a row clear.
    """

    def __init__(self, pe_count: int, bits: int, point: int, reg_width: int) -> None:
        self.bits, self.reg_width = bits, reg_width
        self.pes = [RePEModel(bits, point, reg_width) for _ in range(pe_count)]
        self.reg_q = 0
        self.reg_cols = [0] * reg_width
        self.row_sum = 0

    def step(self, q_left: int, regs_top: list[int], clr: int,
             sel_cols: list[int], acc_ctrl: int, exp_ctrl: int) -> tuple[int, list[int]]:
        adder_out = self.row_sum
        regs_bottom = list(self.reg_cols)

        outs = [
            pe.step(self.reg_q, self.reg_cols, sel_cols[i], acc_ctrl, exp_ctrl)
            for i, pe in enumerate(self.pes)
        ]

        if clr:
            self.reg_q = 0
            self.reg_cols = [0] * self.reg_width
            self.row_sum = 0
        else:
            self.reg_q = q_left
            self.reg_cols = list(regs_top)
            # reduce(_+_) keeps full precision through the tree; only the
            # assignment to row_sum narrows, so the sum wraps rather than
            # saturating.
            self.row_sum = wrap(sum(outs), self.bits)
        return adder_out, regs_bottom


class RePEArrayModel:
    """Cycle-accurate mirror of RePEArray: rows chained top to bottom.

    rows(0) takes io.regs_top; rows(i+1) takes rows(i).regs_bottom, which is the
    *registered* reg_cols. So a column vector reaches row i on cycle i -- the
    array is systolic in the column direction.

    Control is not: clr, acc_ctrl and exp_ctrl are broadcast to every row on the
    same cycle. Row i therefore accumulates during the same window as row 0 while
    seeing data skewed by i cycles, so any schedule that does not skew q_left_vec
    to match will have the lower rows multiply against stale columns. This model
    reproduces that rather than correcting it; whether the schedule is usable is
    a separate question from whether the RTL matches its own structure.
    """

    def __init__(self, num_rows: int, pe_per_row: int, bits: int,
                 point: int, reg_width: int) -> None:
        self.rows = [
            RePERowModel(pe_per_row, bits, point, reg_width) for _ in range(num_rows)
        ]

    def step(self, q_left_vec: list[int], regs_top: list[int], clr: int,
             sel_cols: list[list[int]], acc_ctrl: int, exp_ctrl: int) -> list[int]:
        # regs_bottom is combinational from each row's register, so every row's
        # input is read from current state before any row advances.
        tops = [list(regs_top)] + [list(row.reg_cols) for row in self.rows[:-1]]
        return [
            row.step(q_left_vec[i], tops[i], clr, sel_cols[i], acc_ctrl, exp_ctrl)[0]
            for i, row in enumerate(self.rows)
        ]


def repe_row_cases(pe_count: int, bits: int, point: int,
                   reg_width: int, seed: int) -> list[dict]:
    """Schedules aimed at the row's two latencies and its adder tree."""
    scale = 1 << point
    generator = torch.Generator().manual_seed(seed)
    zeros = [0] * reg_width

    def plan_entry(q_left, regs_top, clr, sel_cols, acc_ctrl, exp_ctrl):
        return (q_left, regs_top, clr, sel_cols, acc_ctrl, exp_ctrl)

    all_zero_sel = [reg_width] * pe_count  # every PE parked on the zero escape
    plans: list[tuple[str, list]] = []

    # The column shift chain in isolation: push a recognisable vector in and
    # watch regs_bottom produce it one cycle later.
    marker = [(i + 1) * 64 for i in range(reg_width)]
    plans.append(("column_shift", [
        plan_entry(0, marker, 0, all_zero_sel, ACC_CLEAR, EXP_IDLE),
        plan_entry(0, zeros, 0, all_zero_sel, ACC_CLEAR, EXP_IDLE),
        plan_entry(0, zeros, 0, all_zero_sel, ACC_CLEAR, EXP_IDLE),
    ]))

    # clr must zero reg_q, reg_cols and row_sum together.
    plans.append(("clear_row", [
        plan_entry(scale, marker, 0, all_zero_sel, ACC_CLEAR, EXP_IDLE),
        plan_entry(scale, marker, 1, all_zero_sel, ACC_CLEAR, EXP_IDLE),
        plan_entry(0, zeros, 0, all_zero_sel, ACC_CLEAR, EXP_IDLE),
        plan_entry(0, zeros, 0, all_zero_sel, ACC_CLEAR, EXP_IDLE),
    ]))

    # The adder tree as a softmax denominator: every PE holds an exponential, so
    # adder_out is sum_j exp(s_j). Each PE selects a different column, so the
    # scores differ and a tree that dropped or double-counted a lane would show.
    scores = [(i + 1) * 32 for i in range(reg_width)]
    denominator = [
        plan_entry(0, zeros, 1, list(range(pe_count)), ACC_CLEAR, EXP_IDLE),
        plan_entry(scale, scores, 0, list(range(pe_count)), ACC_CLEAR, EXP_IDLE),
        plan_entry(scale, scores, 0, list(range(pe_count)), ACC_ACCUMULATE, EXP_IDLE),
        plan_entry(0, zeros, 0, list(range(pe_count)), ACC_IDLE, EXP_COMPUTE),
    ]
    denominator += [plan_entry(0, zeros, 0, list(range(pe_count)), ACC_IDLE, EXP_IDLE)
                    for _ in range(3)]
    plans.append(("softmax_denominator", denominator))

    # The same row draining AV products: adder_out becomes sum_j exp(s_j)*v_j[k],
    # one output dimension per cycle.
    av = list(denominator[:4])
    av += [plan_entry(0, [(k + 1) * 48] * reg_width, 0, list(range(pe_count)),
                      ACC_MOVE_OUT, EXP_IDLE) for k in range(4)]
    av += [plan_entry(0, zeros, 0, list(range(pe_count)), ACC_IDLE, EXP_IDLE)
           for _ in range(2)]
    plans.append(("av_drain", av))

    for index in range(3):
        plan = [plan_entry(0, zeros, 1, all_zero_sel, ACC_CLEAR, EXP_IDLE)]
        for _ in range(20):
            plan.append(plan_entry(
                int(torch.randint(-scale, scale, (1,), generator=generator).item()),
                torch.randint(-scale, scale, (reg_width,), generator=generator).tolist(),
                int(torch.randint(0, 2, (1,), generator=generator).item()),
                torch.randint(0, reg_width + 2, (pe_count,), generator=generator).tolist(),
                int(torch.randint(0, 4, (1,), generator=generator).item()),
                int(torch.randint(0, 2, (1,), generator=generator).item()),
            ))
        plans.append((f"random_{index}", plan))

    # Same reasoning as repe_cases: the PEs inside the row have unresettable
    # score_exp registers, so each case is driven to a known state first.
    preamble = [
        plan_entry(0, zeros, 1, all_zero_sel, ACC_CLEAR, EXP_IDLE),
        plan_entry(0, zeros, 1, all_zero_sel, ACC_IDLE, EXP_COMPUTE),
    ]

    cases = []
    for name, plan in plans:
        model = RePERowModel(pe_count, bits, point, reg_width)
        inputs: list[int] = []
        expected: list[int] = []
        for q_left, regs_top, clr, sel_cols, acc_ctrl, exp_ctrl in preamble + plan:
            inputs.extend([q_left, clr, acc_ctrl, exp_ctrl, *regs_top, *sel_cols])
            adder_out, regs_bottom = model.step(
                q_left, regs_top, clr, sel_cols, acc_ctrl, exp_ctrl
            )
            expected.extend([adder_out, *regs_bottom])
        checks = [0] * len(preamble) + [1] * len(plan)
        cases.append({"name": name, "input_ticks": inputs,
                      "expected_value_ticks": expected, "expected_idx": checks})
    return cases


def repe_array_cases(num_rows: int, pe_per_row: int, bits: int, point: int,
                     reg_width: int, seed: int) -> list[dict]:
    """Schedules aimed at the inter-row skew, which is the array's whole content."""
    scale = 1 << point
    generator = torch.Generator().manual_seed(seed)
    zeros = [0] * reg_width
    parked = [[reg_width] * pe_per_row for _ in range(num_rows)]
    selected = [list(range(pe_per_row)) for _ in range(num_rows)]

    plans: list[tuple[str, list]] = []

    # One recognisable column vector pushed through: it must appear at row i on
    # cycle i, which is the systolic property the array exists to provide.
    marker = [(i + 1) * 64 for i in range(reg_width)]
    skew = [([0] * num_rows, marker, 0, parked, ACC_CLEAR, EXP_IDLE)]
    skew += [([0] * num_rows, zeros, 0, parked, ACC_CLEAR, EXP_IDLE)
             for _ in range(num_rows + 2)]
    plans.append(("column_skew", skew))

    # A broadcast clear must reach every row on the same cycle.
    plans.append(("broadcast_clear", [
        ([scale] * num_rows, marker, 0, parked, ACC_CLEAR, EXP_IDLE),
        ([scale] * num_rows, marker, 1, parked, ACC_CLEAR, EXP_IDLE),
        ([0] * num_rows, zeros, 0, parked, ACC_CLEAR, EXP_IDLE),
        ([0] * num_rows, zeros, 0, parked, ACC_CLEAR, EXP_IDLE),
    ]))

    # Distinct queries per row against a streamed column: the rows must not be
    # able to see each other's q_left, and their adder outputs must differ.
    queries = [(row + 1) * 64 for row in range(num_rows)]
    attention = [([0] * num_rows, zeros, 1, selected, ACC_CLEAR, EXP_IDLE)]
    attention += [(queries, [(c + 1) * 32] * reg_width, 0, selected,
                   ACC_ACCUMULATE, EXP_IDLE) for c in range(3)]
    attention += [([0] * num_rows, zeros, 0, selected, ACC_IDLE, EXP_COMPUTE)]
    attention += [([0] * num_rows, zeros, 0, selected, ACC_IDLE, EXP_IDLE)
                  for _ in range(num_rows + 2)]
    plans.append(("per_row_queries", attention))

    for index in range(2):
        plan = [([0] * num_rows, zeros, 1, parked, ACC_CLEAR, EXP_IDLE)]
        for _ in range(16):
            plan.append((
                torch.randint(-scale, scale, (num_rows,), generator=generator).tolist(),
                torch.randint(-scale, scale, (reg_width,), generator=generator).tolist(),
                int(torch.randint(0, 2, (1,), generator=generator).item()),
                [torch.randint(0, reg_width + 2, (pe_per_row,),
                               generator=generator).tolist() for _ in range(num_rows)],
                int(torch.randint(0, 4, (1,), generator=generator).item()),
                int(torch.randint(0, 2, (1,), generator=generator).item()),
            ))
        plans.append((f"random_{index}", plan))

    preamble = [
        ([0] * num_rows, zeros, 1, parked, ACC_CLEAR, EXP_IDLE),
        ([0] * num_rows, zeros, 1, parked, ACC_IDLE, EXP_COMPUTE),
    ]

    cases = []
    for name, plan in plans:
        model = RePEArrayModel(num_rows, pe_per_row, bits, point, reg_width)
        inputs: list[int] = []
        expected: list[int] = []
        for q_vec, regs_top, clr, sel_cols, acc_ctrl, exp_ctrl in preamble + plan:
            flat_sel = [value for row in sel_cols for value in row]
            inputs.extend([clr, acc_ctrl, exp_ctrl, *q_vec, *regs_top, *flat_sel])
            expected.extend(model.step(q_vec, regs_top, clr, sel_cols,
                                       acc_ctrl, exp_ctrl))
        checks = [0] * len(preamble) + [1] * len(plan)
        cases.append({"name": name, "input_ticks": inputs,
                      "expected_value_ticks": expected, "expected_idx": checks})
    return cases
