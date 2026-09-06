"""综合适配器的契约：报告工具真正测到的，否则什么都不报。

这里的测试都围绕一件事——**一次「成功」的综合可能什么都没综合出来**。
`yowasp-yosys` 在 ABC 那一步静默停下并返回 0；一个只看返回码的适配器会把
那次跑当成成功，然后把 `None` 面积传给协同优化器。所以判据是输出里有没有
面积行，不是返回码。
"""

from __future__ import annotations

from pathlib import Path

from fast.adapters.synthesis import SynthesisResult, YosysSynthesisAdapter


def _adapter(tmp_path: Path, **kwargs) -> YosysSynthesisAdapter:
    container = tmp_path / "yosys.sif"
    liberty = tmp_path / "nangate.lib"
    container.write_text("")
    liberty.write_text("library(x) {}")
    return YosysSynthesisAdapter(container=container, liberty=liberty, **kwargs)


class _Stub(YosysSynthesisAdapter):
    """用一段录好的 yosys 输出替换真实调用。"""

    def __init__(self, text: str, returncode: int = 0, **kwargs) -> None:
        super().__init__(**kwargs)
        self._text = text
        self._rc = returncode
        self.calls = 0

    def synthesize(self, verilog, top_module):  # type: ignore[override]
        self.calls += 1
        import subprocess
        from unittest.mock import patch

        completed = subprocess.CompletedProcess([], self._rc, self._text, "")
        with patch("subprocess.run", return_value=completed):
            return YosysSynthesisAdapter.synthesize(self, verilog, top_module)


_GOOD = """
2.25. Printing statistics.
=== ExpUnitFixPoint ===
   Number of cells:                839
     $_ANDNOT_                     238

3. Executing ABC pass.
Printing statistics.
=== ExpUnitFixPoint ===
   Number of cells:                536
     NAND2_X1                       69
     XNOR2_X1                       81
   Chip area for module '\\ExpUnitFixPoint': 625.898000
"""

# 层次化设计：yosys 先逐个子模块打印，最后才是顶层总和。子模块的面积在前，
# 所以取第一个匹配会拿到 625.9（ExpUnitFixPoint），而真实是 1591880。
_HIERARCHICAL = """
Printing statistics.
=== ExpUnitFixPoint ===
   Number of cells:                536
   Chip area for module '\\ExpUnitFixPoint': 625.898000

=== RePE ===
   Number of cells:               2237
   Chip area for module '\\RePE': 2210.194000

=== RePEArray ===
   Number of cells:            1300544
     NAND2_X1                   161024
   Chip area for top module '\\RePEArray': 1591880.192000
"""

# ABC 之前就停下的一次跑：返回码 0，有 stat，但没有映射后的面积。
_STOPPED_AT_ABC = """
2.22. Executing ABC pass (technology mapping using ABC).
2.22.1. Extracting gate netlist of module `\\ExpUnitFixPoint' to `input.blif'..
"""


def test_a_real_run_reports_measured_area(tmp_path):
    verilog = tmp_path / "x.v"
    verilog.write_text("module x(); endmodule")
    adapter = _Stub(_GOOD, container=tmp_path / "yosys.sif",
                    liberty=tmp_path / "nangate.lib")
    (tmp_path / "yosys.sif").write_text("")
    (tmp_path / "nangate.lib").write_text("library(x) {}")

    result = adapter.synthesize(verilog, "ExpUnitFixPoint")

    assert result.success is True
    assert result.cell_area_um2 == 625.898
    # 最后一次 stat 才是映射到标准单元之后的；前一次 839 是通用门。
    assert result.cell_count == 536
    assert result.technology == "nangate45"


def test_a_hierarchical_design_reports_the_top_module_not_a_submodule(tmp_path):
    """层次化设计里子模块的面积先打印，顶层总和最后打印。

    这是一个真实咬过的错误：RePEArray_L 一度被报成 625.9 um^2，
    那是它内部 ExpUnitFixPoint 的面积；它真实是 1.59 mm^2。
    """
    verilog = tmp_path / "x.v"
    verilog.write_text("module x(); endmodule")
    adapter = _Stub(_HIERARCHICAL, container=tmp_path / "yosys.sif",
                    liberty=tmp_path / "nangate.lib")
    (tmp_path / "yosys.sif").write_text("")
    (tmp_path / "nangate.lib").write_text("library(x) {}")

    result = adapter.synthesize(verilog, "RePEArray")

    assert result.success is True
    assert result.cell_area_um2 == 1591880.192
    assert result.cell_count == 1300544


def test_area_and_cell_count_from_different_modules_is_rejected(tmp_path):
    """面积和单元数必须自洽，否则它们来自不同的模块段。

    出错时的表现不是崩溃，是一个看起来合理的小数字——226703 个单元配
    311.8 um^2。每单元面积一算就露馅。
    """
    inconsistent = """
Printing statistics.
=== SRAM ===
   Number of cells:             226703
   Chip area for module '\\SRAMBank': 311.800000
"""
    verilog = tmp_path / "x.v"
    verilog.write_text("module x(); endmodule")
    adapter = _Stub(inconsistent, container=tmp_path / "yosys.sif",
                    liberty=tmp_path / "nangate.lib")
    (tmp_path / "yosys.sif").write_text("")
    (tmp_path / "nangate.lib").write_text("library(x) {}")

    result = adapter.synthesize(verilog, "SRAM")

    assert result.success is False
    assert "不自洽" in result.error


def test_a_run_that_stopped_at_abc_is_not_a_success(tmp_path):
    """返回码 0 但没有映射结果——判据是面积行，不是退出码。"""
    verilog = tmp_path / "x.v"
    verilog.write_text("module x(); endmodule")
    adapter = _Stub(_STOPPED_AT_ABC, returncode=0,
                    container=tmp_path / "yosys.sif", liberty=tmp_path / "nangate.lib")
    (tmp_path / "yosys.sif").write_text("")
    (tmp_path / "nangate.lib").write_text("library(x) {}")

    result = adapter.synthesize(verilog, "ExpUnitFixPoint")

    assert result.success is False
    assert result.cell_area_um2 is None
    assert "no area" in result.error


def test_the_histogram_keeps_standard_cells_and_drops_generic_gates(tmp_path):
    verilog = tmp_path / "x.v"
    verilog.write_text("module x(); endmodule")
    adapter = _Stub(_GOOD, container=tmp_path / "yosys.sif",
                    liberty=tmp_path / "nangate.lib")
    (tmp_path / "yosys.sif").write_text("")
    (tmp_path / "nangate.lib").write_text("library(x) {}")

    result = adapter.synthesize(verilog, "ExpUnitFixPoint")

    assert result.cell_histogram == {"NAND2_X1": 69, "XNOR2_X1": 81}


def test_a_missing_input_fails_before_running_anything(tmp_path):
    adapter = _adapter(tmp_path)

    result = adapter.synthesize(tmp_path / "nope.v", "X")

    assert result.success is False
    assert "no such Verilog" in result.error


def test_the_script_maps_flipflops_before_asking_abc_for_area(tmp_path):
    """`dfflibmap` 必须在 `abc -liberty` 之前。

    否则 abc 会把触发器留成通用 `$_DFF_`，最后的 `stat -liberty` 少算一大块
    面积——而且不会报错，只会给出一个偏小且看起来合理的数字。
    """
    adapter = _adapter(tmp_path)

    script = adapter.script(Path("x.v"), "X")

    assert script.index("dfflibmap") < script.index("abc -liberty")
    assert script.index("abc -liberty") < script.rindex("stat -liberty")


def test_repeated_synthesis_of_one_module_is_cached(tmp_path):
    adapter = _adapter(tmp_path)
    recorded = SynthesisResult(True, "X", "nangate45", 1.0, 1)
    adapter._cache[(str(tmp_path / "x.v"), "X")] = recorded

    assert adapter.synthesize(tmp_path / "x.v", "X") is recorded


# ---------------------------------------------------------------------------
# 标定：模型的系数来自实测，所以实测变了模型必须跟着变
# ---------------------------------------------------------------------------

def test_the_area_model_matches_what_synthesis_measured():
    """面积公式的系数是从 yosys 实测标定出来的，这里把它钉住。

    实测（Nangate45，slurm/rtl/fast_synthesis.slurm，job 17018014）：

        TopK(32,8,16)           3141.7 um^2
        TopK(64,16,16)          6468.9 um^2
        RePEArray(32,4,16,8)  371999.9 um^2
        RePEArray(64,8,16,16)1591880.2 um^2

    容差 10%：公式只有两个自由度（每族一个缩放），要拟合两个配置，所以
    残差是公式**形式**的误差，不是拟合误差。实测族内一致性是 1.07-1.08x，
    所以 10% 是能达到的；达不到就说明公式形式不再成立。
    """
    from fast.agents.templates import array_area_units, topk_area_units

    measured = [
        (topk_area_units(32, 8, 16), 3141.7),
        (topk_area_units(64, 16, 16), 6468.9),
        (array_area_units(32, 4, 16, 8), 371999.9),
        (array_area_units(64, 8, 16, 16), 1591880.2),
    ]
    for model, actual in measured:
        assert abs(model - actual) / actual < 0.10, (
            f"模型 {model:.1f} um^2 偏离实测 {actual:.1f} um^2 超过 10%"
        )


def test_the_relative_weighting_between_the_two_units_is_right():
    """族间相对权重是这次标定真正修的东西。

    标定前，模型把执行阵列相对预测单元低估了 25.3 倍。协同优化器正是在用
    kept_per_block（预测单元面积）换阵列规模（执行单元面积），所以这个偏差
    直接改变它选出哪个点——它不是精度问题，是取舍问题。
    """
    from fast.agents.templates import array_area_units, topk_area_units

    # 实测比：371999.9 / 6468.9 = 57.5
    ratio = array_area_units(32, 4, 16, 8) / topk_area_units(64, 16, 16)

    assert 50 < ratio < 66, f"阵列/TopK 面积比 {ratio:.1f}，实测是 57.5"


def test_the_area_budget_is_named_in_the_unit_it_holds():
    """字段名必须和单位一致——一个叫 units 却装 um^2 的字段是静默错配。"""
    from fast.schemas.models import ArchSpecs

    specs = ArchSpecs()

    assert hasattr(specs, "max_area_um2")
    assert not hasattr(specs, "max_area_units")
    # 预算要真的能拒掉东西：DynaX-L 规模的阵列加 SRAM 应当逼近它。
    assert 1_000_000 < specs.max_area_um2 < 20_000_000
