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



def software_1_2_qk(query: list[int], key: list[int], out_bits: int) -> int:
    """What DynaX's own software says this array should compute.

    From models/utils/sparse_attention.py, quant_qk_matmul("1_2_4bit"): keep the
    larger-magnitude element of each adjacent pair along the head dimension,
    zero the other, then take the dot product with K. The accelerator exists to
    run that, so it is the reference -- not a mirror of the RTL, which could only
    ever confirm that the RTL equals itself.

    Restricted here to non-negative 4-bit operands, which makes torch.abs a
    no-op and lets the RTL's unsigned compare mean the same thing. That leaves
    exactly one thing under test: which K element each kept Q element multiplies.
    """
    total = 0
    for c in range(len(query) // 2):
        first, second = query[2 * c], query[2 * c + 1]
        kept = 2 * c if first >= second else 2 * c + 1
        total += query[kept] * key[kept]
    return total & ((1 << out_bits) - 1)


def software_1_4_qk(query: list[int], key: list[int], out_bits: int) -> int:
    """DynaX's quant_qk_matmul("1_4_6bit"): keep one of every four, by magnitude."""
    total = 0
    for c in range(len(query) // 4):
        group = query[4 * c:4 * c + 4]
        kept = 4 * c + group.index(max(group))
        total += query[kept] * key[kept]
    return total & ((1 << out_bits) - 1)
