#!/usr/bin/env bash
#SBATCH --job-name=fast-design-ppa
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=64G --time=03:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# 一份计划的整设计 PPA。**这是「拿到设计参数」的最后一步。**
#
# 逻辑走 yosys+OpenSTA，存储查 fakeram45 宏——hammer 的 nangate45
# sram_compiler 映射到的就是同一批宏，所以面积和功耗不需要 hammer 也能算对。
# hammer 额外给的是 P&R，那是另一个量级的工作。报的是**布局前**的数。
set -uo pipefail
ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
OUT="$ROOT/runs/ppa_${SLURM_JOB_ID}"
export PATH=/share/apps/openjdk/21.0.3/bin:$ROOT/tools:$PATH
export COURSIER_CACHE="$ROOT/cache/coursier" SCALA_CLI_HOME="$ROOT/cache/scala-cli"
# 每个作业用自己的 .scala-build。
#
# 共享的后果撞到过三次：所有作业都从同一个仓库路径跑 `scala-cli run chisel`，
# 于是并发提交时它们编译进**同一个** FAST/hardware/chisel/.scala-build。
# 表现是随机一两个作业报 `FAIL: predict_unit/PrePEArray_1_2` 或干脆不产出
# ELABORATE 行——看起来像 RTL 坏了，串行重跑就全过。
export SCALA_BUILD_WS="${TMPDIR:-/tmp}/scala-build-${SLURM_JOB_ID:-$$}"
mkdir -p "$SCALA_BUILD_WS"

export APPTAINER_TMPDIR=/tmp APPTAINER_CACHEDIR=/tmp/apptainer-cache
export TMPDIR=/tmp/ppa-$$; mkdir -p "$TMPDIR" "$OUT" /tmp/apptainer-cache

# 计划由脚本自己生成，不依赖外部文件。
#
# 原来默认指向 /tmp/plan.json——而 /tmp 是**节点本地**的，登录节点写的文件
# 计算节点看不到。一次提交要能独立复现整条链：kernel 结果 -> 规划 -> 造设计
# -> PPA。
PLAN=${PLAN_JSON:-$OUT/plan.json}
if [ ! -f "$PLAN" ]; then
  echo "=== 0. 规划 ==="
  PYTHONPATH="$REPO/FAST" "$ROOT/env/fast-py312/bin/python" - "$PLAN" <<'PYEOF'
import json, sys
from dataclasses import asdict
from fast.agents.compiler import CompilerAgent
from fast.agents.uarch import elaborate_spec, passes_for
from fast.schemas.models import ArchSpecs, KernelResult, Status

# 工作负载来自 Kernel Agent 的真实测量。这里用的是它跑出来的一个候选
# （xm:16:8:64，真实困惑度损失 0.01、稀疏度 0.85）。
kernel = KernelResult(
    status=Status.PASSED, baseline_metric=10.0, candidate_metric=10.1,
    metric_name="ppl", quality_loss=0.01, actual_sparsity=0.85,
    index_entropy=0.9, block_occupancy=0.42, trace_uri="kernel-search",
    sparse_method="xm:16:8:64",
)
# 只允许 16 位：8 位在 Q8.8 下一个整数位都不剩，设计造不出来。
plan = CompilerAgent(allow_unverified=True).plan(
    kernel, sequence_length=512, specs=ArchSpecs(data_widths=(16,)),
    budget=24, batch=8,
)
if plan.status is not Status.PASSED:
    sys.exit(f"规划失败: {plan.error}")
payload = asdict(plan)
payload["status"] = plan.status.value
json.dump(payload, open(sys.argv[1], "w"), indent=2)
print(f"  {elaborate_spec(plan, head_dim=64)}  ({passes_for(plan)} 趟)")
print(f"  预测: 面积 {plan.predicted_area_um2:,.0f} um^2 | "
      f"时钟 {plan.predicted_clock_ns:.3f} ns | 功耗 {plan.predicted_power_mw:.0f} mW")
PYEOF
fi
[ -f "$PLAN" ] || { echo "规划没有产出 $PLAN"; exit 2; }
SPEC=$("$ROOT/env/fast-py312/bin/python" -c "
import json,sys; sys.path.insert(0,'$REPO/FAST')
from fast.agents.uarch import elaborate_spec
from fast.schemas.models import CompilerSchedule, Status
d=json.load(open('$PLAN')); d['status']=Status(d['status'])
d['loop_order']=tuple(d['loop_order']); d['rationale']=tuple(d['rationale'])
print(elaborate_spec(CompilerSchedule(**d), head_dim=${HEAD_DIM:-64}))")
echo "计划: $SPEC"

echo; echo "=== 1. 按计划造出设计 ==="
cd "$REPO/FAST/hardware"
# 取数引擎和工作队列按计划的 bank 数/队列深度实例化。
BANKS=$("$ROOT/env/fast-py312/bin/python" -c "import json;print(json.load(open('$PLAN'))['bank_count'])")
QD=$("$ROOT/env/fast-py312/bin/python" -c "import json;print(json.load(open('$PLAN'))['queue_depth'])")
scala-cli run chisel --workspace "$SCALA_BUILD_WS" --server=false --main-class Elaborate -- "$SPEC" "$OUT/rtl" 2>&1 \
  | grep -E "^ELABORATE|FAIL"
scala-cli run chisel --workspace "$SCALA_BUILD_WS" --server=false --main-class Elaborate -- \
  "LIST:KeyFeeder_S${BANKS},BlockSched_S${QD}" "$OUT/rtl" 2>&1 | grep -E "^ELABORATE|FAIL"
# 综合脚本按固定目录名找，统一一下。
for pair in "KeyFeeder_S${BANKS}:KeyFeeder" "BlockSched_S${QD}:BlockScheduler"; do
  src=${pair%%:*}; dst=${pair##*:}
  [ -d "$OUT/rtl/$src" ] && ln -sfn "$OUT/rtl/$src" "$OUT/rtl/$dst"
done

echo; echo "=== 2. 整设计 PPA ==="
cd "$REPO/FAST"
PYTHONPATH="$REPO/FAST" "$ROOT/env/fast-py312/bin/python" -u scripts/legacy/design_ppa.py \
    --plan "$PLAN" --rtl-dir "$OUT/rtl" \
    --container "$ROOT/containers/yosys.sif" \
    --liberty "$ROOT/pdk/nangate45/NangateOpenCellLibrary_typical.lib" \
    --sta-container "$ROOT/containers/opensta.sif" --period-ns 2.5 \
    --work "$OUT/work" --out "$OUT/ppa.json"
echo "退出码 $?"
echo "结果 $OUT/ppa.json"
