"""翻转率必须从真实激励数出来，不能用假设值。

实测 α = 0.0213，而代码里一直假设 0.2——**差 9.4 倍**。叠加上
`set_power_activity -input` 对内部网没有控制力（α 扫 45 倍，功耗非单调
抖动 ±5%），同一个设计的功耗报出 113.4 mW 而正确值是 14.05 mW，
**高估 8.07 倍**。
"""

from __future__ import annotations

import textwrap

import pytest

from fast.adapters.timing import DEFAULT_ACTIVITY
from fast.adapters.vcd_activity import activity_from_vcd


def _vcd(body: str) -> str:
    return textwrap.dedent(body).strip() + "\n"


def test_a_signal_that_never_toggles_has_zero_activity(tmp_path):
    path = tmp_path / "still.vcd"
    path.write_text(_vcd("""
        $var wire 1 ! clock $end
        $var wire 1 " data $end
        $enddefinitions $end
        #0
        0!
        0"
        #1
        1!
        #2
        0!
    """), encoding="utf-8")
    got = activity_from_vcd(path)
    assert got.transitions == 0
    assert got.alpha == 0.0


def test_the_clock_is_not_counted(tmp_path):
    """时钟每周期必翻两次。混进去会把 α 拉向一个与工作负载无关的常数。"""
    path = tmp_path / "clk.vcd"
    path.write_text(_vcd("""
        $var wire 1 ! clock $end
        $var wire 1 " data $end
        $enddefinitions $end
        #0
        0!
        0"
        #1
        1!
        #2
        0!
        #3
        1!
    """), encoding="utf-8")
    got = activity_from_vcd(path)
    assert got.signals == 1          # 只有 data
    assert got.transitions == 0      # data 没动过


def test_a_vector_counts_bits_not_signals(tmp_path):
    """一个 16 位总线翻 3 位算 3 次翻转。

    按信号计会让宽总线和单比特控制信号权重相同，而功耗跟的是位。
    """
    path = tmp_path / "bus.vcd"
    path.write_text(_vcd("""
        $var wire 1 ! clock $end
        $var wire 4 " bus $end
        $enddefinitions $end
        #0
        0!
        b0000 "
        #1
        1!
        b0111 "
        #2
        0!
    """), encoding="utf-8")
    got = activity_from_vcd(path)
    assert got.transitions == 3


def test_the_default_activity_is_the_measured_one_not_the_assumed_one():
    """0.2 是个从来没被验证过的假设。实测是 0.0213。"""
    assert DEFAULT_ACTIVITY == pytest.approx(0.0213)
    assert DEFAULT_ACTIVITY < 0.2 / 5


def test_the_sta_script_uses_global_not_input():
    """`-input` 对内部网没有控制力：α 扫 45 倍，功耗非单调抖动 ±5%。"""
    from pathlib import Path

    from fast.adapters.timing import OpenStaTimingAdapter

    adapter = OpenStaTimingAdapter(
        container=Path("/nonexistent.sif"), liberty=Path("/nonexistent.lib"),
        work_root=Path("/tmp"))
    script = adapter.script(Path("/n.v"), "Top", 2.0, 0.0213)
    assert "set_power_activity -global" in script
    assert "set_power_activity -input" not in script
