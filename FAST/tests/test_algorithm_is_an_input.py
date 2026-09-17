"""算法是输入，不是搜索维度。

使用者给定算法（DynaX 的是动态 X:M），Agent 探索的是**它的配置**以及为这个
配置协同设计的架构。曾经搞反过：`labels()` 把 xm / nm / topk / sanger / salo
全部枚举在一起，于是 Kernel Agent 在选算法；`select_candidates` 还有一条
「先保方法族覆盖」的规则专门让候选散布到不同算法上；Critic 在算法层的变异
因此变成「换成 sanger」而不是「换一组 X:M 参数」。
"""

from __future__ import annotations

import pytest

from fast.agents.kernel import select_candidates
from fast.schemas.models import KernelMeasurement, KernelProfile, KernelSearchSpace, Status


def _profile(imbalance: float) -> KernelProfile:
    return KernelProfile(
        histogram_bins=4, row_density_histogram=(1, 1, 1, 1),
        block_density_histogram=(1, 1, 1, 1), load_imbalance=imbalance,
        column_top1_mass=0.1, column_top5_mass=0.3, column_top10_mass=0.5,
        tile_load_imbalance=((32, imbalance),),
    )


def _m(label: str, sparsity: float, imbalance: float, loss: float = 0.02) -> KernelMeasurement:
    return KernelMeasurement(
        label=label, status=Status.PASSED, perplexity=10.0, quality_loss=loss,
        actual_sparsity=sparsity, index_entropy=0.9, block_occupancy=0.5,
        row_kept_min=8.0, row_kept_max=16.0, wall_seconds=1.0,
        profile=_profile(imbalance),
    )


@pytest.mark.parametrize("algorithm", KernelSearchSpace.SEARCHABLE)
def test_the_space_only_holds_configurations_of_the_given_algorithm(algorithm):
    space = KernelSearchSpace(algorithm=algorithm)
    labels = space.labels()
    assert labels, f"{algorithm} 的配置空间不该是空的"
    assert all(label.split(":")[0] == algorithm for label in labels), labels
    # 其他算法的标签一律不在空间里——proposer 提了会在测量前被拒。
    for other in KernelSearchSpace.SEARCHABLE:
        if other == algorithm:
            continue
        for label in KernelSearchSpace(algorithm=other).labels():
            assert not space.contains(label), f"{algorithm} 的空间里出现了 {label}"


def test_the_xm_space_is_actually_a_space():
    """DynaX 自己的算法要有足够的配置可搜，否则「探索配置」是空话。"""
    assert len(KernelSearchSpace(algorithm="xm").labels()) >= 10


def test_baselines_are_not_searchable_and_say_why():
    """sanger / salo 的配置不在标签语法里，所以不能被搜——要明确失败。"""
    for baseline in KernelSearchSpace.BASELINES:
        with pytest.raises(ValueError, match="cannot search the configuration space"):
            KernelSearchSpace(algorithm=baseline)
    # 但它们仍然作为对照存在，不是被删掉了。
    assert set(KernelSearchSpace(algorithm="xm").baselines()) == set(KernelSearchSpace.BASELINES)


def test_candidates_spread_over_sparsity_and_imbalance_within_one_algorithm():
    """同一个算法内部，候选要在下游真正感受到的两个量上散开。

    稀疏度决定 cycles，tile 不均衡度决定利用率。三个候选全挤在不均衡度
    相近的地方，等于给 3 个和给 1 个没区别。
    """
    # 作业 17248126 实测的 tile(32) 值。
    accepted = (
        _m("xm:32:4:64", 0.8681, 1.576),    # 最稀疏
        _m("xm:32:8:64", 0.8576, 1.512),
        _m("xm:32:16:64", 0.8362, 1.425),
        _m("xm:32:32:64", 0.7932, 1.336),   # 最均衡，在不均衡度轴上离其余最远
    )
    picked, shortfall = select_candidates(accepted, 3)

    assert shortfall is None
    labels = [item.label for item in picked]
    # 最稀疏的必进（那是最想要的点）。
    assert labels[0] == "xm:32:4:64"
    # 最均衡的那个也要进来。
    assert "xm:32:32:64" in labels
    assert all(label.startswith("xm:") for label in labels)


def test_selection_no_longer_prefers_family_coverage():
    """族覆盖那条规则必须真的没了。

    喂一份**混了算法**的输入（跨算法枚举时代的旧报告长这样）。旧规则每族先
    拿一个，所以 count=2 必然选出两个**不同**算法。新规则按 (稀疏度, tile
    不均衡度) 散布——这里两个 xm 配置在两根轴上都拉得最开，而 nm / topk 挤
    在中间，所以两个名额都该给 xm。
    """
    accepted = (
        _m("xm:32:4:64", 0.90, 1.20),     # 最稀疏且最均衡
        _m("xm:64:16:64", 0.70, 1.90),    # 离它最远
        _m("nm:32:64", 0.80, 1.55),       # 正中间
        _m("topk:256", 0.79, 1.54),       # 也在中间
    )
    picked, _ = select_candidates(accepted, 2)

    labels = {item.label for item in picked}
    assert labels == {"xm:32:4:64", "xm:64:16:64"}, labels
    # 两个都是同一个算法——旧的族覆盖规则不可能给出这个结果。
    assert len({label.split(":")[0] for label in labels}) == 1


def test_a_fallback_imbalance_is_not_treated_as_a_measurement():
    """`tile_load_imbalance` 缺失时不能拿全局 `load_imbalance` 顶替。

    两者差 1.9-2.5 倍而且**排序不同**：作业 17248126 实测，按全局
    `xm:32:32:64` 排第 4，按 tile(32) 排第 2。旧报告的这个字段是 None，
    于是整整一轮归因、一条换候选规则和两份文档里的数字，都把回退值当成了
    实测 tile 不均衡度。
    """
    from fast.agents.critic import _tile_imbalance
    from fast.agents.kernel import _imbalance_of
    from fast.agents.llm_critic import _imbalance

    bare = KernelProfile(
        histogram_bins=4, row_density_histogram=(1, 1, 1, 1),
        block_density_histogram=(1, 1, 1, 1), load_imbalance=2.666,
        column_top1_mass=0.1, column_top5_mass=0.3, column_top10_mass=0.5,
        tile_load_imbalance=(),          # 没测
    )
    item = _m("xm:32:16:64", 0.8362, 1.425)
    unmeasured = KernelMeasurement(
        label="xm:32:16:64", status=Status.PASSED, perplexity=10.0, quality_loss=0.02,
        actual_sparsity=0.8362, index_entropy=0.9, block_occupancy=0.5,
        row_kept_min=8.0, row_kept_max=16.0, wall_seconds=1.0, profile=bare,
    )

    # 兼容读老报告的那个入口仍然退回，但**明确标出来**这是退回。
    assert bare.tile_imbalance_for(32) == pytest.approx(2.666)
    assert bare.tile_imbalance_measured(32) is None

    # 做决策 / 喂模型的三个入口一律不接受回退值。
    assert _tile_imbalance(unmeasured) is None
    assert _imbalance_of(unmeasured) == 0.0
    assert _imbalance(unmeasured) == "not measured"
    # 有实测时照常给。
    assert _tile_imbalance(item) == pytest.approx(1.425)
    assert _imbalance(item) == "1.425"
