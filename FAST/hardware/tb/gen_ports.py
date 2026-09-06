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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", required=True,
                        choices=["RePEArray", "PrePEArray_1_2", "PrePEArray_1_4"])
    parser.add_argument("--rows", type=int, default=4, help="RePEArray numRows")
    parser.add_argument("--pes", type=int, default=2, help="RePEArray peCountPerRow")
    parser.add_argument("--reg-width", type=int, default=4)
    parser.add_argument("--height", type=int, default=2, help="PrePEArray height")
    parser.add_argument("--width", type=int, default=8, help="PrePEArray width")
    parser.add_argument("--data-bits", type=int, default=16)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    if args.module == "RePEArray":
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
