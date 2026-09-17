"""时序与功耗适配器的契约。

核心是一条：**动态功耗严格正比于 α**。实测（ExpUnitFixPoint，Nangate45，
同一网表只改 α）：

    α = 0.05  ->  1.199 mW
    α = 0.20  ->  4.751 mW   (4.0x)
    α = 0.50  -> 11.854 mW  (10.0x)

泄漏全程 14.8 uW 不变。所以 α 用工具默认常数等于给出一个任意数——更糟的是
那个数和稀疏度无关，而 DynaX 省的恰恰就是翻转。这里的测试因此围绕
「α 必须来自实际激励，并且必须跟着结果一起走」。
"""

from __future__ import annotations

from pathlib import Path
import subprocess
from unittest.mock import patch

from fast.adapters.timing import (
    OpenStaTimingAdapter,
    TimingResult,
    activity_from_stimulus,
)

# 一次真实 OpenSTA 输出的节选。
_GOOD = """
   0.017    1.659 v _1007_/ZN (OAI21_X1)
   0.000    1.659 v io_out_exp[0] (out)
            1.659   data arrival time
            1.900   data required time
-----------------------------------------------------------
            0.241   slack (MET)

Group                  Internal  Switching    Leakage      Total
                          Power      Power      Power      Power (Watts)
----------------------------------------------------------------
Sequential           0.0000e+00 0.0000e+00 0.0000e+00 0.0000e+00   0.0%
Combinational        2.5944e-03 2.1413e-03 1.4842e-05 4.7505e-03 100.0%
Total                2.5944e-03 2.1413e-03 1.4842e-05 4.7505e-03 100.0%
"""

_VIOLATED = _GOOD.replace("0.241   slack (MET)", "-0.350   slack (VIOLATED)")


def _adapter(tmp_path: Path) -> OpenStaTimingAdapter:
    (tmp_path / "sta.sif").write_text("")
    (tmp_path / "n.lib").write_text("library(x) {}")
    return OpenStaTimingAdapter(
        container=tmp_path / "sta.sif", liberty=tmp_path / "n.lib",
        work_root=tmp_path,
    )


def _run(adapter: OpenStaTimingAdapter, tmp_path: Path, text: str,
         **kwargs) -> TimingResult:
    netlist = tmp_path / "netlist.v"
    netlist.write_text("module x(); endmodule")
    completed = subprocess.CompletedProcess([], 0, text, "")
    with patch("subprocess.run", return_value=completed):
        return adapter.analyse(netlist, "ExpUnitFixPoint", **kwargs)


def test_timing_and_power_come_from_one_run(tmp_path):
    """两者共用同一次 link，所以也共用同一份网表——不会各说各话。"""
    result = _run(_adapter(tmp_path), tmp_path, _GOOD, activity=0.2)

    assert result.success is True
    assert result.critical_path_ns == 1.659
    assert result.slack_ns == 0.241
    assert result.total_power_w == 4.7505e-03
    assert result.leakage_power_w == 1.4842e-05


def test_frequency_estimate_includes_setup_and_external_delays(tmp_path):
    result = _run(_adapter(tmp_path), tmp_path, _GOOD)

    assert abs(result.max_frequency_mhz - 1000 / (2.0 - 0.241)) < 0.01
    # Arrival alone would optimistically omit the output delay in this path.
    assert result.max_frequency_mhz < 1000 / result.critical_path_ns


def test_a_violated_path_still_reports_its_negative_slack(tmp_path):
    """时序不收敛必须能被看见——一个 slack 为负的设计，它的 EDP 是假的。"""
    result = _run(_adapter(tmp_path), tmp_path, _VIOLATED)

    assert result.success is True
    assert result.slack_ns == -0.350


def test_the_activity_travels_with_the_result(tmp_path):
    """动态功耗严格正比于 α，所以脱离 α 的功耗数字没有意义。"""
    result = _run(_adapter(tmp_path), tmp_path, _GOOD, activity=0.37)

    assert result.activity == 0.37


def test_a_run_without_timing_is_not_a_success(tmp_path):
    result = _run(_adapter(tmp_path), tmp_path, "STA 启动失败\n")

    assert result.success is False
    assert result.critical_path_ns is None
    assert "no timing" in result.error


def test_a_missing_netlist_fails_before_running_anything(tmp_path):
    adapter = _adapter(tmp_path)

    result = adapter.analyse(tmp_path / "nope.v", "X")

    assert result.success is False
    assert "no such netlist" in result.error


# ---------------------------------------------------------------------------
# α 从激励里数出来
# ---------------------------------------------------------------------------

def test_activity_counts_bit_transitions_in_the_real_stimulus():
    """α = 每个输入位每周期翻转的次数。"""
    # 0b0000 -> 0b1111 -> 0b0000：每步 4 位全翻，其余位不动。
    cases = [{"input_ticks": [0b0000, 0b1111, 0b0000]}]

    activity = activity_from_stimulus(cases, bits_per_field=4)

    assert activity == 1.0


def test_a_constant_stimulus_has_no_activity():
    """不翻转就没有动态功耗——这是 α 定义的下界。"""
    cases = [{"input_ticks": [7, 7, 7, 7]}]

    assert activity_from_stimulus(cases, bits_per_field=4) == 0.0


def test_activity_is_measured_not_assumed():
    """不同激励给出不同 α，这正是让功耗随工作负载变化的那一步。

    如果这个函数返回常数，功耗就和稀疏度脱钩了——那正是用工具默认 α 的后果。
    """
    quiet = [{"input_ticks": [0, 0, 1, 1, 0, 0]}]
    busy = [{"input_ticks": [0, 15, 0, 15, 0, 15]}]

    assert activity_from_stimulus(quiet, 4) < activity_from_stimulus(busy, 4)


def test_a_single_cycle_case_contributes_nothing():
    """只有一拍就没有「翻转」可言，不能当成 0 活动混进平均值。"""
    assert activity_from_stimulus([{"input_ticks": [5]}], 4) == 0.0


# ---------------------------------------------------------------------------
# 合理性守卫：综合后的网表没有插过缓冲
# ---------------------------------------------------------------------------

_FANOUT_ARTIFACT = """
   0.1224    0.2224 v _30910_/ZN (INV_X1)
  12.7092   12.9317 ^ _37240_/ZN (NOR2_X1)
 196.1739  209.1055 v _37244_/ZN (NOR2_X1)
  20.4495  229.5550 ^ _44199_/ZN (AOI22_X1)
          228.9956   data arrival time
         -227.434   slack (VIOLATED)

Group                  Internal  Switching    Leakage      Total
Total                1.838971e-01 1.368157e-01 3.649699e-02 3.570000e-01 100.0%
"""


def test_an_unbuffered_fanout_path_is_flagged_not_reported(tmp_path):
    """单个 NOR2 报出 196 ns 不是关键路径，是缺缓冲的伪影。

    45nm 的 NOR2_X1 实际约 0.02 ns，差了 4000 倍。起点是广播给 512 个 PE 的
    控制信号——插缓冲是布局布线干的活，综合后的网表没有。

    这个测试存在的理由是我差点把它当成「DynaX 达不到 500 MHz」报出去。
    """
    result = _run(_adapter(tmp_path), tmp_path, _FANOUT_ARTIFACT)

    assert result.success is True          # STA 本身跑成功了
    assert result.timing_credible is False  # 但这个时序不能用
    assert result.worst_stage_cell == "NOR2_X1"
    assert result.worst_stage_ns == 196.1739
    assert "未插缓冲" in result.error or "缓冲" in result.error


def test_a_credible_path_is_not_flagged(tmp_path):
    """真实路径每一级都在零点几 ns 以内。"""
    result = _run(_adapter(tmp_path), tmp_path, _GOOD)

    assert result.timing_credible is True
    assert result.error is None


def test_power_survives_an_incredible_timing_path(tmp_path):
    """时序被扇出主导，不影响面积和功耗——它们不依赖路径延迟。"""
    result = _run(_adapter(tmp_path), tmp_path, _FANOUT_ARTIFACT)

    assert result.total_power_w == 3.570000e-01
    assert result.leakage_power_w == 3.649699e-02
