"""DynaX 自己的 Python，作为预测单元的判据。

镜像 RTL 的参照永远答不了「接口约定是不是接反了」——它只能证明 RTL 等于
它自己。判据必须是这个加速器**存在的目的**：
`DynaX/models/utils/sparse_attention.py` 里的 `quant_qk_matmul`。

这两个函数是它的整数复现，限定在非负操作数上（让 `torch.abs` 成为恒等，
RTL 的无符号比较才和软件的 `argmax(abs)` 同义）。

用它定下来的事：预测阵列里**选择索引的顺序和到达顺序相反**，所以每组
必须按下标降序喂。1:2 和 1:4 是同一条规则，源码在哪条上都没写。
"""

from __future__ import annotations

from golden.fixedpoint import wrap



def software_1_2_qk(query: list[int], key: list[int], out_bits: int) -> int:
    """What DynaX's own software says this array should compute.

    From models/utils/sparse_attention.py, quant_qk_matmul("1_2_4bit"): keep the
    larger-magnitude element of each adjacent pair along the head dimension,
    zero the other, then take the dot product with K. The accelerator exists to
    run that, so it is the reference -- not a mirror of the RTL, which could only
    ever confirm that the RTL equals itself.

    操作数是**有符号**的，和 calc_max_quant_value(4) = ±7 对齐。

    这里曾经限定非负操作数（让 torch.abs 成为恒等）——**正是那条限定掩盖了
    软件和 RTL 之间的符号分歧**：软件按 sum(q*k) 排序，上游 RTL 按
    sum(|q|*|k|) 排序，而非负输入下两者恰好相同。RTL 现已改为有符号，
    这个参照也随之恢复成软件真正的语义。
    """
    total = 0
    for c in range(len(query) // 2):
        first, second = query[2 * c], query[2 * c + 1]
        # 选谁：按**幅值**（argmax(abs)）。乘什么：**带符号**的那个值。
        # 这两件事分开，正是这次 RTL 改动的要点。
        kept = 2 * c if abs(first) >= abs(second) else 2 * c + 1
        total += query[kept] * key[kept]
    return wrap(total, out_bits)


def software_1_4_qk(query: list[int], key: list[int], out_bits: int) -> int:
    """DynaX 的 quant_qk_matmul("1_4_6bit")：每四个按幅值保留一个。

    和 1:2 版本同样的两件事分开：
      选谁   —— 按**幅值**（argmax(abs)）
      乘什么 —— **带符号**的那个值

    这里曾经写成 `group.index(max(group))`：对非负输入而言 max 就是
    argmax(abs)，所以它一直「对」——直到操作数带上符号。那正是掩盖了
    软件与 RTL 符号分歧的同一类限定。
    """
    total = 0
    for c in range(len(query) // 4):
        group = query[4 * c:4 * c + 4]
        kept = 4 * c + max(range(4), key=lambda i: abs(group[i]))
        total += query[kept] * key[kept]
    return wrap(total, out_bits)
