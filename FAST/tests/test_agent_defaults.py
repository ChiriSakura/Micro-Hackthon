"""两个「默认值悄悄骗人」的回归测试。

这类 bug 的共同形状：**没有任何东西会报错**。字段有默认值、参数有默认值，
流水线照常跑完，出来的数字看起来完全正常——只是它描述的不是被测的那个东西。
所以只能靠测试把「默认值必须和实测一致」这条钉住。
"""

from __future__ import annotations

import pytest

from fast.adapters.deterministic import DeterministicKernelAdapter
from fast.agents.templates import (
    ARRAY_CRITICAL_PATH_NS,
    gather_slowdown,
    queue_critical_path_ns,
    sram_area_units,
)
from fast.agents.uarch import TemplateRecord, UArchAgent, sram_for_schedule
from fast.schemas.models import (
    Budget,
    CompilerSchedule,
    ExperimentSpec,
    KernelSearchSpace,
    Status,
)


def _spec(method: str = "nm") -> ExperimentSpec:
    return ExperimentSpec(
        experiment_id="e", candidate_id="c", model="m", dataset="wikitext",
        sequence_length=512, sparsity_x=16, sparsity_m=64, epsilon=0.05, seed=0,
        budget=Budget(max_evaluations=1), sparse_method=method,
    )


def _schedule(tile_q=64, tile_k=64, tile_d=32) -> CompilerSchedule:
    return CompilerSchedule(
        status=Status.PASSED, tile_q=tile_q, tile_k=tile_k, tile_d=tile_d,
        loop_order=("q", "k", "d"), data_layout="blocked-qkd", parallelism=8,
        predicted_utilization=0.9, predicted_bytes=4096,
    )


# --- bug 1：sparse_method 从来没被填上 ---------------------------------------

def test_the_kernel_result_carries_the_method_it_measured():
    """`KernelResult.sparse_method` 有默认值 "xm"，而没有 adapter 去填它。

    后果是下游的 `gather_slowdown()` 对每个 kernel 都查 xm 那一行——而 xm
    恰好是实测里最差的一档（8 bank 下 2.14x，而 nm 是 1.19x）。**每个候选
    都被按最坏情况计价，而且不会有任何东西报错。**
    """
    result = DeterministicKernelAdapter().evaluate(_spec("nm"))
    assert result.sparse_method == "nm"
    assert gather_slowdown(8, result.sparse_method) < gather_slowdown(8, "xm")


def test_every_legal_label_resolves_to_a_measured_bank_conflict_cost():
    """搜索空间里的每个标签都要能查到一个减速值。

    `gather_slowdown` 按前缀匹配（"xm:16:8:64" -> "xm"）。空间里出现一个
    解析不出族的标签时，它会静默退回 xm——所以这条要保证退回是**刻意的**
    （salo 没有实测点），不是拼写导致的。
    """
    # 空间现在按**输入的算法**限定（算法是输入不是搜索维度），所以要把
    # 每个可搜索算法各建一次，再加上只能整体跑的基线。
    families = {
        label.split(":")[0]
        for algorithm in KernelSearchSpace.SEARCHABLE
        for label in KernelSearchSpace(algorithm=algorithm).labels()
    } | set(KernelSearchSpace.BASELINES)
    measured = {"xm", "nm", "topk", "sanger"}
    # salo 没有实测点，按文档退回 xm 的保守值；其余必须命中自己的那一行。
    assert families - measured == {"salo"}
    for family in measured:
        assert gather_slowdown(8, family) == pytest.approx(
            gather_slowdown(8, f"{family}:1:2:3"), abs=1e-9
        ), f"{family} 的前缀解析不一致"


# --- bug 2：µArch 的默认值和实测矛盾 -----------------------------------------

def test_the_default_queue_depth_is_not_past_the_clock_crossover():
    """默认深度不能落在「调度器夺走系统时钟」的那一侧。

    实测：深度 8 的工作队列关键路径 3.140 ns > 阵列的 2.23 ns，41% 的时钟
    惩罚换来的利用率是 0.864 -> 0.867。按「利用率/周期」算深度 8 比完全
    不装队列还差。默认值原本就是 8。
    """
    candidate = UArchAgent((TemplateRecord("t", "d", "uri", True),)).run(
        _schedule(), template_id="t"
    )
    assert queue_critical_path_ns(32, 4, candidate.queue_depth) <= ARRAY_CRITICAL_PATH_NS * 1.2
    assert queue_critical_path_ns(32, 4, 8) > ARRAY_CRITICAL_PATH_NS


def test_the_sram_is_sized_from_the_schedule_not_from_a_magic_number():
    """SRAM 容量要按调度推导，不能写死。

    原来写死 262144（256 KB），而 CompilerAgent 发出的 64/64/32 调度只需要
    12,288 字节——21 倍。SRAM 现在是实测计价的：256 KB 是 1,049,989 um^2，
    64 KB 是 262,497，**差得比整个 RePEArray_S（372,000）还多**。
    """
    # 64/64/32 -> (64 + 2*64) * 32 * 2 = 12,288 字节
    small = sram_for_schedule(_schedule(64, 64, 32), data_width=16)
    # 256/256/64 -> (256 + 2*256) * 64 * 2 = 98,304 字节，装不下 64 KB
    large = sram_for_schedule(_schedule(256, 256, 64), data_width=16)

    assert small == 65_536
    assert large == 131_072
    assert sram_area_units(262_144) - sram_area_units(small) > 372_000


def test_a_schedule_too_large_for_any_choice_is_not_silently_inflated():
    """装不下最大档位时返回最大档位，让 `violations()` 去明确报错。

    在这里悄悄放大容量，会让「working set 超了」这个真实约束消失，
    而代价（面积）却照收。
    """
    huge = sram_for_schedule(_schedule(4096, 4096, 512), data_width=16)
    assert huge == 262_144


def test_the_failure_path_still_reports_a_concrete_capacity():
    """模板没过验证门时也要给出具体容量。

    返回 None 会让下游拿它去算面积时炸在离原因很远的地方。
    """
    agent = UArchAgent((TemplateRecord("t", "d", "uri", False),))
    candidate = agent.run(_schedule(), template_id="t")

    assert candidate.status is Status.FAILED
    assert isinstance(candidate.sram_bytes, int) and candidate.sram_bytes > 0
