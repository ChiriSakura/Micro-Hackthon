"""为阵列 testbench 生成端口访问代码。

只生成机械的那一半。Chisel 把 `Vec(N)` 展平成 `io_x_0 .. io_x_{N-1}`，
`Vec(M, Vec(N))` 展平成 `io_x_i_j`——DynaX-L 的 RePEArray 是 64×8，
光 `sel_cols` 就有 512 个端口，手写既写不完也读不出问题。

testbench 的**逻辑**仍然手写：驱动顺序、采样时机、和参照比什么，
那些是需要被人审的部分。这里生成的只有尺寸常量和 drive/read 两个函数。

    python tb/gen_ports.py --module RePEArray --rows 64 --pes 8 \
        --reg-width 16 --out array_ports.h

生成的头文件定义：
    kNumRows / kPePerRow / kRegWidth  尺寸常量
    kFieldsPerCycle                   每周期输入字段数（与 golden 的编码一致）
    drive(DUT*, const long*)          按 golden 的字段顺序驱动全部输入
    row_out(DUT*, int)                读一行的输出
"""

from __future__ import annotations

import argparse
from pathlib import Path


def _mask(bits: int) -> str:
    return f"0x{(1 << bits) - 1:X}"


def _cast(bits: int) -> str:
    """Verilator 按位宽选择 C 类型：<=8 位 CData，<=16 位 SData，<=32 位 IData。"""
    if bits <= 8:
        return "unsigned char"
    if bits <= 16:
        return "unsigned short"
    return "unsigned int"


def _signed_read(bits: int, expr: str) -> str:
    return f"(short)(unsigned short){expr}" if bits <= 16 else f"(int){expr}"


def repe_array(rows: int, pes: int, reg_width: int, data_bits: int) -> str:
    """RePEArray：clr, acc_ctrl, exp_ctrl, q_left_vec[R], regs_top[W], sel_cols[R][P]"""
    lines = [
        f"constexpr int kNumRows = {rows};",
        f"constexpr int kPePerRow = {pes};",
        f"constexpr int kRegWidth = {reg_width};",
        "// clr, acc_ctrl, exp_ctrl, then q_left_vec[R], regs_top[W], sel_cols[R][P]",
        "constexpr int kFieldsPerCycle ="
        " 3 + kNumRows + kRegWidth + kNumRows * kPePerRow;",
        "",
        "inline void drive(VRePEArray* dut, const long* fields) {",
        "    dut->io_clr = (unsigned char)(fields[0] & 1);",
        "    dut->io_acc_ctrl = (unsigned char)fields[1];",
        "    dut->io_exp_ctrl = (unsigned char)fields[2];",
        "",
        "    const long* q = fields + 3;",
    ]
    cast, mask = _cast(data_bits), _mask(data_bits)
    for r in range(rows):
        lines.append(f"    dut->io_q_left_vec_{r} = ({cast})(q[{r}] & {mask});")
    lines += ["", "    const long* tops = fields + 3 + kNumRows;"]
    for i in range(reg_width):
        lines.append(f"    dut->io_regs_top_{i} = ({cast})(tops[{i}] & {mask});")
    lines += ["", "    const long* sel = fields + 3 + kNumRows + kRegWidth;"]
    for r in range(rows):
        for p in range(pes):
            lines.append(
                f"    dut->io_sel_cols_{r}_{p} = (unsigned char)sel[{r * pes + p}];"
            )
    lines += ["}", "", "inline long row_out(VRePEArray* dut, int row) {",
              "    switch (row) {"]
    for r in range(rows):
        expr = _signed_read(data_bits, f"dut->io_rows_adder_out_{r}")
        lines.append(f"        case {r}: return {expr};")
    lines += ["        default: return 0;", "    }", "}"]
    return "\n".join(lines)


def prepe_array(height: int, width: int, operand_bits: int, cls: str) -> str:
    """PrePEArray：pes_state, array_state, left_in[H], top_in[W]"""
    lines = [
        f"constexpr int kHeight = {height};",
        f"constexpr int kWidth = {width};",
        "// pes_state, array_state, then left_in[H], top_in[W]",
        "constexpr int kFieldsPerCycle = 2 + kHeight + kWidth;",
        "",
        f"inline void drive(V{cls}* dut, const long* fields) {{",
        "    dut->io_pes_state = (unsigned char)fields[0];",
        "    dut->io_array_state = (unsigned char)fields[1];",
        "",
        "    const long* left = fields + 2;",
    ]
    mask = _mask(operand_bits)
    for i in range(height):
        lines.append(f"    dut->io_left_in_{i} = (unsigned char)(left[{i}] & {mask});")
    lines += ["", "    const long* top = fields + 2 + kHeight;"]
    for i in range(width):
        lines.append(f"    dut->io_top_in_{i} = (unsigned char)(top[{i}] & {mask});")
    lines += ["}", "", f"inline long score(V{cls}* dut, int row) {{", "    switch (row) {"]
    for i in range(height):
        lines.append(
            f"        case {i}: return (short)(unsigned short)dut->io_s_out_{i};"
        )
    lines += ["        default: return 0;", "    }", "}"]
    return "\n".join(lines)


def block_scheduler(rows: int, pes: int, queue_depth: int, col_bits: int) -> str:
    """BlockScheduler：enq_valid[R], enq_cols[R][P], enq_active[R][P]

    入队是每行并行的（每个 query 行有自己的 TopK），所以 32x4 就有 256 个
    enq_cols 端口、64x8 有 512 个——正是这个生成器存在的理由。

    读出侧只用打包好的 `row_busy_bits` / `enq_ready_bits` 和计数器，不展开：
    利用率测量只关心占用，不关心列索引，少展开一半端口就少一半写错的机会。
    """
    lines = [
        f"constexpr int kNumRows = {rows};",
        f"constexpr int kPeCount = {pes};",
        f"constexpr int kQueueDepth = {queue_depth};",
        "",
        "inline void set_enq_valid(VBlockScheduler* dut, int row, int v) {",
        "    switch (row) {",
    ]
    for r in range(rows):
        lines.append(f"        case {r}: dut->io_enq_valid_{r} = (unsigned char)v; return;")
    lines += ["        default: return;", "    }", "}", "",
              "inline int get_enq_valid(VBlockScheduler* dut, int row) {",
              "    switch (row) {"]
    for r in range(rows):
        lines.append(f"        case {r}: return dut->io_enq_valid_{r};")
    lines += ["        default: return 0;", "    }", "}", ""]

    cast = _cast(col_bits)
    lines += ["inline void set_enq_col(VBlockScheduler* dut, int row, int pe, int v) {",
              "    switch (row * kPeCount + pe) {"]
    for r in range(rows):
        for q in range(pes):
            lines.append(
                f"        case {r * pes + q}: dut->io_enq_cols_{r}_{q} = ({cast})v; return;")
    lines += ["        default: return;", "    }", "}", "",
              "inline void set_enq_active(VBlockScheduler* dut, int row, int pe, int v) {",
              "    switch (row * kPeCount + pe) {"]
    for r in range(rows):
        for q in range(pes):
            lines.append(
                f"        case {r * pes + q}: dut->io_enq_active_{r}_{q} = (unsigned char)v; return;")
    lines += ["        default: return;", "    }", "}", "",
              "inline void set_enq_last(VBlockScheduler* dut, int row, int v) {",
              "    switch (row) {"]
    for r in range(rows):
        lines.append(f"        case {r}: dut->io_enq_last_{r} = (unsigned char)v; return;")
    lines += ["        default: return;", "    }", "}", "",
              "inline unsigned long long enq_ready_bits(VBlockScheduler* dut) {",
              "    return (unsigned long long)dut->io_enq_ready_bits;", "}", "",
              "inline unsigned long long row_busy_bits(VBlockScheduler* dut) {",
              "    return (unsigned long long)dut->io_row_busy_bits;", "}"]
    return "\n".join(lines)


def key_feeder(reg_width: int, bank_count: int, col_bits: int, data_bits: int) -> str:
    """KeyFeeder：req_cols[W], req_active[W], out_cols[W]

    只展开这三组。写口和计数器是标量端口，testbench 直接访问。
    """
    lines = [
        f"constexpr int kRegWidth = {reg_width};",
        f"constexpr int kBankCount = {bank_count};",
        "",
        "inline void set_req_col(VKeyFeeder* dut, int slot, int v) {",
        "    switch (slot) {",
    ]
    cast = _cast(col_bits)
    for i in range(reg_width):
        lines.append(f"        case {i}: dut->io_req_cols_{i} = ({cast})v; return;")
    lines += ["        default: return;", "    }", "}", "",
              "inline void set_req_active(VKeyFeeder* dut, int slot, int v) {",
              "    switch (slot) {"]
    for i in range(reg_width):
        lines.append(f"        case {i}: dut->io_req_active_{i} = (unsigned char)v; return;")
    lines += ["        default: return;", "    }", "}", "",
              "inline int out_col(VKeyFeeder* dut, int slot) {",
              "    switch (slot) {"]
    for i in range(reg_width):
        lines.append(f"        case {i}: return (int)(unsigned short)dut->io_out_cols_{i};")
    lines += ["        default: return 0;", "    }", "}"]
    return "\n".join(lines)


def attention_tile(tile_q: int, tile_k: int, head_dim: int,
                   kept: int, pe: int, data_bits: int) -> str:
    """AttentionTile：随 tileQ / keptPerRow / peCountPerRow 三个尺寸变的端口。

    手写的版本把 `setExtIdx` 展开到 8 个 case 加一个 `default` ——kept=16 时
    第 8-15 项会**全部写进端口 7**，而且不会有任何东西报错：索引装错了，
    算出来的是另一组保留列的注意力，数字看起来完全正常。

    论文尺寸 kept=16 / pe=4 必然踩到这个。
    """
    col_bits = max(1, (tile_k - 1).bit_length())
    lines = [
        f"constexpr int kTileQ = {tile_q};",
        f"constexpr int kTileK = {tile_k};",
        f"constexpr int kHeadDim = {head_dim};",
        f"constexpr int kKept = {kept};",
        f"constexpr int kPe = {pe};",
        f"constexpr int kPasses = ({kept} + {pe} - 1) / {pe};",
        "",
    ]
    cast = _cast(data_bits)

    def switch(name, count, body, ret=None):
        out = [f"inline {'long' if ret else 'void'} {name} {{", "    switch (index) {"]
        for i in range(count):
            out.append("        case %d: %s" % (i, body(i)))
        out.append(f"        default: {'return 0;' if ret else 'return;'}")
        out += ["    }", "}", ""]
        return out

    lines += switch(
        "setExecuteQ(VAttentionTile* dut, int index, int v)", tile_q,
        lambda i: f"dut->io_execute_q_{i} = ({cast})v; return;")
    lines += switch(
        "setExecuteCol(VAttentionTile* dut, int index, int v)", pe,
        lambda i: f"dut->io_execute_cols_{i} = ({cast})v; return;")
    lines += switch(
        "setExtIdx(VAttentionTile* dut, int index, int idx, int valid)", kept,
        lambda i: (f"dut->io_sched_ext_idx_{i} = ({_cast(col_bits)})idx; "
                   f"dut->io_sched_ext_valid_{i} = (unsigned char)valid; return;"))
    lines += switch(
        "rowSum(VAttentionTile* dut, int index)", tile_q,
        lambda i: f"return {_signed_read(data_bits, f'dut->io_execute_row_sum_{i}')};",
        ret=True)
    lines += switch(
        "outValue(VAttentionTile* dut, int index)", tile_q,
        lambda i: f"return {_signed_read(data_bits, f'dut->io_out_{i}')};", ret=True)
    lines += switch(
        "setNorm(VAttentionTile* dut, int index, int num, int den)", tile_q,
        lambda i: (f"dut->io_norm_numerator_{i} = ({cast})num; "
                   f"dut->io_norm_denominator_{i} = ({cast})den; return;"))
    lines += switch(
        "predictScore(VAttentionTile* dut, int index)", tile_q,
        lambda i: f"return {_signed_read(data_bits, f'dut->io_predict_score_{i}')};",
        ret=True)
    # 预测通路。这几个原来也是手写的，而且把「行 * 8 + k」写死了——
    # kept=16 时索引全错，静默地读到另一个 lane。
    lines += switch(
        "setPredictQ(VAttentionTile* dut, int index, int v)", tile_q,
        lambda i: f"dut->io_predict_q_{i} = (unsigned char)v; return;")
    lines += switch(
        "setPredictK(VAttentionTile* dut, int index, int v)", head_dim,
        lambda i: f"dut->io_predict_k_{i} = (unsigned char)v; return;")
    lines += switch(
        "setSelectIn(VAttentionTile* dut, int index, int v)", tile_q,
        lambda i: f"dut->io_select_in_{i} = ({cast})v; return;")

    # Vec(tileQ, Vec(kept)) 展平成 io_x_row_k。
    for name, port, ret_cast in (
        ("selectIdx", "io_select_idx", "(long)"),
        ("selectValid", "io_select_valid", "(long)"),
    ):
        lines += [f"inline long {name}(VAttentionTile* dut, int row, int k) {{",
                  f"    switch (row * {kept} + k) {{"]
        for r in range(tile_q):
            for kk in range(kept):
                lines.append(
                    f"        case {r * kept + kk}: return {ret_cast}dut->{port}_{r}_{kk};")
        lines += ["        default: return 0;", "    }", "}", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", required=True,
                        choices=["RePEArray", "PrePEArray_1_2", "PrePEArray_1_4",
                                 "BlockScheduler", "KeyFeeder", "AttentionTile"])
    parser.add_argument("--rows", type=int, default=4, help="RePEArray numRows")
    parser.add_argument("--pes", type=int, default=2, help="RePEArray peCountPerRow")
    parser.add_argument("--reg-width", type=int, default=4)
    parser.add_argument("--height", type=int, default=2, help="PrePEArray height")
    parser.add_argument("--width", type=int, default=8, help="PrePEArray width")
    parser.add_argument("--data-bits", type=int, default=16)
    parser.add_argument("--queue-depth", type=int, default=0, help="BlockScheduler queueDepth")
    parser.add_argument("--col-bits", type=int, default=6, help="log2(blockM)")
    parser.add_argument("--reg-width2", type=int, default=8, help="KeyFeeder regWidth")
    parser.add_argument("--banks", type=int, default=8, help="KeyFeeder bankCount")
    parser.add_argument("--tile-q", type=int, default=4)
    parser.add_argument("--tile-k", type=int, default=32)
    parser.add_argument("--head-dim", type=int, default=8)
    parser.add_argument("--kept", type=int, default=8)
    parser.add_argument("--pe", type=int, default=8)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    if args.module == "AttentionTile":
        body = attention_tile(args.tile_q, args.tile_k, args.head_dim,
                              args.kept, args.pe, args.data_bits)
        header = (f"AttentionTile tileQ={args.tile_q} tileK={args.tile_k} "
                  f"headDim={args.head_dim} kept={args.kept} pe={args.pe}")
    elif args.module == "KeyFeeder":
        body = key_feeder(args.reg_width2, args.banks, args.col_bits, args.data_bits)
        header = (f"KeyFeeder regWidth={args.reg_width2}, banks={args.banks}, "
                  f"colBits={args.col_bits}")
    elif args.module == "BlockScheduler":
        body = block_scheduler(args.rows, args.pes, args.queue_depth, args.col_bits)
        header = (f"BlockScheduler {args.rows}x{args.pes}, "
                  f"queueDepth={args.queue_depth}, colBits={args.col_bits}")
    elif args.module == "RePEArray":
        body = repe_array(args.rows, args.pes, args.reg_width, args.data_bits)
        header = f"RePEArray {args.rows}x{args.pes}, regWidth={args.reg_width}"
    else:
        operand_bits = 4 if args.module == "PrePEArray_1_2" else 6
        body = prepe_array(args.height, args.width, operand_bits, args.module)
        header = f"{args.module} height={args.height} width={args.width}"

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        f"// 由 tb/gen_ports.py 生成，请勿手改。\n"
        f"// 配置：{header}\n"
        f"//\n"
        f"// Chisel 把 Vec 展平成带下标的独立端口，所以这些访问只能按尺寸展开。\n"
        f"// testbench 的逻辑在对应的 .cpp 里，那部分是手写的。\n"
        f"#pragma once\n\n{body}\n",
        encoding="utf-8",
    )
    print(f"wrote {header} -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
