#!/usr/bin/env bash
#SBATCH --job-name=fast-gate-check
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=32G --time=01:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# 验证 `LocalRtlGate` 对着真实工具链真的能用。
#
# 这个门是 µArch 内循环的全部判据。**一个从没跑过真实工具链的门，看起来
# 和能用的门一模一样**——三级都返回 GateResult，测试里用假 gate 全过。
#
# 两个用例：
#   1. 未改动的模块 -> 三级全过
#   2. 故意改坏的模块 -> 在哪一级失败、诊断信息够不够定位
#
# 第 2 个才是重点。内循环能不能收敛，取决于失败消息能不能定位——只输出
# FAILED 的门会让它退化成盲目重试。
set -uo pipefail
ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
OUT="$ROOT/runs/gate_${SLURM_JOB_ID}"
export PATH=/share/apps/openjdk/21.0.3/bin:$ROOT/tools:$PATH
export COURSIER_CACHE="$ROOT/cache/coursier" SCALA_CLI_HOME="$ROOT/cache/scala-cli"
export APPTAINER_TMPDIR=/tmp APPTAINER_CACHEDIR=/tmp/apptainer-cache
export TMPDIR=/tmp/gate-$$; mkdir -p "$TMPDIR" "$OUT" /tmp/apptainer-cache

cd "$REPO/FAST"
PYTHONPATH="$REPO/FAST" "$ROOT/env/fast-py312/bin/python" -u - "$OUT" <<'PYEOF'
import shutil, sys
from pathlib import Path

from fast.agents.rtl_gate import LocalRtlGate, MODULES

out = Path(sys.argv[1])
root = Path("/scratch/gz2522/gz2522/tmp/micro-hackthon")
repo = Path("/home/gz2522/Micro-Hackthon")
gate = LocalRtlGate(
    repo=repo, work_root=out, containers=root / "containers",
    python=str(root / "env" / "dynax-py312" / "bin" / "python"),
    liberty=root / "pdk" / "nangate45" / "NangateOpenCellLibrary_typical.lib",
    timeout_seconds=900,
)

target = "TopK"
module = repo / "FAST/hardware/chisel/src/main/scala/predict_unit/topk.scala"
original = module.read_text(encoding="utf-8")

print(f"=== 用例 1：未改动的 {target} ===", flush=True)
for result in gate.check(module, target):
    mark = "PASS" if result.passed else "FAIL"
    print(f"  [{mark}] {result.stage:<11s} {result.metrics or ''}")
    if not result.passed:
        print("    " + result.diagnostics.replace("\n", "\n    ")[:1200])

print(f"\n=== 用例 2：故意改坏（把一个比较符反过来）===", flush=True)
# 反转一个比较：语法仍然合法，elaborate 会过，**只有仿真能抓到**。
# DynaX 的 6 个缺陷里有 2 个正是这种形状。
broken = original.replace("(a: UInt, b: UInt) => a > b", "(a: UInt, b: UInt) => a < b", 1)
if broken == original:
    import re
    m = re.search(r"(\w+)\s*>\s*(\w+)", original)
    if m:
        broken = original.replace(m.group(0), f"{m.group(1)} < {m.group(2)}", 1)
        print(f"  改的是: {m.group(0)} -> {m.group(1)} < {m.group(2)}")
    else:
        print("  找不到可反转的比较，跳过用例 2"); broken = None

if broken and broken != original:
    module.write_text(broken, encoding="utf-8")
    try:
        for result in gate.check(module, target):
            mark = "PASS" if result.passed else "FAIL"
            print(f"  [{mark}] {result.stage:<11s}")
            if not result.passed:
                print("    --- 诊断信息（内循环靠它定位）---")
                print("    " + result.diagnostics.replace("\n", "\n    ")[:1500])
    finally:
        module.write_text(original, encoding="utf-8")
        print(f"\n  已还原 {module.name}: {'一致' if module.read_text(encoding='utf-8') == original else '不一致！'}")
PYEOF
echo "退出码 $?"
