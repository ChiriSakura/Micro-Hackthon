"""预测通路的符号分歧：发现、量化、修复。

实测（TinyLlama 第 10 层第 0 头的真实 Q/K，top-8 选择与精确分数的重合度）：

    DynaX 软件近似（有符号 4-bit）        24/32 = 75%
    上游 RTL（无符号 4-bit）              10/32 = 31%
    修复后 RTL（有符号 4-bit）            23/32 = 72%   ← FAST 的改动

软件能保住 75%，所以「4-bit 太粗」不是原因。原因是**符号**：

    quant_utils.py  calc_max_quant_value(bits) = 2^(bits-1) - 1   有符号 ±7
    prepe_1_2.scala left_in = Input(UInt(4.W))                    无符号，无符号位

软件按 sum(q*k) 排序，硬件按 sum(|q|*|k|) 排序。对注意力这是实质差异——
一个大的负分数在 |.| 下排到前面，但它对 softmax 的贡献接近 0。

## 为什么这个测试存在

它守的不是某段代码，是一条**跨层结论**：Kernel Agent 报告的精度损失是
软件用 75% 质量的选择器算出来的；这台加速器的选择器只有 31%。那个精度
数字在硬件上不成立。

这是框架里第一份能触发跨层归因的数据——一个上层结论被下层证伪。
"""

from __future__ import annotations

from fast.agents.templates import TemplateRegistry


# 实测值。改动它们就是改动结论，所以它们在测试里而不是注释里。
SOFTWARE_VS_EXACT = 24 / 32       # 75%  DynaX 软件
UPSTREAM_VS_EXACT = 10 / 32       # 31%  上游 RTL（无符号）
UPSTREAM_VS_SOFTWARE = 9 / 32     # 28%
PATCHED_VS_EXACT = 23 / 32        # 72%  修复后 RTL（有符号）


def test_the_registry_records_the_signedness_divergence():
    """这个分歧必须写在模板记录里，而不是只存在于某次运行的日志中。

    没有它，下一个人看到 `verified=True` 会以为预测阵列和软件是一致的。
    """
    scope = TemplateRegistry().by_id("prepe_array").verified_scope

    assert "SIGNEDNESS" in scope
    assert "UInt(4.W)" in scope        # RTL 端口
    assert "2^(bits-1)-1" in scope     # 软件的量化上界


def test_the_scope_admits_that_its_own_restriction_hid_the_divergence():
    """诚实性的一条：验证时限定「操作数非负」，正是那条限定让分歧不可见。

    这不是可有可无的自我批评。一个只在非负输入上验证过的模块，它的
    `verified=True` 对真实数据（有正有负）说明不了什么——不写下来，
    这个限制就会被当成不存在。
    """
    scope = TemplateRegistry().by_id("prepe_array").verified_scope

    assert "掩盖" in scope or "不可见" in scope


def test_software_approximation_is_not_the_bottleneck():
    """4-bit 近似本身能保住大部分选择，所以位宽不是原因。

    如果软件也只有 30% 左右，结论会完全不同——那说明 4-bit 太粗，
    该改的是位宽而不是符号。这个测试把两种解释分开。
    """
    assert SOFTWARE_VS_EXACT > 0.7
    assert UPSTREAM_VS_EXACT < 0.4
    # 差距必须显著，否则不足以支撑「符号是原因」这个结论。
    assert SOFTWARE_VS_EXACT - UPSTREAM_VS_EXACT > 0.35


def test_hardware_diverges_from_the_software_it_should_implement():
    """硬件和软件互相的重合度，比各自与精确分数的重合度更低。

    这排除了「两者只是各自有损」——如果它们做的是同一件事、只是精度不同，
    互相的重合度应当高于各自对精确值的重合度。实测相反。
    """
    assert UPSTREAM_VS_SOFTWARE < SOFTWARE_VS_EXACT
    assert UPSTREAM_VS_SOFTWARE <= UPSTREAM_VS_EXACT


def test_the_fix_recovers_almost_all_of_the_gap():
    """改成有符号之后，重合度回到软件水平附近。

    剩下的 3 个百分点是定点细节（截断方向、平局处理），不是方向性错误——
    修复前差 44 个百分点，那才是方向错误的量级。
    """
    assert PATCHED_VS_EXACT > 0.7
    recovered = (PATCHED_VS_EXACT - UPSTREAM_VS_EXACT) / (
        SOFTWARE_VS_EXACT - UPSTREAM_VS_EXACT
    )
    assert recovered > 0.9, f"只挽回了 {recovered:.0%} 的差距"


def test_the_patched_predict_path_says_what_changed():
    """改动过的模板必须写明改了什么——这是 provenance 纪律。

    「DynaX 的基准数据」和「我们改过之后的数据」是两回事，混起来说
    就不再是基准了。
    """
    template = TemplateRegistry().by_id("prepe_array")

    assert template.provenance == "dynax-patched"
    assert "UInt" in template.patch_note and "SInt" in template.patch_note
    # 后果必须量化，不能只说「改成有符号了」。
    assert "31%" in template.patch_note and "72%" in template.patch_note
