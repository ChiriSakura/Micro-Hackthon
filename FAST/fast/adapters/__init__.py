"""后端边界：同一个协议，不同的保真度与执行位置。

    base.py           Kernel / Evaluator 的后端协议（Protocol）
    deterministic.py  L0：合成数据，秒级，只验证控制流
    dynax.py          Kernel：调用真实 DynaX 测量（可经 Slurm / 远端 worker）
    analytical.py     L1：一阶代价模型——**自己声明它不独立**
    verilator.py      L2：真实 RTL 仿真——**它可以反对**

`analytical` 和 `verilator` 的关系是这个项目的方法论核心：前者和协同优化器
共用同一个代价模型，所以它不可能反对自己选中的设计；后者跑独立参照，
六个 DynaX 缺陷就是这么找出来的。两者都会把自己的性质写进 evidence。
"""

from fast.adapters.base import EvaluationAdapter, KernelAdapter
from fast.adapters.analytical import AnalyticalEvaluationAdapter
from fast.adapters.deterministic import DeterministicEvaluationAdapter, DeterministicKernelAdapter
from fast.adapters.dynax import DynaXKernelAdapter

__all__ = [
    "AnalyticalEvaluationAdapter",
    "DeterministicEvaluationAdapter",
    "DeterministicKernelAdapter",
    "DynaXKernelAdapter",
    "EvaluationAdapter",
    "KernelAdapter",
]
