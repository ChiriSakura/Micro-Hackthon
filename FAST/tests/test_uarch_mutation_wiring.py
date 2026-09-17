"""归因到 µArch 时要真的改 RTL，而不是把同一份计划再算一遍。

`UArchAgent.run(plan, template_id)` 是计划的**纯函数**，所以「保计划、重新
实现」在构造上必然给出同一份硬件。实测撞到过（作业 17248917）：Critic 连续
两轮发 `uarch.queue rewrite`，三轮的计划和 util 逐字节相同，循环照常跑完，
没有任何东西说这两轮白跑了。真正的 RTL 变异路径 `rtl_mutation.py` 当时根本
没接进 flow。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from fast.agents.rtl_gate import MODULES, mutable_modules, resolve_module
from fast.agents.templates import DYNAX_TEMPLATES, TemplateRegistry
from fast.agents.uarch import UArchAgent
from fast.schemas.models import Layer, Mutation


def _mutation(field: str, value: str = "rewrite", effect: str = "") -> Mutation:
    return Mutation(layer=Layer.UARCH, field=field, operation="rewrite",
                    value=value, expected_effect=effect, risk="r")


# --- 解析：按内容，不按字段名 ------------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("queue rewrite reduce critical path, queue depth 2 is 2.528 ns", "BlockSched_S4"),
    ("queue_rtl add_pipeline_stage", "BlockSched_S4"),
    ("the TopK comparator chain is the critical path", "TopK"),
    ("divider_stages decrease to 4", "Divider"),
    ("the RePE multiplier truncates instead of rounding", "RePE"),
    ("bank_count increase to break gather conflicts", "KeyFeeder_B32"),
])
def test_a_mutation_resolves_to_a_module_by_content(text, expected):
    """字段名是模型自由发挥的部分——同一次运行里就出现过 `queue` 和
    `queue_rtl` 两种写法。"""
    module, why = resolve_module(text)
    assert module == expected, why


def test_short_aliases_do_not_match_inside_longer_words():
    """按词边界匹配，不是子串。

    `pe` 是「pi**pe**line」和「**pe**riod」的子串——子串匹配会把一条关于
    工作队列的变异解析成「改 RePE」，然后门在一个和症状无关的地方失败。
    """
    module, _ = resolve_module("add a pipeline stage; the clock period is 2.528 ns")
    assert module != "RePE"


def test_an_unresolvable_mutation_says_why_instead_of_guessing():
    module, why = resolve_module("make it faster somehow")
    assert module is None
    assert "指不到" in why and "可变异的是" in why


# --- 只有「有门」的模块才允许被改 --------------------------------------------

def test_only_gated_modules_are_mutable():
    """变异的全部价值在于有一个机械的门判它能不能用。

    没有门的模块被改写 = 无验证地生成 RTL，正是这个项目一开始就拒绝的东西。
    """
    for name, spec in mutable_modules().items():
        assert spec.source, f"{name} 登记为可变异却没有源文件"
        assert name in MODULES, f"{name} 可变异却不在门的登记表里"


def test_every_registered_source_actually_exists():
    root = Path(__file__).resolve().parents[1] / "hardware/chisel/src/main/scala"
    for name, spec in mutable_modules().items():
        assert (root / spec.source).is_file(), f"{name}: {spec.source} 不存在"


# --- 做不了的时候要说清楚是哪一种做不了 --------------------------------------

def _agent(**kwargs) -> UArchAgent:
    return UArchAgent(DYNAX_TEMPLATES, registry=TemplateRegistry(), **kwargs)


def test_without_a_mutator_it_says_reimplementation_is_a_no_op():
    """「没配变异器」和「改了但没过门」的下一步完全不同，不能报成一样。"""
    outcome = _agent().mutate(_mutation("queue"), symptom="s", target="t")
    assert outcome.accepted is False
    assert "空转" in outcome.reason


def test_an_unresolvable_mutation_is_refused_before_touching_any_file(tmp_path):
    class _NeverCalled:
        def mutate(self, *a, **k):   # pragma: no cover
            raise AssertionError("解析不出模块时不该去改文件")

    agent = _agent(mutator=_NeverCalled(), chisel_root=tmp_path)
    outcome = agent.mutate(_mutation("make it faster"), symptom="", target="")
    assert outcome.accepted is False
    assert "指不到" in outcome.reason


def test_a_resolved_mutation_reaches_the_mutator_with_the_right_file(tmp_path):
    seen = {}

    class _Spy:
        def mutate(self, path, module, *, symptom, target):
            seen.update(path=path, module=module, symptom=symptom, target=target)
            return "outcome"

    source = tmp_path / MODULES["TopK"].source
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("// chisel", encoding="utf-8")

    agent = _agent(mutator=_Spy(), chisel_root=tmp_path)
    got = agent.mutate(
        _mutation("topk", "rewrite", "critical path below 2.230 ns"),
        symptom="TopK is the critical path at 19.0 ns", target="",
    )

    assert got == "outcome"
    assert seen["module"] == "TopK"
    assert seen["path"] == source
    assert "19.0 ns" in seen["symptom"]
    assert "2.230 ns" in seen["target"]


# --- 主语优先：Critic 的叙述常拿别的模块作对比 -------------------------------

def test_the_mutations_own_words_outrank_the_critics_narration():
    """实测撞到过：症状是

        "the queue's 2.528 ns critical path, which is slower than the
         execution array's 2.230 ns"

    "execution array"（15 字符）比 "queue"（5 字符）长，只按最长别名打分就
    会去改 RePE——而要改的是队列。**主语在变异里，对比对象在叙述里。**
    """
    symptom = ("The clock frequency is limited by the queue's 2.528 ns critical "
               "path, which is slower than the execution array's 2.230 ns")
    for field in ("queue", "queue_rtl"):
        module, why = resolve_module(f"{field} rewrite {symptom}", subject=f"{field} rewrite")
        assert module == "BlockSched_S4", why
        assert "变异字段" in why


def test_a_mutation_that_really_targets_repe_is_not_stolen_by_the_narration():
    module, why = resolve_module(
        "repe multiplier rounding; the queue is fine", subject="repe multiplier")
    assert module == "RePE", why


def test_uarch_agent_passes_the_subject_through(tmp_path):
    """`UArchAgent.mutate` 要把字段/值单独当主语传下去，不是拼成一坨全文。"""
    seen = {}

    class _Spy:
        def mutate(self, path, module, *, symptom, target):
            seen.update(module=module)
            return "outcome"

    spec = MODULES["BlockSched_S4"]
    source = tmp_path / spec.source
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("// chisel", encoding="utf-8")

    agent = _agent(mutator=_Spy(), chisel_root=tmp_path)
    agent.mutate(
        _mutation("queue", "rewrite", "clock period below 2.230 ns"),
        symptom=("The clock frequency is limited by the queue's 2.528 ns critical "
                 "path, which is slower than the execution array's 2.230 ns"),
        target="",
    )
    assert seen["module"] == "BlockSched_S4"


# --- 门自己坏了，不该重试 -----------------------------------------------------

def test_the_mutator_stops_when_the_gate_itself_is_broken(tmp_path):
    """环境问题重试多少次都是同一个错，而每次重试都要花一次真实 LLM 调用。

    实测浪费过 6 次：门用的解释器没有 torch，`gen_golden.py` 每次都以同一个
    ImportError 失败。
    """
    from fast.agents.rtl_mutation import INFRA_PREFIX, GateResult, RtlMutator

    calls = {"n": 0}

    class _LLM:
        def prompt(self, text, tools=None):
            calls["n"] += 1
            class R:
                result, success = "// rewritten", True
            return R()

    class _BrokenGate:
        def check(self, module_path, target):
            return (GateResult("simulate", False,
                               f"{INFRA_PREFIX}golden model failed: No module named 'torch'"),)

    source = tmp_path / "m.scala"
    source.write_text("// original", encoding="utf-8")

    outcome = RtlMutator(_LLM(), _BrokenGate(), attempts=3).mutate(
        source, "RePE", symptom="s", target="t")

    assert outcome.accepted is False
    assert calls["n"] == 1, "门坏了却重试了——每次都是一次浪费的真实调用"
    assert "门自己跑不起来" in outcome.reason
    # 失败必须回退原文件。
    assert source.read_text(encoding="utf-8") == "// original"


# --- 内循环的打磨：契约、反馈、可测的目标 -------------------------------------

def test_every_module_with_a_known_invariant_states_its_contract():
    """契约是设计文档，不是测试内部——改它的模型本来就该知道。

    不写的后果实测过：LLM 三次改写 BlockScheduler，三次都丢了工作
    （23760 个保留列只发出 19160 个）。门每次都抓住了，但模型在猜契约。
    """
    for name in ("BlockSched_S4", "KeyFeeder_B32", "TopK", "RePE", "SRAM", "Divider"):
        assert MODULES[name].contract.strip(), f"{name} 没写契约"


def test_the_block_scheduler_contract_names_work_conservation():
    """那正是三次改写全部违反的那一条。"""
    contract = MODULES["BlockSched_S4"].contract.lower()
    assert "work conservation" in contract
    assert "exactly equal" in contract


def test_the_prompt_carries_the_contract_and_the_previous_diff():
    from fast.agents.rtl_mutation import MUTATION_PROMPT

    assert "{contract}" in MUTATION_PROMPT
    body = MUTATION_PROMPT.format(
        symptom="s", target="t", contract="CONTRACT-HERE", attempt=2, attempts=3,
        history="H", source="src",
    )
    assert "CONTRACT-HERE" in body


def test_a_rejected_attempt_feeds_back_what_the_model_changed():
    """只回诊断，等于让模型对着一个它看不见的东西调试。"""
    from fast.agents.rtl_mutation import _diff_summary

    summary = _diff_summary("val a = 1\nval b = 2\n", "val a = 1\nval b = 3\n")
    assert "what you changed" in summary
    assert "-val b = 2" in summary and "+val b = 3" in summary


def test_an_unchanged_rewrite_is_called_out():
    from fast.agents.rtl_mutation import _diff_summary

    assert "unchanged" in _diff_summary("same\n", "same\n")


# --- 症状是时序时，门必须能测到时序 -------------------------------------------

@pytest.mark.parametrize("text,expected", [
    ("the queue's 2.528 ns critical path limits the clock", True),
    ("area is 2,203,630 um^2, too large", True),
    ("max_frequency_mhz is below target", True),
    ("the accumulator wraps instead of saturating", False),
    ("row 3 has passes that never enqueue", False),
])
def test_physical_symptoms_are_recognised(text, expected):
    """关键路径和面积在仿真里根本不存在。不综合的门测不到这类目标——
    模型被要求改进一个门无法观察的数，改完也说不出有没有用。"""
    from fast.agents.uarch import _mentions_physical

    assert _mentions_physical(text) is expected


def test_synthesis_is_turned_on_for_a_timing_symptom_and_restored_after(tmp_path):
    """按症状开，不是一直开——综合慢，功能类变异不该每次白等一次。"""
    seen = {}

    class _Gate:
        synthesise = False

    class _Mutator:
        gate = _Gate()

        def mutate(self, path, module, *, symptom, target):
            seen["synthesise_during"] = self.gate.synthesise
            return "outcome"

    spec = MODULES["BlockSched_S4"]
    source = tmp_path / spec.source
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text("// chisel", encoding="utf-8")

    mutator = _Mutator()
    agent = _agent(mutator=mutator, chisel_root=tmp_path)
    agent.mutate(
        _mutation("queue", "rewrite", "clock period below 2.230 ns"),
        symptom="the queue's 2.528 ns critical path limits the clock", target="",
    )
    assert seen["synthesise_during"] is True
    assert mutator.gate.synthesise is False, "用完没还回去，后面每次功能变异都白等综合"


def test_short_technical_words_never_match_inside_longer_words():
    """同一个子串错误这个会话里犯了三次，所以匹配收敛到一个共用实现。

        pe ⊂ pi**pe**line / **pe**riod   -> 队列的变异被解析成「改 RePE」
        ns ⊂ i**ns**tead                 -> 纯功能症状被判成「需要综合」
    """
    from fast.agents.rtl_mutation import contains_word

    assert not contains_word("add a pipeline stage", "pe")
    assert not contains_word("the clock period is 2.5", "pe")
    assert not contains_word("the accumulator wraps instead of saturating", "ns")
    # 独立成词时仍然要命中。
    assert contains_word("the critical path is 2.528 ns", "ns")
    assert contains_word("rewrite the pe array", "pe")
    assert contains_word("area is 2203630 um^2", "um^2")
