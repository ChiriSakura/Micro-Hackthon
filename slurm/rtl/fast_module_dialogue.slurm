#!/usr/bin/env bash
#SBATCH --job-name=fast-dialogue
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=32G --time=01:30:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# 用真实工具链跑逐模块对话，验证面积逐模块分摊真的能用。
#
# 分摊用的是**综合实测面积**，不是规划时的估计。一个只在假 gate 上验证过的
# 分摊逻辑，看起来和能用的一模一样。
set -uo pipefail
ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
OUT="$ROOT/runs/dialogue_${SLURM_JOB_ID}"
export PATH=/share/apps/openjdk/21.0.3/bin:$ROOT/tools:$PATH
export COURSIER_CACHE="$ROOT/cache/coursier" SCALA_CLI_HOME="$ROOT/cache/scala-cli"
export APPTAINER_TMPDIR=/tmp APPTAINER_CACHEDIR=/tmp/apptainer-cache
export TMPDIR=/tmp/dlg-$$; mkdir -p "$TMPDIR" "$OUT" /tmp/apptainer-cache

cd "$REPO/FAST"
PYTHONPATH="$REPO/FAST" "$ROOT/env/fast-py312/bin/python" -u - "$OUT" <<'PYEOF'
import sys
from pathlib import Path

from fast.agents.module_dialogue import ModuleDialogue
from fast.agents.rtl_gate import LocalRtlGate

out = Path(sys.argv[1])
root = Path("/scratch/gz2522/gz2522/tmp/micro-hackthon")
repo = Path("/home/gz2522/Micro-Hackthon")
gate = LocalRtlGate(
    repo=repo, work_root=out, containers=root / "containers",
    python=str(root / "env" / "dynax-py312" / "bin" / "python"),
    liberty=root / "pdk" / "nangate45" / "NangateOpenCellLibrary_typical.lib",
    # 综合不在内循环里：yosys 综合不了 SRAM，而且内循环要的是正确性不是 PPA。
    # 面积从已标定的模型取（那些系数就是从同一次综合来的），最终 PPA 走 hammer。
    synthesise=False,
    timeout_seconds=1200,
)
source = repo / "FAST/hardware/chisel/src/main/scala"
order = ("ExpUnit", "PSumSoftmax", "TopK", "RePE")

import time
t0 = time.time()
print("=== 用例 1：预算充足，全部造完（综合关闭）===", flush=True)
report = ModuleDialogue(gate, source_root=source, order=order).build(
    None, area_budget_um2=1e9
)
for item in report.outcomes:
    area = f"{item.area_um2:>10,.1f}" if item.area_um2 is not None else "         -"
    print(f"  {'PASS' if item.passed else 'FAIL'}  {item.module:<14s} {area} um^2   {item.reason}")
print(f"  合计 {report.area_spent_um2:,.1f} um^2 | 完成={report.complete} | {report.stopped_because}")
print(f"  耗时 {time.time()-t0:.1f}s")

spent = report.area_spent_um2
if spent > 0:
    tight = spent * 0.6
    print(f"\n=== 用例 2：预算收紧到 {tight:,.0f} um^2（实测总量的 60%）===", flush=True)
    tight_report = ModuleDialogue(gate, source_root=source, order=order).build(
        None, area_budget_um2=tight
    )
    for item in tight_report.outcomes:
        area = f"{item.area_um2:>10,.1f}" if item.area_um2 is not None else "         -"
        print(f"  {'PASS' if item.passed else 'FAIL'}  {item.module:<14s} {area} um^2")
    print(f"  造了 {len(tight_report.outcomes)}/{len(order)} 个就停了")
    for c in tight_report.discovered_constraints:
        print(f"  发现的约束: {c}")
PYEOF
echo "退出码 $?"
