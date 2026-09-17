"""动态 X:M 的阈值：从软件的尺度换算到硬件比较的尺度。

## 两边比的不是同一个量

软件 `gen_sparsity_mask_xm` 里：

    sum_m = sum(block_probs) * token_len / m

即把块内概率和**放大到「整行都按这个密度」的尺度**，再和
`threshold_0 = 1.0` / `threshold_1 = 0.1` 比。放大因子 `token_len / m` 是
一行里有几个 block。

硬件 `BlockTierSelect` 比的是 `PrePEArray` 现成的 exp 和——**没有那个放大**。
加一个乘法器只为做一次标量缩放是浪费，而阈值本来就是标定出来的常数，
所以缩放折进阈值：

    hw_threshold = sw_threshold * m / token_len

这个模块把那句话变成可验证的代码。之前它只是 Chisel 里的一句注释，
而「注释里的声称」和「代码里的行为」是两回事。

## 还有一层：softmax 归一化

软件的 `sum_m` 是在 **softmax 之后**的概率上算的，而硬件的 exp 和是
**未归一化**的 exp 值之和。两者差一个整行的 exp 总和：

    prob_block_sum = exp_block_sum / exp_row_sum

硬件在分档那一刻还没有 `exp_row_sum`（它要等整行扫完）。所以严格对齐需要
**两趟**：先扫一遍求和，再分档。当前实现是单趟的，意味着硬件比的是未归一化
的量——`hardware_is_exact()` 会如实说这一点，不要让它看起来像对齐了。
"""

from __future__ import annotations

from dataclasses import dataclass


#: DynaX `run_eval_matrix.py` 里的默认值。
SOFTWARE_THRESHOLD_HIGH = 1.0
SOFTWARE_THRESHOLD_LOW = 0.1


@dataclass(frozen=True)
class TierThresholds:
    """硬件 `BlockTierSelect` 要的两个阈值，以及它们怎么来的。"""

    hardware_high: float
    hardware_low: float
    software_high: float
    software_low: float
    blocks_per_row: int
    #: 硬件比的是未归一化的 exp 和。True 只在硬件也做了 softmax 归一化时成立。
    normalised: bool = False

    def hardware_is_exact(self) -> bool:
        """硬件的比较是否和软件严格等价。

        **当前恒为 False**：硬件在分档那一刻还没有整行的 exp 总和（它要等
        整行扫完），所以比的是未归一化的量。严格对齐需要两趟。说出来，
        不要让「换算过了」看起来像「对齐了」。
        """
        return self.normalised


def thresholds_for(
    *, token_len: int, block_m: int,
    software_high: float = SOFTWARE_THRESHOLD_HIGH,
    software_low: float = SOFTWARE_THRESHOLD_LOW,
) -> TierThresholds:
    """把软件阈值折算到硬件比较的尺度。

    Args:
        token_len: 一行有多少个 key（软件里的 `token_len`）。
        block_m: 一个 block 多宽（软件里的 `m`）。

    Raises:
        ValueError: `token_len` 不是 `block_m` 的整数倍——软件侧同样拒绝，
            因为 reshape 会失败。
    """
    if block_m <= 0 or token_len <= 0:
        raise ValueError(f"token_len={token_len} block_m={block_m} 必须为正")
    if token_len % block_m:
        raise ValueError(
            f"X:M 要求 token_len 能被 m 整除，收到 token_len={token_len} m={block_m}")
    blocks = token_len // block_m
    return TierThresholds(
        hardware_high=software_high / blocks,
        hardware_low=software_low / blocks,
        software_high=software_high,
        software_low=software_low,
        blocks_per_row=blocks,
    )


def keep_for_mass(mass: float, thresholds: TierThresholds, *, n1: int, n2: int) -> int:
    """给定块质量，这一块留几个。**比较顺序与软件的两次 `torch.where` 一致。**

    软件是：先按 lo 判丢弃，再用 hi 覆盖成高档——等价于「hi 优先」。
    写反了会让一个质量很高的块在 lo 那一步被判丢弃之后再也回不来。
    """
    if mass > thresholds.hardware_high:
        return n1
    if mass < thresholds.hardware_low:
        return 0
    return n2
