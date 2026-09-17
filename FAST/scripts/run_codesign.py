"""端到端协同设计：读 Kernel Agent 的真实搜索结果，跑完整循环。

## 这个脚本补的是「协同」的定义所在

在它之前，端到端跑的是 `slurm/rtl/fast_design_ppa.slurm`——而那个脚本里的
`KernelResult` 是**手写的常量**：

    kernel = KernelResult(..., sparse_method="xm:16:8:64", actual_sparsity=0.85)

也就是说 Kernel Agent 的结论是**靠人转录**给下游的。那不是 agent 协作，是
两段各自能跑的流程加一次人工搬运。

这里从 `kernel_search_*.json` 读真实测量——真实困惑度、真实稀疏度、真实的
sparse-index profile——一路交到 Compiler / µArch / Evaluator / Critic。

## 候选是 Critic 的动作空间，不是并行评估

Kernel 的搜索报告里带着 K 个候选。它们**不是拿来同时评估的**，是归因到算法
层时 Critic 可以换过去的那些点——每一个的精度和稀疏度都已经量过，换过去
不用重测。

    python scripts/run_codesign.py --search kernel_search_sweep.json \\
        --rounds 3 --template repe_array --out codesign.json
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
import sys
from pathlib import Path

from fast.adapters.analytical import AnalyticalEvaluationAdapter
from fast.agents import CompilerAgent, CriticAgent, EvaluatorAgent, KernelAgent, UArchAgent
from fast.agents.kernel import select_candidates
from fast.agents.templates import DYNAX_TEMPLATES, TemplateRegistry
from fast.orchestrator.flow import FiveAgentFlow, _LoopState
from fast.schemas.conversions import kernel_result_from_measurement
from fast.agents.codesign import DEFAULT_OBJECTIVE, POWER_COVERAGE
from fast.storage.experiment_db import ExperimentDB
from fast.schemas.models import (
    ArchSpecs,
    digest_json,
    ArchSpecs,
    ExperimentSpec,
    Status,
    kernel_search_report_from_dict,
    to_primitive,
)



def _vertex(role: str, project: str | None, location: str, override: str | None):
    """给某个角色建一个真实的 Vertex 客户端。

    模型从 `llm_models.ROLES` 取，不在这里写死——「用最强的那一档」是一条
    项目级决定，散在各个脚本的默认参数里改一次要找五个地方。
    """
    from fast.agents.llm_backends import VertexDirect
    from fast.agents.llm_models import model_for

    choice = model_for(role)
    model = override or choice.model
    if not project:
        raise SystemExit("--llm 需要 --gcp-project 或 GCP_PROJECT")
    return VertexDirect(
        model=model, project=project, location=location,
        system_message=SYSTEM_MESSAGE, timeout_seconds=300,
        temperature=choice.temperature,
    ), model


SYSTEM_MESSAGE = (
    "You are a careful hardware/software co-design engineer. You reason from "
    "measured numbers and never invent configurations."
)

class _ReplayAdapter:
    """把已经跑完的搜索原样交回去，不重测。

    Kernel 的测量是这条链上最贵的一环（要加载模型跑困惑度）。已经有结果了
    还重跑一遍，等于把预算花两次；而且**重跑的结果会和报告里的不一致**——
    稀疏方法是数据相关的，换一次采样窗口候选就变了。
    """

    def __init__(self, report):
        self.report = report

    def evaluate(self, spec):  # pragma: no cover - 单点路径不走这里
        raise NotImplementedError("replay adapter only serves a finished search")

    def measure(self, spec, candidates):
        raise NotImplementedError("replay adapter only serves a finished search")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--search", type=Path, required=True,
                        help="Kernel Agent 的搜索报告 JSON")
    parser.add_argument("--candidates", type=int, default=3)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--template", default="repe_array")
    parser.add_argument("--head-dim", type=int, default=64)
    parser.add_argument("--capture-root", type=Path, default=None,
                        help="tile_*/tile.json 的父目录。给了就用 L2（真实 RTL "
                             "仿真）评估被规划的设计；不给就只有 L1 解析模型。")
    parser.add_argument("--repo-root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--llm", action="store_true",
                        help="Compiler 与 Critic 用真实的 Vertex 调用提议/归因；"
                             "不给就用确定性的 GuidedProposer 和规则 Critic")
    parser.add_argument("--gcp-project", default=os.environ.get("GCP_PROJECT"))
    parser.add_argument("--gcp-location", default=os.environ.get("GCP_LOCATION", "us-central1"))
    parser.add_argument("--llm-model", default=None,
                        help="覆盖两个角色的模型；不给就用 llm_models.py 里的选择")
    # ---- 约束：全部是**输入**，默认值只是默认值 ------------------------
    #
    #     min  L(x)  s.t.  dAcc(x) <= eps,  A(x) <= A_max,
    #                      P(x) <= P_max,   f(x) >= f_min
    #
    # eps 不在这里：它是 Kernel 搜索的门，跟着那份搜索报告一起进来
    # （`report.spec.epsilon`），在候选进入下游之前就已经生效了。
    parser.add_argument("--max-area-um2", type=float, default=None,
                        help="面积预算 A_max。默认用 ArchSpecs 的 4 mm^2（Nangate45）"
                             "——论文的 DynaX-S 是 28nm 1.08 mm^2，换算到 45nm 约 2.8 mm^2。")
    parser.add_argument("--max-power-mw", type=float, default=None,
                        help="功耗预算 P_max。默认不设——不给就不该拿功耗挡任何点。")
    parser.add_argument("--target-mhz", type=float, default=None,
                        help="频率下限 f_min。默认用 ArchSpecs 的 350 MHz"
                             "（执行阵列实测硬上限 448 MHz）。")
    parser.add_argument("--max-sram-bytes", type=int, default=None)
    parser.add_argument("--max-pe", type=int, default=None)
    parser.add_argument("--board", type=Path, default=None,
                        help="共享板的 sqlite 路径（记录整条优化轨迹）。"
                             "不给就放在 --out 旁边。")
    parser.add_argument("--mutate-rtl", action="store_true",
                        help="归因到 µArch 时真的改写 Chisel（LLM 改 + 机械门验证）。"
                             "不开的话「重新实现」是空转。需要 --llm。")
    parser.add_argument("--liberty", type=Path, default=None,
                        help="Nangate45 的 .lib。症状是时序/面积时门要综合，"
                             "没有它那一步只能报「没测」。")
    parser.add_argument("--sta-container", type=Path, default=None,
                        help="OpenSTA 镜像。给了才能量关键路径——而实测的症状"
                             "正是关键路径。")
    parser.add_argument("--gate-python", default=None,
                        help="跑 gen_golden.py / gen_ports.py 的解释器。金标准要 "
                             "torch，而 FAST 自己的环境没有——不给就用当前解释器，"
                             "那多半会让门以 ImportError 失败。")
    parser.add_argument("--mutate-attempts", type=int, default=3,
                        help="内循环次数：一个模块最多改几次去过门")
    parser.add_argument("--containers", type=Path,
                        default=Path("/scratch/gz2522/gz2522/tmp/micro-hackthon/containers"))
    parser.add_argument("--workload", type=Path, default=None,
                        help="BlockScheduler / KeyFeeder 的门要真实工作量激励；"
                             "不给的话这两个模块的门明确失败（不会静默通过）")
    args = parser.parse_args()

    report = kernel_search_report_from_dict(
        json.loads(args.search.read_text(encoding="utf-8"))
    )
    accepted = tuple(
        item for item in report.measurements
        if item.within and item.quality_loss <= report.spec.epsilon
    )
    picked, shortfall = select_candidates(accepted, args.candidates)
    if not picked:
        print(f"没有候选通过 epsilon 门：{shortfall}")
        return 2

    # 算法是**输入**：报告里的候选应当全是同一个算法的不同配置。
    # 旧报告（跨算法枚举时代产出的）会混，说出来而不是让它悄悄流下去——
    # 下游的「换候选」在混合报告里会变成换算法，那不是这个循环该做的事。
    algorithms = sorted({item.label.split(":")[0] for item in accepted})
    print(f"从 {args.search.name} 读到 {len(report.measurements)} 个测量，"
          f"{len(accepted)} 个通过 epsilon={report.spec.epsilon}")
    if len(algorithms) == 1:
        print(f"算法（输入，不是搜出来的）：{algorithms[0]}")
    else:
        print(f"⚠ 这份报告混了 {len(algorithms)} 个算法 {algorithms}——它是"
              f"「算法也在被搜」那一版留下的。算法应当是输入：用 "
              f"`fast.cli_kernel --algorithm <名字>` 重跑一次搜索。")
    print(f"选出 {len(picked)} 个候选（在稀疏度 / tile 不均衡度上散开）：")
    for index, item in enumerate(picked):
        print(f"  #{index} {item.label:<16s} 稀疏度 {item.actual_sparsity:.4f}  "
              f"精度损失 {item.quality_loss:+.4f}  "
              f"profile={'有' if item.profile else '无'}")
    if shortfall:
        print(f"  （{shortfall}）")

    # 约束从命令行来，没给的落回 ArchSpecs 的默认值。**默认值也要打印**——
    # 一个没说出口的约束，读结果的人不知道它挡掉了什么。
    defaults = ArchSpecs()
    specs = ArchSpecs(
        max_pe=args.max_pe if args.max_pe is not None else defaults.max_pe,
        max_sram_bytes=(args.max_sram_bytes if args.max_sram_bytes is not None
                        else defaults.max_sram_bytes),
        max_area_um2=(args.max_area_um2 if args.max_area_um2 is not None
                      else defaults.max_area_um2),
        target_mhz=args.target_mhz if args.target_mhz is not None else defaults.target_mhz,
        max_power_mw=(args.max_power_mw if args.max_power_mw is not None
                      else defaults.max_power_mw),
    )
    print(f"约束：精度损失 <= {report.spec.epsilon}（Kernel 的 ε 门）  "
          f"面积 <= {specs.max_area_um2:,.0f} um^2  "
          f"功耗 <= {f'{specs.max_power_mw:,.0f} mW' if specs.max_power_mw else '不限'}  "
          f"频率 >= {specs.target_mhz:,.0f} MHz")

    registry = TemplateRegistry()
    evaluator = _build_evaluator(args, picked[0], report.spec)

    # Compiler 和 Critic 的提议侧可以换成真实模型；可行性、打分、frontier、
    # 验收门仍然全部归代码。两种配置**只在「提议什么」这一维上**不同，
    # 否则「LLM 有没有帮上忙」这个对照就不成立。
    plan_proposer = None
    critic = CriticAgent()
    llm_note = "compiler=guided critic=rules（确定性）"
    if args.llm:
        from fast.agents.llm_critic import LLMCriticAgent
        from fast.agents.plan_proposers import LLMPlanProposer

        plan_llm, plan_model = _vertex("compiler", args.gcp_project,
                                       args.gcp_location, args.llm_model)
        critic_llm, critic_model = _vertex("critic", args.gcp_project,
                                           args.gcp_location, args.llm_model)
        plan_proposer = LLMPlanProposer(plan_llm, model_name=plan_model)
        critic = LLMCriticAgent(critic_llm, model_name=critic_model, specs=specs)
        llm_note = f"compiler={plan_model} critic={critic_model}（真实 Vertex 调用）"

    # µArch 的 RTL 变异：归因到这一层时**真的改 Chisel**，由机械门判能不能用。
    #
    # 不接的话「保计划、重新实现」在构造上是空转——`UArchAgent.run()` 是计划
    # 的纯函数。实测撞到过：三轮的计划和 util 逐字节相同，循环照常跑完。
    mutator = None
    if args.llm and args.mutate_rtl:
        from fast.agents.rtl_gate import LocalRtlGate
        from fast.agents.rtl_mutation import RtlMutator

        # **门的解释器不是这个脚本的解释器。** `gen_golden.py` import torch，
        # 而 FAST 自己的环境没有 torch——实测因此浪费过 6 次真实 LLM 调用：
        # 三次尝试 × 两轮，每次都以同一个 ImportError 失败，模型被要求
        # 「修一个它没弄坏的东西」。
        gate_python = args.gate_python or sys.executable
        # 综合默认关（慢），症状是时序/面积时由 `UArchAgent.mutate` 按症状开。
        # liberty + OpenSTA 在这里就位，否则那一步只能报「没测」。
        gate = LocalRtlGate(
            repo=args.repo_root, work_root=args.out.parent / "rtl_gate",
            containers=args.containers, python=gate_python,
            workload=args.workload, liberty=args.liberty,
            sta_container=args.sta_container,
        )
        mutate_llm, mutate_model = _vertex("uarch-mutate", args.gcp_project,
                                           args.gcp_location, args.llm_model)
        hardware = args.repo_root / "FAST" / "hardware"
        mutator = RtlMutator(
            mutate_llm, gate, model_name=mutate_model, attempts=args.mutate_attempts,
            # 金标准和 testbench 是只读的：每次门检查前后比对哈希，动了就直接
            # 判死，不给重试机会。
            protected=tuple(sorted(
                [*(hardware / "golden").glob("*.py"), *(hardware / "tb").glob("*.cpp"),
                 *(hardware / "tb").glob("*.h")]
            )),
        )
        llm_note += f" uarch-mutate={mutate_model}"

    # 横幅在这里打：mutator 也算提议侧的一部分，早打的话控制台会和报告里的
    # `proposers` 字段说不一样的话。
    print(f"提议侧：{llm_note}")

    # **共享板**：提案 Table II 里 Orchestrator 的输出是 "Prompts, shared
    # state"，Fig. 1 里 Evaluator 挂着 "Shared Data"。它记录整条优化轨迹
    # （每轮的计划、实测、归因），有两个消费者：组装 Critic 的 prompt，
    # 以及回答「这次循环验证过的最好的点是哪个」。
    #
    # 这块基础设施一直在（`ExperimentDB` 有完整 schema 和 cross_layer 视图），
    # 但循环从来没接上——`db=None` 让 `_record` 直接返回。
    objective = DEFAULT_OBJECTIVE
    board = ExperimentDB(args.board or (args.out.parent / "board.sqlite"))
    print(f"共享板：{board.path}")

    compiler = CompilerAgent(registry, template_id=args.template,
                             allow_unverified=True, proposer=plan_proposer, objective=objective)
    flow = FiveAgentFlow(
        KernelAgent(_ReplayAdapter(report)),
        compiler,
        UArchAgent(DYNAX_TEMPLATES, registry=registry, mutator=mutator,
                   chisel_root=args.repo_root / "FAST" / "hardware" / "chisel"
                               / "src" / "main" / "scala"),
        evaluator,
        critic,
        db=board,
        # **同一份约束交给所有阶段。** 原来 CLI 声明的 specs 只到 Critic 和
        # 报告，规划路径用的是 `plan()` 里的 `ArchSpecs()` 默认值——「声明的
        # 约束」和「搜索实际用的约束」可以不是一个，而事后拒绝代替不了
        # 约束内搜索。
        specs=specs,
        head_dim=args.head_dim,
    )

    # 循环从已有的搜索出发，不重跑 Kernel。
    #
    # **用 `FiveAgentFlow` 自己的分层重入，不再在这里复制一个。** 这个脚本
    # 原来手写了一个只认「换 kernel 候选」的循环，于是 Critic 归因到
    # compiler/uarch 时——两次真实运行里都发生了——只能报「该层的变异本脚本
    # 不施加」然后停在第 0 轮。看起来像 Critic 没给出可执行的动作，实际上
    # `_LoopState.apply` 一直支持这四层，是接收端少了三层。
    #
    # 分层重入正是「不再完整走一轮」的实现：
    #     KERNEL / COMPILER / PLANNER_MODEL   重新规划
    #     UARCH                               保计划，只重新实现
    #     EVALUATOR                           计划和硬件都保，只换保真度
    rounds = []
    state = _LoopState(
        candidate_index=0,
        labels=tuple(item.label for item in picked),
    )
    stopped = f"exhausted {args.rounds} rounds"

    for _ in range(args.rounds):
        chosen = picked[min(state.candidate_index, len(picked) - 1)]
        kernel = kernel_result_from_measurement(report, chosen)
        run = flow._round(
            report.spec, kernel, args.template, state,
            label=chosen.label, candidates=picked, history=tuple(rounds),
        )
        rounds.append(run)
        _print_round(len(rounds) - 1, run, state)

        critique = run.critique
        if critique.decision.value == "stop":
            stopped = f"critic stopped: {critique.summary}"
            break
        advanced, why = state.apply(critique, run)
        if not advanced:
            stopped = why
            break

    payload = {
        "search": str(args.search),
        "candidates": [to_primitive(asdict(item)) for item in picked],
        "candidate_shortfall": shortfall,
        "rounds": [to_primitive(asdict(item)) for item in rounds],
        "stopped_because": stopped,
        # **验证过的最优点。** 循环原来停在最后一轮而不是最好一轮——实测有
        # 一次第 1 轮拿到 util 0.899 / 1.47M um^2（全程最好），之后两轮都更差，
        # 报告里却找不到那个点。只在真跑过 RTL 且功能通过的轮次里挑：L1 的
        # 利用率是 planner 自己算的，拿它当"最好"等于让规划者给自己打分。
        "constraints": to_primitive(asdict(specs)),
        # 约束的摘要：报告里的数字属于**哪一组约束**要可追溯，否则两次跑
        # 出来的前沿没法比。
        "constraints_digest": digest_json(specs),
        "objective": {"primary": objective.primary,
                      "pareto_axes": list(objective.pareto_axes)},
        "power_coverage": POWER_COVERAGE,
        "energy_unit": "J/task",
        "energy_efficiency_unit": "task/J",
        "pareto_evidence": "model-predicted on function-checked designs; partial energy",
        "representative_policy": "lowest latency; full Pareto front is the result",
        "head_dim": args.head_dim,
        "pareto_front": board.pareto_front(flow.run_id, specs, objective) if flow.run_id else [],
        "infeasible": board.infeasible(flow.run_id, specs) if flow.run_id else [],
        "best_verified": board.best_verified(flow.run_id, specs) if flow.run_id else None,
        "verified_rounds": sum(
            1 for r in rounds
            if (r.evaluation and r.evaluation.fidelity == "L2-rtl-simulation")
        ),
        "trajectory": board.trajectory(flow.run_id) if flow.run_id else [],
        # 提议侧到底是模型还是回退。`LLMPlanProposer` / `LLMCriticAgent` 调用
        # 失败时会静默回退到确定性实现，只报「配置了 LLM」会把一次全靠回退
        # 的运行说成模型跑出来的。
        "proposers": llm_note,
        # 每轮改了哪个模块、过没过门、试了几次。失败的也留——归因到 µArch
        # 下一轮要靠它。
        "rtl_mutations": [
            {
                "round": i, "module": m.module, "accepted": m.accepted,
                "attempts": m.attempts, "reason": m.reason,
                # 通过的门量到了什么。「过了门」和「改进了目标」是两回事——
                # 只记诊断的话，一次 accepted 但毫无改进的变异读起来像成功。
                "gate_metrics": m.metrics,
                "gate_diagnostics": m.diagnostics[:2000],
            }
            for i, r in enumerate(rounds)
            if (m := getattr(r, "mutation", None)) is not None
        ],
        "llm_rejected": {
            "compiler": list(getattr(plan_proposer, "rejected", ()) or []),
            "critic": list(getattr(critic, "rejected", ()) or []),
        },
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, default=str) + "\n",
                        encoding="utf-8")
    verified = payload["verified_rounds"]
    print(f"\n跑了 {len(rounds)} 轮（{verified} 轮经过 RTL 验证）| 停止：{stopped}")
    # Report the whole energy/latency trade-off set, with explicit evidence scope.
    front = payload["pareto_front"]
    if front:
        axes = " / ".join(objective.pareto_axes)
        print(f"\n模型帕累托前沿（功能验证通过、模型约束可行，{len(front)} 个）"
              f"｜支配轴：{axes}")
        print(f"  {'轮':>3} {'配置':<14} {'形状':<9} {'延迟 ns':>10} {'能耗 uJ':>9} "
              f"{'面积 um^2':>12} {'吞吐 G-MAC/s':>13}")
        for row in front:
            print(f"  {row['round_index']:>3} {row['label']:<14} "
                  f"{row['num_rows']}x{row['pe_per_row']} q={row['queue_depth']:<3} "
                  f"{row['latency_ns']:>10,.0f} {row['energy_j']*1e6:>9,.3f} "
                  f"{row['area_um2']:>12,.0f} "
                  f"{(row['throughput_mac_per_s'] or 0)/1e9:>13.2f}"
                  + (f"   (轮 {row['reached_in_rounds']} 都到达了同一个点)"
                     if len(row.get("reached_in_rounds", [])) > 1 else ""))
    else:
        print("\n⚠ 帕累托前沿是空的——没有任何一轮既经过 RTL 验证又满足约束")
    if front:
        print(f"  注：能耗来自部分功耗模型（覆盖 {'/'.join(POWER_COVERAGE['included'])}；"
              f"未含 {'/'.join(POWER_COVERAGE['excluded'][:3])} 等），"
              f"用于探索前沿，不代表整机实测能效。")
    for row in payload["infeasible"]:
        print(f"  轮 {row['round_index']} 被约束挡掉：{'; '.join(row['violations'])}")
    print(f"结果 {args.out}")
    return 0



def _build_evaluator(args, seed_candidate, spec: ExperimentSpec) -> EvaluatorAgent:
    """给了 capture 目录就用 L2，否则只有 L1。

    **说清楚用的是哪一档。** L1 和 planner 共用同一个代价模型——它给出的
    「一致」是算术不是确认，而且它的 `functional_passed` 恒为 False（那是
    「没检查」不是「失败」）。
    """
    seed = kernel_result_from_measurement(None, seed_candidate)
    analytical = AnalyticalEvaluationAdapter(kernel=seed, kept_per_block=16)
    if args.capture_root is None:
        print("评估：L1 解析模型（和 planner 共用代价模型，functional_passed 恒为 False）")
        return EvaluatorAgent(analytical)

    from fast.adapters.verilator import VerilatorEvaluationAdapter

    print(f"评估：L2 真实 RTL 仿真，抓取目录 {args.capture_root}")
    l2 = VerilatorEvaluationAdapter(
        repo_root=args.repo_root, capture_root=args.capture_root,
        head_dim=args.head_dim,
    )
    # 阶梯：先跑便宜的 L1 拿 cycles/area/power，过了再升到 L2 验功能。
    return EvaluatorAgent(analytical, ladder=(l2,))


def _print_round(index: int, run, state=None) -> None:
    plan, ev, cr = run.compiler, run.evaluation, run.critique
    # 这一轮重做了哪一层——「一轮只变一层」如果看不见，跨轮对比就无从判断。
    redone = ""
    if state is not None and index > 0:
        parts = [name for name, flag in
                 (("重新规划", state.replan), ("重新实现", state.reimplement)) if flag]
        redone = f"  [{'、'.join(parts) if parts else '只重新评估'}]"
    print(f"\n轮 {index}  候选 {run.kernel.sparse_method}  "
          f"稀疏度 {run.kernel.actual_sparsity:.4f}{redone}")
    if plan.status is Status.PASSED:
        print(f"  计划 {plan.num_rows}x{plan.pe_per_row} q={plan.queue_depth} "
              f"div={plan.divider_stages} banks={plan.bank_count} "
              f"| 预测 {plan.predicted_area_um2:,.0f} um^2 "
              f"{1000 / plan.predicted_clock_ns:.0f} MHz")
    else:
        print(f"  规划失败：{plan.error}")
    # **没跑 RTL 要说响。** L1 的 pe_utilization 是 planner 自己的代价模型算
    # 出来的（证据字段自己写着 NOT INDEPENDENT），Critic 在这种轮次上的归因
    # 建立在不独立的数上。实测有一次 7 轮里 4 轮是这样，而输出看起来和验证过
    # 的轮次一模一样。
    verified = (ev.fidelity or "") == "L2-rtl-simulation"
    mark = "" if verified else "  ⚠ 未经 RTL 验证（这一档的数来自 planner 自己的代价模型）"
    print(f"  评估 [{ev.fidelity}] functional={ev.functional_passed} "
          f"util={ev.pe_utilization if ev.pe_utilization is None else f'{ev.pe_utilization:.3f}'}"
          f"{mark}")
    print(f"  归因 {cr.attribution.value} / {cr.decision.value}: {cr.summary[:80]}")


if __name__ == "__main__":
    raise SystemExit(main())
