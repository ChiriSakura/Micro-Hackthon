"""预测单元（PrePEA、TopK、softmax 归一化）的参照模型。

三种不同性质的参照，选哪种取决于想发现哪类问题：

* `TopK` → `torch.topk`（同一定点网格）：发现「算错了」
* `PSumSoftmax` → 含截断宽度的 bit-exact 镜像：同上
* `PrePEArray` → **DynaX 自己的软件**（见 `golden.software`）：
  发现「接口约定接反了」，镜像做不到这一点

`PrePEArray*Model` 里记录了两条源码从未说明的性质：`cycleToggle` /
`cycleCount` 无条件每周期推进而 PE 的 `inputCounter` 只在 sInput 推进，
所以两者有相对相位、装载必须从对的那一拍开始；以及选择索引与到达顺序相反。
"""

from __future__ import annotations

import torch

from golden.exp_unit import exp_unit_reference
from golden.fixedpoint import trunc_div, wrap
from golden.software import software_1_2_qk, software_1_4_qk


def psum_softmax_reference(add1: int, add2: int, exp: int, s: int,
                           bits: int, point: int) -> tuple[int, int]:
    """Mirror of PSumSoftmax, including the widths it truncates at."""
    total = wrap(add1 + add2, bits)
    if s == 0:
        return total, 0
    if exp == 0:
        return 0, 0
    # FixedPointDiv: (num << point) / den, then narrowed back to `bits`.
    return wrap(trunc_div(total << point, exp), bits), 1


def psum_softmax_cases(bits: int, point: int, seed: int) -> list[dict]:
    scale = 1 << point
    limit = 1 << (bits - 1)
    named: list[tuple[str, list[tuple[int, int, int, int]]]] = [
        # s=0 is the accumulate mode: pass the sum through, do not divide.
        ("passthrough", [(a, b, 0, 0) for a, b in
                         [(0, 0), (scale, scale), (-scale, scale), (limit - 1, 1)]]),
        # The guarded divide-by-zero path.
        ("exp_is_zero", [(scale, 0, 0, 1), (0, 0, 0, 1), (-scale, 0, 0, 1)]),
        # Exact quotients: the answer is checkable by hand.
        ("exact", [(scale, 0, scale, 1), (2 * scale, 0, scale, 1),
                   (scale, scale, 2 * scale, 1), (-2 * scale, 0, scale, 1)]),
        # Truncation toward zero, both signs -- the easy thing to get wrong.
        ("truncation", [(3, 0, 2 * scale, 1), (-3, 0, 2 * scale, 1),
                        (1, 0, 3 * scale, 1), (-1, 0, 3 * scale, 1)]),
        # Quotients too large for Q(bits-point).point: the module truncates the
        # width rather than saturating, so the result wraps. Recorded as the
        # module's behaviour, not endorsed as correct -- see the README.
        ("quotient_overflow", [(scale, 0, 1, 1), (100 * scale, 0, scale, 1),
                               (scale, 0, 2, 1)]),
        # Sum overflow: add1 + add2 narrows from bits+1 back to bits.
        ("sum_overflow", [(limit - 1, limit - 1, scale, 1),
                          (-limit, -limit, scale, 1)]),
    ]
    generator = torch.Generator().manual_seed(seed)
    noise = torch.randint(-limit, limit, (48,), generator=generator).tolist()
    named.append(("random", [
        (noise[i], noise[i + 1], noise[i + 2], noise[i + 3] & 1)
        for i in range(0, 44, 4)
    ]))

    cases = []
    for name, points in named:
        inputs: list[int] = []
        expected: list[int] = []
        for add1, add2, exp, s in points:
            inputs.extend((add1, add2, exp, s))
            expected.extend(psum_softmax_reference(add1, add2, exp, s, bits, point))
        cases.append({"name": name, "input_ticks": inputs,
                      "expected_value_ticks": expected, "expected_idx": []})
    return cases


# prepe_1_2.scala / prepe_1_4.scala: Enum(4) for the PE state.
S_IDLE, S_CLEAR, S_CALC, S_INPUT = 0, 1, 2, 3


class PrePEModel:
    """Cycle-accurate mirror of one PrePE_1_2.

    Everything this PE exposes is a register, so every output lags its input by
    a cycle, and the multiply in sCalc uses the *previously* latched top values
    while latching the next ones -- the systolic pattern. A reference that
    multiplied the values presented this cycle would be off by one everywhere
    and still look plausible on a constant stimulus, which is why the cases
    below use ramps rather than constants.

    `inputCounter` is a single bit that only samples left_in when it reads 1, so
    the q chain advances once every two sInput cycles. That is not arbitrary:
    PrePEArray_1_2 spends two cycles per input pair (latch, then compare-and-
    select), which is the 1:2 Q pruning, so one selected value arrives every two
    cycles and the chain shifts at exactly that rate.
    """

    def __init__(self, out_bits: int) -> None:
        self.out_bits = out_bits
        self.top0 = 0
        self.top1 = 0
        self.left = 0
        self.sel = 0
        self.psum = 0
        self.counter = 0

    def step(self, left_in: int, sel_in: int, top_in0: int, top_in1: int,
             psum_in: int, state: int) -> tuple[int, int, int, int, int]:
        outputs = (self.top0, self.top1, self.left, self.sel, self.psum)
        mask = (1 << self.out_bits) - 1

        if state == S_CLEAR:
            self.top0 = self.top1 = self.left = self.sel = self.psum = 0
            self.counter = 0
        elif state == S_CALC:
            chosen = self.top0 if self.sel == 0 else self.top1
            # 有符号乘累加，按二进制补码窄化回 outBits——和 RTL 的
            # `(a * b +& c)(outBits-1, 0).asSInt` 一致。
            self.psum = wrap(chosen * self.left + psum_in, self.out_bits)
            self.top0, self.top1 = top_in0, top_in1
        elif state == S_INPUT:
            if self.counter == 1:
                self.left, self.sel = left_in, sel_in
            self.counter ^= 1
            self.top0 = self.top1 = self.psum = 0
        return outputs


def prepe_cases(out_bits: int, seed: int) -> list[dict]:
    """单个 PrePE 的用例。操作数是**有符号** 4-bit（-7..7）。

    这里曾经是无符号的，和 RTL 的 UInt(4.W) 端口一致。端口改成 SInt 之后
    同一个位模式含义就变了——比如 14 在无符号下是 +14，有符号下是 -2。
    """
    generator = torch.Generator().manual_seed(seed)
    plans: list[tuple[str, list]] = []

    # (left_in, sel_in, top_in0, top_in1, psum_in, state)
    def entry(left=0, sel=0, t0=0, t1=0, psum=0, state=S_IDLE):
        return (left, sel, t0, t1, psum, state)

    limit = 7          # SInt(4) 的软件量化上界，同 calc_max_quant_value(4)
    psum_lo = -(1 << (out_bits - 1))
    psum_hi = (1 << (out_bits - 1)) - 1

    # sClear must zero every register including the input counter.
    plans.append(("clear", [
        entry(left=-6, sel=1, t0=7, t1=-5, psum=100, state=S_CALC),
        entry(state=S_CLEAR),
        entry(state=S_IDLE),
        entry(state=S_IDLE),
    ]))

    # The input counter samples on its second sInput cycle, not its first.
    plans.append(("input_counter", [
        entry(state=S_CLEAR),
        entry(left=3, sel=0, state=S_INPUT),    # counter 0 -> 不采样
        entry(left=-7, sel=1, state=S_INPUT),   # counter 1 -> 采样（负值）
        entry(left=2, sel=0, state=S_INPUT),    # counter 0 -> 不采样
        entry(left=5, sel=1, state=S_INPUT),    # counter 1 -> 采样
        entry(state=S_IDLE),
        entry(state=S_IDLE),
    ]))

    # Both halves of the 1:2 select, with a ramp so an off-by-one in which top
    # register is multiplied cannot hide behind equal operands.
    for name, sel_bit in (("select_top0", 0), ("select_top1", 1)):
        plan = [entry(state=S_CLEAR)]
        # 负的 left 配正负交替的 top：符号必须一路传到乘积。
        plan += [entry(left=-6, sel=sel_bit, state=S_INPUT) for _ in range(2)]
        plan += [entry(t0=index - 3, t1=4 - index, psum=index * 4, state=S_CALC)
                 for index in range(6)]
        plan += [entry(state=S_IDLE), entry(state=S_IDLE)]
        plans.append((name, plan))

    # The psum chain saturating its width: 4x4 products accumulated past
    # 2^outBits wrap rather than saturate, same as every other narrowing here.
    plan = [entry(state=S_CLEAR)]
    plan += [entry(left=-limit, sel=0, state=S_INPUT) for _ in range(2)]
    plan += [entry(t0=-limit, t1=limit, psum=psum_lo + 200, state=S_CALC)
             for _ in range(4)]
    plan += [entry(state=S_IDLE)]
    plans.append(("psum_wrap", plan))   # 有符号下是向负方向回绕

    for index in range(3):
        plan = [entry(state=S_CLEAR)]
        for _ in range(24):
            values = torch.randint(-limit, limit + 1, (4,), generator=generator).tolist()
            plan.append(entry(
                left=values[0], sel=values[1] & 1, t0=values[2], t1=values[3],
                psum=int(torch.randint(psum_lo, psum_hi + 1, (1,),
                                       generator=generator).item()),
                state=int(torch.randint(0, 4, (1,), generator=generator).item()),
            ))
        plans.append((f"random_{index}", plan))

    # Every output here is a combinational read of a register, so the sClear
    # cycle itself still shows the previous case's contents -- the zeroing lands
    # on the edge that ends it. One unchecked clear cycle in front of each plan
    # is what makes the cases independent; reset cannot do it, because these are
    # Reg rather than RegInit.
    preamble = [entry(state=S_CLEAR)]

    cases = []
    for name, plan in plans:
        model = PrePEModel(out_bits)
        inputs: list[int] = []
        expected: list[int] = []
        for left, sel, t0, t1, psum, state in preamble + plan:
            inputs.extend([left, sel, t0, t1, psum, state])
            expected.extend(model.step(left, sel, t0, t1, psum, state))
        checks = [0] * len(preamble) + [1] * len(plan)
        cases.append({"name": name, "input_ticks": inputs,
                      "expected_value_ticks": expected, "expected_idx": checks})
    return cases


class PrePEArrayModel:
    """Cycle-accurate mirror of PrePEArray_1_2.

    The array wraps the PE grid in the part that actually does the 1:2 pruning:
    `cycleToggle` latches one Q element, compares it with the next, and drives
    the larger of the two into PE column 0 along with a select bit. Everything
    else is chaining -- Q shifts right, K shifts down, the partial sum ripples
    right one PE per cycle.

    Two details the sources do not state but a driver has to know:

      * `cycleToggle` toggles every cycle unconditionally, while a PE's
        `inputCounter` only advances in sInput. They can therefore drift out of
        phase, and a Q load that starts on the wrong parity samples nothing.
      * PE column c is wired to K[2c], K[2c+1], and the Q chain shifts right, so
        the pairs have to be injected last-first for pair c to land in PE c.
    """

    def __init__(self, height: int, width: int, out_bits: int,
                 bits: int, point: int) -> None:
        self.height, self.width = height, width
        self.columns = width // 2
        self.out_bits, self.bits, self.point = out_bits, bits, point
        self.pes = [[PrePEModel(out_bits) for _ in range(self.columns)]
                    for _ in range(height)]
        self.left_first = [0] * height
        self.cycle_toggle = 0
        self.exp_regs = [0] * height

    def step(self, left_in: list[int], top_in: list[int],
             pes_state: int, array_state: int) -> list[int]:
        """Advance one cycle; returns s_out (exp of each row's partial sum)."""
        outputs = list(self.exp_regs)

        # Column 0's inputs come from the pruning stage, not from a neighbour.
        if self.cycle_toggle == 0:
            first_left = [0] * self.height
            first_sel = [0] * self.height
        else:
            # 选谁按幅值，传下去的是带符号的值。
            first_left = [
                self.left_first[i] if abs(self.left_first[i]) > abs(left_in[i])
                else left_in[i]
                for i in range(self.height)
            ]
            # sel = 1 when the FIRST-latched element won. Which K that selects is
            # the question tb_prepe_array.cpp exists to answer: sel=1 drives
            # top_in1, i.e. K[2c+1], so the odd element of the pair has to be the
            # one presented first for the product to pair up correctly.
            first_sel = [
                1 if abs(self.left_first[i]) > abs(left_in[i]) else 0
                for i in range(self.height)
            ]

        # Every PE's inputs are read from current state before any PE advances.
        left_inputs = [
            [first_left[r]] + [self.pes[r][c].left for c in range(self.columns - 1)]
            for r in range(self.height)
        ]
        sel_inputs = [
            [first_sel[r]] + [self.pes[r][c].sel for c in range(self.columns - 1)]
            for r in range(self.height)
        ]
        psum_inputs = [
            [0] + [self.pes[r][c].psum for c in range(self.columns - 1)]
            for r in range(self.height)
        ]
        top_inputs = [
            [(top_in[2 * c], top_in[2 * c + 1]) for c in range(self.columns)]
            if r == 0 else
            [(self.pes[r - 1][c].top0, self.pes[r - 1][c].top1)
             for c in range(self.columns)]
            for r in range(self.height)
        ]

        for r in range(self.height):
            for c in range(self.columns):
                top0, top1 = top_inputs[r][c]
                self.pes[r][c].step(
                    left_inputs[r][c], sel_inputs[r][c], top0, top1,
                    psum_inputs[r][c], pes_state,
                )

        # The exponential reads the last column's registered partial sum, which
        # the PE step above has just replaced -- so it sees the new value, the
        # same as the RTL where psum_out is a wire off the register being
        # written this cycle... except it is not: psum_out is the register, so
        # the exponential sees the PREVIOUS partial sum.
        tail = [psum_inputs[r][-1] if self.columns == 1 else
                self.pes[r][self.columns - 1].psum for r in range(self.height)]

        if self.cycle_toggle == 0:
            self.left_first = list(left_in)
        self.cycle_toggle ^= 1

        if array_state == A_CLEAR:
            self.exp_regs = [0] * self.height
        elif array_state == A_IDLE:
            pass  # switch(aIdle) re-assigns expRegs to itself, holding it
        else:
            # 不再对 psum == 0 特殊处理：有符号下 0 是正常的中间分数，
            # 强制归零会把它排到所有负分数之下，破坏 exp 的单调性。
            self.exp_regs = [
                wrap(exp_unit_reference(value, self.bits, self.point, 4, 4), self.bits)
                for value in tail
            ]
        return outputs


A_IDLE, A_CLEAR, A_CALC = 0, 1, 2


def prepe_array_schedule(query: list[int], key: list[int], height: int,
                         width: int, *, odd_first: bool) -> list[tuple]:
    """Cycles that load Q, then stream K, for one query row broadcast to all rows.

    `odd_first` chooses which element of each pair is presented first. The RTL
    ties sel=1 to "the first one won" and sel=1 to K[2c+1], so only one of the
    two orders can pair a kept Q with its own K. Making it a parameter is what
    turns an unstated convention into something a test can decide.
    """
    columns = width // 2
    plan: list[tuple] = []

    # `cycleToggle` advances every cycle no matter what state the PEs are in,
    # while a PE's `inputCounter` only advances in sInput -- so the two have a
    # relative phase, and the load has to start on the right one. A PE samples
    # left_in when its counter reads 1; the array emits the compared value when
    # the toggle reads 1. Opening with an idle cycle puts sClear on the odd
    # toggle, which lines the two up: the first sInput cycle latches, the second
    # compares, and the PE samples exactly then. Starting one cycle earlier
    # samples the zero the toggle-0 branch drives, and loads nothing.
    plan.append(([0] * height, [0] * width, S_IDLE, A_CLEAR))
    plan.append(([0] * height, [0] * width, S_CLEAR, A_CLEAR))
    for c in reversed(range(columns)):
        low, high = query[2 * c], query[2 * c + 1]
        first, second = (high, low) if odd_first else (low, high)
        plan.append(([first] * height, [0] * width, S_INPUT, A_CLEAR))
        plan.append(([second] * height, [0] * width, S_INPUT, A_CLEAR))

    # Stream K held stationary: PE column 0 recomputes its product every cycle
    # and the partial sum ripples right one column per cycle, so `columns`
    # cycles are enough for the last column to hold the whole dot product.
    # 沉降时间 = height + 链长，这就是阵列的脉动延迟本身：K 每周期下移一行，
    # 所以第 (height-1) 行要等 height-1 个周期才看到它；psum 每周期右移一个 PE，
    # 所以还要 columns 个周期才走到链尾。另加几拍余量。
    #
    # 小实例（height=2）会掩盖这一点——只留 columns+4 也能对。论文尺寸下
    # 前几行正确、后面逐行衰减到 0，正是 K 还没走到那些行。
    for _ in range(height + columns + 4):
        plan.append(([0] * height, list(key), S_CALC, A_CLEAR))
    # One aCalc cycle to latch the exponential of that settled partial sum.
    plan.append(([0] * height, list(key), S_CALC, A_CALC))
    plan.append(([0] * height, list(key), S_IDLE, A_IDLE))
    return plan


class PrePE14Model:
    """Cycle-accurate mirror of one PrePE_1_4.

    The four-way generalisation of PrePEModel: `inputCounter` is two bits and
    samples on its fourth sInput cycle, so the q chain shifts once every four
    cycles rather than every two -- the rate at which PrePEArray_1_4 produces
    one selected value out of each group of four.
    """

    def __init__(self, out_bits: int) -> None:
        self.out_bits = out_bits
        self.top = [0, 0, 0, 0]
        self.left = 0
        self.sel = 0
        self.psum = 0
        self.counter = 0

    def step(self, left_in: int, sel_in: int, top_in: list[int],
             psum_in: int, state: int) -> tuple[int, ...]:
        outputs = (*self.top, self.left, self.sel, self.psum)
        mask = (1 << self.out_bits) - 1

        if state == S_CLEAR:
            self.top = [0, 0, 0, 0]
            self.left = self.sel = self.psum = 0
            self.counter = 0
        elif state == S_CALC:
            # 有符号乘累加，按二进制补码窄化——和 RTL 的
            # `(a * b +& c)(outBits-1, 0).asSInt` 一致。
            self.psum = wrap(self.top[self.sel] * self.left + psum_in, self.out_bits)
            self.top = list(top_in)
        elif state == S_INPUT:
            if self.counter == 3:
                self.left, self.sel = left_in, sel_in
            self.counter = 0 if self.counter == 3 else self.counter + 1
            self.top = [0, 0, 0, 0]
            self.psum = 0
        return outputs


class PrePEArray14Model:
    """Cycle-accurate mirror of PrePEArray_1_4.

    The selection stage collects four Q elements in a three-deep shift register
    and picks the largest on the fourth cycle. Tracing the shift is what settles
    the pairing: at cycleCount==3 the comparator sees

        a = io.left_in      (4th presented)  -> index 0 -> K[4c+0]
        b = l_first         (3rd presented)  -> index 1 -> K[4c+1]
        c = l_second        (2nd presented)  -> index 2 -> K[4c+2]
        d = l_third         (1st presented)  -> index 3 -> K[4c+3]

    so the index order runs opposite to the arrival order, and a group has to be
    fed in DESCENDING index order for each kept Q to meet its own K. That is the
    same rule the 1:2 array follows -- "odd element first" is this convention on
    a group of two -- which the sources state in neither case.

    Ties differ from the software either way: every comparison here is a strict
    `>`, so a tie keeps the higher index, while torch.argmax keeps the lower.
    """

    def __init__(self, height: int, width: int, out_bits: int,
                 bits: int, point: int) -> None:
        self.height, self.width = height, width
        self.columns = width // 4
        self.out_bits, self.bits, self.point = out_bits, bits, point
        self.pes = [[PrePE14Model(out_bits) for _ in range(self.columns)]
                    for _ in range(height)]
        self.first = [0] * height
        self.second = [0] * height
        self.third = [0] * height
        self.cycle_count = 0
        self.exp_regs = [0] * height

    def step(self, left_in: list[int], top_in: list[int],
             pes_state: int, array_state: int) -> list[int]:
        outputs = list(self.exp_regs)

        selecting = self.cycle_count == 3
        head_left = [0] * self.height
        head_sel = [0] * self.height
        if selecting:
            for i in range(self.height):
                a, b = left_in[i], self.first[i]
                c, d = self.second[i], self.third[i]
                # 选谁按**幅值**（软件用 argmax(abs)），传下去的是**带符号**
                # 的值。上游比幅值也传幅值——这就是符号分歧的来源。
                max01, idx01 = (a, 0) if abs(a) > abs(b) else (b, 1)
                max23, idx23 = (c, 2) if abs(c) > abs(d) else (d, 3)
                head_left[i], head_sel[i] = (
                    (max01, idx01) if abs(max01) > abs(max23) else (max23, idx23)
                )

        left_inputs = [
            [head_left[r]] + [self.pes[r][c].left for c in range(self.columns - 1)]
            for r in range(self.height)
        ]
        sel_inputs = [
            [head_sel[r]] + [self.pes[r][c].sel for c in range(self.columns - 1)]
            for r in range(self.height)
        ]
        psum_inputs = [
            [0] + [self.pes[r][c].psum for c in range(self.columns - 1)]
            for r in range(self.height)
        ]
        top_inputs = [
            [list(top_in[4 * c:4 * c + 4]) for c in range(self.columns)]
            if r == 0 else
            [list(self.pes[r - 1][c].top) for c in range(self.columns)]
            for r in range(self.height)
        ]

        tail = [self.pes[r][self.columns - 1].psum for r in range(self.height)]

        for r in range(self.height):
            for c in range(self.columns):
                self.pes[r][c].step(
                    left_inputs[r][c], sel_inputs[r][c], top_inputs[r][c],
                    psum_inputs[r][c], pes_state,
                )

        if selecting:
            # The selection cycle clears the shift register rather than shifting.
            self.first = [0] * self.height
            self.second = [0] * self.height
            self.third = [0] * self.height
            self.cycle_count = 0
        else:
            self.third = list(self.second)
            self.second = list(self.first)
            self.first = list(left_in)
            self.cycle_count += 1

        if array_state == A_CLEAR:
            self.exp_regs = [0] * self.height
        elif array_state != A_IDLE:
            # 同 1:2：不再对 psum == 0 特殊处理，有符号下 0 是正常中间分数。
            self.exp_regs = [
                wrap(exp_unit_reference(value, self.bits, self.point, 4, 4), self.bits)
                for value in tail
            ]
        return outputs


def prepe_array_14_schedule(query: list[int], key: list[int], height: int,
                            width: int, *, descending: bool) -> list[tuple]:
    """Cycles that load Q in groups of four, then stream K.

    `cycleCount` runs free while a PE's `inputCounter` only advances in sInput,
    so the load has to begin on the cycle where both read zero -- the schedule
    tracks cycleCount and pads with idle cycles until it wraps. Starting on any
    other phase samples the zero that the non-selection branch drives.
    """
    columns = width // 4
    plan: list[tuple] = []
    cycle_count = 0

    def emit(left, top, pes_state, array_state):
        nonlocal cycle_count
        plan.append((left, top, pes_state, array_state))
        cycle_count = 0 if cycle_count == 3 else cycle_count + 1

    emit([0] * height, [0] * width, S_IDLE, A_CLEAR)
    emit([0] * height, [0] * width, S_CLEAR, A_CLEAR)
    while cycle_count != 0:
        emit([0] * height, [0] * width, S_IDLE, A_CLEAR)

    # Groups last-first so group c lands in PE column c; within a group,
    # descending index order so the kept Q meets its own K.
    for c in reversed(range(columns)):
        group = list(range(4 * c, 4 * c + 4))
        order = list(reversed(group)) if descending else group
        for position in order:
            emit([query[position]] * height, [0] * width, S_INPUT, A_CLEAR)

    # 同 1:2：沉降时间必须覆盖 height 行的下移加 columns 级的 psum 右移。
    for _ in range(height + columns + 4):
        emit([0] * height, list(key), S_CALC, A_CLEAR)
    emit([0] * height, list(key), S_CALC, A_CALC)
    emit([0] * height, list(key), S_IDLE, A_IDLE)
    return plan


def prepe_array_14_cases(height: int, width: int, out_bits: int, bits: int,
                         point: int, seed: int) -> list[dict]:
    """Drive the 1:4 array with real (Q, K) and check it against DynaX's Python.

    Same arbiter as the 1:2 case and for the same reason: the accelerator exists
    to run quant_qk_matmul, so that is what decides whether the selection index
    means what the array assumes. Groups carry no ties, because a tie is a
    separate disagreement (the software keeps the lowest index, every comparison
    in the RTL is a strict `>`).

    Q spans the full 6-bit range because that is what the comparator sees, but K
    is held small on purpose. The only observable output is exp(psum) in Q8.8,
    which saturates above e^7; full-range 6-bit operands drive the partial sum
    to ~7900, i.e. e^31, so every case would read 32767 and the test would agree
    with itself no matter what the selection did. Measured: with full-range K a
    deliberately wrong feed order still "agrees" on 149 of 200 random inputs.
    With K bounded the same wrong order agrees on none.
    """
    generator = torch.Generator().manual_seed(seed)
    cases = []
    mismatched_orders = 0

    for index in range(6):
        query: list[int] = []
        for _ in range(width // 4):
            # 幅值互不相同（避开平局），符号随机——和 1:2 同样的理由：
            # 非负输入会让 sum(|q||k|) 和 sum(qk) 恰好相同，从而掩盖分歧。
            group = (torch.randperm(31, generator=generator)[:4] + 1).tolist()
            signs = (torch.randint(0, 2, (4,), generator=generator) * 2 - 1).tolist()
            query.extend(int(v * sgn) for v, sgn in zip(group, signs))
        key_max = _key_bound(width // 4, 31, point, bits, operand_bits=6)
        magnitude = torch.randint(1, key_max + 1, (width,), generator=generator)
        key_signs = torch.randint(0, 2, (width,), generator=generator) * 2 - 1
        key = (magnitude * key_signs).tolist()

        model = PrePEArray14Model(height, width, out_bits, bits, point)
        plan = prepe_array_14_schedule(query, key, height, width, descending=True)
        inputs: list[int] = []
        expected: list[int] = []
        for left_in, top_in, pes_state, array_state in plan:
            inputs.extend([pes_state, array_state, *left_in, *top_in])
            expected.extend(model.step(left_in, top_in, pes_state, array_state))

        psum = software_1_4_qk(query, key, out_bits)
        want = 0 if psum == 0 else wrap(
            exp_unit_reference(psum, bits, point, 4, 4), bits
        )
        settled = expected[-height:]
        assert all(value == want for value in settled), (
            f"case {index}: array gives {settled}, software says {want}"
        )

        other = PrePEArray14Model(height, width, out_bits, bits, point)
        for left_in, top_in, pes_state, array_state in prepe_array_14_schedule(
            query, key, height, width, descending=False
        ):
            wrong = other.step(left_in, top_in, pes_state, array_state)
        mismatched_orders += any(value != want for value in wrong)

        cases.append({
            "name": f"qk_{index}",
            "input_ticks": inputs,
            "expected_value_ticks": expected,
            "expected_idx": [0, 0] + [1] * (len(plan) - 2),
        })

    print(f"  key bound: K in [1, {key_max}] so exp(psum) stays out of saturation")
    print(f"  pairing check: {mismatched_orders}/6 cases disagree with the "
          f"software when each group is fed in ascending index order")
    return cases



def _key_bound(chain_length: int, query_max: int, point: int, bits: int,
               operand_bits: int | None = None) -> int:
    """K 的上界。两个约束取更紧的那个。

    这个函数存在的理由是一次真实的教训：阵列唯一可观测的输出是 Q8.8 的
    `exp(psum)`，超过 e^7 就饱和到 32767。链越长 psum 越大，论文尺寸
    （chain=16 或 8）比小实例大一个数量级——**一旦全部饱和，故意喂错顺序
    也读出同一个值，测试就和自己一致了**。实测过：1:4 在满量程 K 下，
    错误的喂入顺序仍有 149/200「通过」。

    选择只依赖 Q，K 只进入乘积，所以压 K 不影响被测的比较逻辑。

    **第二个约束：K 必须装得进端口的位宽。** 这一条起初漏了，代价是一个
    难查的失配：端口是 SInt(4.W)（-8..7），而这里算出的上界是 16——16 被
    截成 0、9 被截成 -7，模型用完整值而 RTL 用截断值，于是只有「唯一携带
    信息的那一拍」对不上。1:4 通路端口是 SInt(6.W)（±31）装得下，所以它
    通过了，更显得像是尺寸相关的问题，其实不是。
    """
    saturation_ticks = 7 << point          # exp 在这里之后饱和
    bound = saturation_ticks // max(chain_length * query_max, 1)
    bound = max(2, min(bound, 1 << (bits // 4)))
    if operand_bits is not None:
        # 有符号端口的可表示上界，和软件的 calc_max_quant_value 一致。
        bound = min(bound, (1 << (operand_bits - 1)) - 1)
    return bound


def divider_reference(numerator: int, denominator: int,
                      bits: int, point: int) -> int:
    """流水化除法器的参照：和上游 `FixedPointDiv` 逐位一致。

    两者语义必须相同，否则「换一个除法器实现」就不是在同一条曲线上取点，
    而是换了功能。上游用 Chisel 的 `/`（SInt 除法，朝零截断）；这里用基 2
    恢复除法先算绝对值再套符号——同样朝零截断。

    除零返回 0，也和上游一致。
    """
    if denominator == 0:
        return 0
    # 被除数左移 point 位，这是定点除法的对齐。
    shifted = abs(numerator) << point
    magnitude = shifted // abs(denominator)
    negative = (numerator < 0) != (denominator < 0)
    return wrap(-magnitude if negative else magnitude, bits)


def divider_cases(bits: int, point: int, stages: int, seed: int) -> list[dict]:
    """覆盖符号组合、除零、截断方向和溢出的输入。

    每个用例是一拍输入；流水线延迟 `stages` 拍，testbench 按 out_valid 采样。
    """
    generator = torch.Generator().manual_seed(seed)
    scale = 1 << point
    limit = 1 << (bits - 1)

    named: list[tuple[str, list[tuple[int, int]]]] = [
        # 除零：唯一有明确规定的特殊值。
        ("divide_by_zero", [(scale, 0), (0, 0), (-scale, 0), (limit - 1, 0)]),
        # 精确商，肉眼可核对。
        ("exact", [(scale, scale), (2 * scale, scale), (scale, 2 * scale),
                   (-2 * scale, scale), (2 * scale, -scale), (-2 * scale, -scale)]),
        # 四种符号组合下的截断方向——朝零，不是朝负无穷。
        ("truncation", [(3, 2 * scale), (-3, 2 * scale),
                        (3, -2 * scale), (-3, -2 * scale),
                        (1, 3 * scale), (-1, 3 * scale)]),
        # 商超出输出宽度：窄化时回绕，和上游一样。
        ("overflow", [(scale, 1), (100 * scale, scale), (scale, 2), (limit - 1, 1)]),
        # 分子为零，以及分母远大于分子。
        ("small_quotient", [(0, scale), (1, limit - 1), (-1, limit - 1)]),
    ]
    noise = torch.randint(-limit, limit, (64,), generator=generator).tolist()
    named.append(("random", [(noise[i], noise[i + 1]) for i in range(0, 60, 2)]))

    cases = []
    for name, points in named:
        inputs: list[int] = []
        expected: list[int] = []
        for numerator, denominator in points:
            inputs.extend((numerator, denominator))
            expected.append(divider_reference(numerator, denominator, bits, point))
        cases.append({"name": name, "input_ticks": inputs,
                      "expected_value_ticks": expected,
                      "expected_idx": [stages]})
    return cases


def prepe_array_cases(height: int, width: int, out_bits: int, bits: int,
                      point: int, seed: int) -> list[dict]:
    """Drive the array with real (Q, K) and check it against DynaX's own Python.

    The reference is quant_qk_matmul("1_2_4bit") from
    models/utils/sparse_attention.py -- the software this accelerator exists to
    run -- not a mirror of the RTL. A mirror could only ever confirm that the
    RTL equals itself, which is why the pairing convention looked unanswerable
    until the software was used as the arbiter.

    操作数是**有符号** 4-bit（-7..7），和 DynaX 软件的
    calc_max_quant_value(4) = 2^3 - 1 = 7 对齐。

    这一点在改动前是反的：那时用非负操作数，让 torch.abs 成为恒等——
    而**正是那条限定掩盖了软件和 RTL 之间的符号分歧**。现在两边都带符号，
    这个用例才真的在检验它们算的是同一件事。

    每组内部不取等幅值：等幅时软件的 argmax 保留最小下标，RTL 的严格 `>`
    保留最大下标——那是另一个分歧，单独记录。
    """
    generator = torch.Generator().manual_seed(seed)
    cases = []
    mismatched_orders = 0

    for index in range(6):
        query: list[int] = []
        for _ in range(width // 2):
            # 幅值互不相同（避开平局），符号随机——这才覆盖真实数据的形态。
            pair = (torch.randperm(7, generator=generator)[:2] + 1).tolist()
            signs = (torch.randint(0, 2, (2,), generator=generator) * 2 - 1).tolist()
            query.extend(int(v * sgn) for v, sgn in zip(pair, signs))
        key_max = _key_bound(width // 2, 7, point, bits, operand_bits=4)
        magnitude = torch.randint(1, key_max + 1, (width,), generator=generator)
        key_signs = torch.randint(0, 2, (width,), generator=generator) * 2 - 1
        key = (magnitude * key_signs).tolist()

        model = PrePEArrayModel(height, width, out_bits, bits, point)
        plan = prepe_array_schedule(query, key, height, width, odd_first=True)
        inputs: list[int] = []
        expected: list[int] = []
        for left_in, top_in, pes_state, array_state in plan:
            inputs.extend([pes_state, array_state, *left_in, *top_in])
            expected.extend(model.step(left_in, top_in, pes_state, array_state))

        # The claim this case makes: the array reproduces the software.
        psum = software_1_2_qk(query, key, out_bits)
        want = 0 if psum == 0 else wrap(
            exp_unit_reference(psum, bits, point, 4, 4), bits
        )
        settled = expected[-height:]
        assert all(value == want for value in settled), (
            f"case {index}: array gives {settled}, software says {want}"
        )

        # And the claim it depends on: the pairing convention is not free. The
        # same Q and K fed even-element-first disagree with the software, which
        # is what makes "odd element first" a constraint rather than a guess.
        other = PrePEArrayModel(height, width, out_bits, bits, point)
        for left_in, top_in, pes_state, array_state in prepe_array_schedule(
            query, key, height, width, odd_first=False
        ):
            wrong = other.step(left_in, top_in, pes_state, array_state)
        mismatched_orders += any(value != want for value in wrong)

        cases.append({
            "name": f"qk_{index}",
            "input_ticks": inputs,
            "expected_value_ticks": expected,
            # The first cycles carry whatever the previous case left behind:
            # expRegs is a Reg the array clears only in aClear, and the s_out
            # of a cycle reflects the state before it.
            "expected_idx": [0, 0] + [1] * (len(plan) - 2),
        })

    print(f"  key bound: K in [1, {key_max}] so exp(psum) stays out of saturation")
    print(f"  pairing check: {mismatched_orders}/6 cases disagree with the "
          f"software when fed even-element-first")
    return cases
