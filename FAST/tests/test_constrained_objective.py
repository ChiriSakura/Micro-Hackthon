"""ε 是**可行域**，不是目标函数。

真实运行（作业 17299021）里循环第 0 轮就把全程最好的点换掉了，理由是
「quality loss of +0.0271 is unacceptable」——而 ε = 0.05，+0.0271 是**满足
约束**的。被换掉的那个快一倍：

    轮0  xm:32:4:64   稀疏度 0.8681  延迟 29,522 ns  功耗 680.7 mW
    轮1  xm:64:16:64  稀疏度 0.7209  延迟 61,606 ns  功耗 689.8 mW

同样硬件（16x16 q=2），差别全在 kernel 配置：稀疏度高 → cycles 少 → 延迟低。
轮 0 在两根轴上都更好，支配了后面全部三轮。

按利用率排看不出来（0.839 < 0.850，会认为换对了）——**是延迟这根轴把它翻
过来的**。
"""

from __future__ import annotations

import pytest

from fast.agents.codesign import DesignObjectives, constraint_violations, dominates
from fast.agents.llm_critic import CRITIC_PROMPT
from fast.schemas.models import ArchSpecs


def _point(latency_ns, power_mw, area=1_649_532.0, clock=2.528):
    return DesignObjectives(latency_ns=latency_ns, power_mw=power_mw, area_um2=area,
                            throughput_mac_per_s=None, clock_ns=clock)


def test_the_abandoned_configuration_dominated_its_replacement():
    """这是那次真实运行的两个点。"""
    kept = _point(29_522, 680.7)      # xm:32:4:64，被换掉的
    chosen = _point(61_606, 689.8)    # xm:64:16:64，换过去的
    assert dominates(kept, chosen)
    assert not dominates(chosen, kept)


def test_accuracy_is_not_one_of_the_objectives():
    """支配关系只看 (延迟, 功耗)。精度是约束，不进目标向量。"""
    assert not hasattr(_point(1.0, 1.0), "quality_loss")
    # 精度更好但延迟更差的点，不该因为"精度更好"就不被支配。
    assert dominates(_point(100, 100), _point(200, 100))


@pytest.mark.parametrize("loss,epsilon,feasible", [
    (0.0271, 0.05, True),    # 那次被判成 "unacceptable" 的点
    (0.0008, 0.05, True),
    (0.0600, 0.05, False),
])
def test_epsilon_is_a_binary_gate(loss, epsilon, feasible):
    """门内的点彼此**同样可接受**——0.0271 和 0.0008 在可行性上没有差别。"""
    assert (loss <= epsilon) is feasible


def test_the_prompt_states_the_formulation_and_the_gate():
    """模型必须看到「什么是目标、什么只是可行域」。"""
    body = CRITIC_PROMPT.format(
        algorithm="xm", epsilon="0.0500", max_area="2,800,000 um^2",
        max_power="not given", min_mhz="350 MHz",
        method="xm:32:4:64", sparsity=0.8681, loss=0.0271, menu="m",
        plan="p", p_cycles="1", p_area="1", p_power="1", p_clock="1",
        hardware="h", fidelity="L2-rtl-simulation", measured="x", history="h",
    )
    assert "constrained optimisation" in body.lower()
    assert "GATE, not a score" in body
    assert "EQUALLY ACCEPTABLE" in body
    # 真实的反例要在 prompt 里，光讲道理不够。
    assert "29,522" in body and "61,606" in body
    # 约束值要真的填进去，不是占位符。
    assert "2,800,000 um^2" in body and "0.0500" in body


def test_a_missing_budget_is_reported_as_not_given():
    """不给功耗预算就说 not given——**不要编一个默认值**，模型会去优化一个
    没人要求的东西。"""
    specs = ArchSpecs()
    assert specs.max_power_mw is None
    assert constraint_violations(_point(1000, 9_999_999.0), specs) == ()
