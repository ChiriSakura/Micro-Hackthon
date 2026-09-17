#!/usr/bin/env bash
#SBATCH --job-name=fast-codesign-l2
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=64G --time=03:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# 端到端协同设计，评估走 **L2 真实 RTL 仿真**。
#
# 这是第一次让整条链在真实测量上闭合：Kernel 的真实困惑度 -> 规划 ->
# 按计划造出设计 -> 真实 Q/K/V 逐维比对 -> Critic 归因。
#
# 在此之前，循环只在解析模型上跑过——而那个模型是 planner 自己用来挑设计的
# 那一个，它给出的「一致」是算术不是确认。
set -uo pipefail
ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
OUT="$ROOT/runs/codesign_${SLURM_JOB_ID}"
export PATH=/share/apps/openjdk/21.0.3/bin:$ROOT/tools:$PATH
export COURSIER_CACHE="$ROOT/cache/coursier" SCALA_CLI_HOME="$ROOT/cache/scala-cli"
export APPTAINER_TMPDIR=/tmp APPTAINER_CACHEDIR=/tmp/apptainer-cache
export TMPDIR=/tmp/cds-$$; mkdir -p "$TMPDIR" "$OUT" /tmp/apptainer-cache
# 约束是输入：不给就用 ArchSpecs 的默认值（面积 4 mm^2 / 频率 350 MHz /
# 功耗不限）。精度那条 eps 跟着 kernel 搜索报告进来，不在这里给。
#   MAX_AREA_UM2=2800000 MAX_POWER_MW=500 TARGET_MHZ=400 sbatch ...
export GCP_PROJECT=${GCP_PROJECT:-project-842e7b1d-4f04-40b2-9b0}
export GCP_LOCATION=${GCP_LOCATION:-us-central1}

# FAST_LLM=1 让 Compiler 和 Critic 走真实 Vertex 调用。默认关，因为它引入
# 网络依赖：一次因为出网失败而静默回退的运行，和一次确定性运行长得一样。
LLM_FLAG=""
[ "${FAST_LLM:-0}" = "1" ] && LLM_FLAG="--llm"

# FAST_MUTATE_RTL=1：归因到 µArch 时**真的改写 Chisel**（LLM 改 + 机械门验证）。
# 不开的话「保计划、重新实现」是空转——`UArchAgent.run()` 是计划的纯函数。
#
# BlockScheduler / KeyFeeder 的门要真实工作量激励，所以顺带把最近一次抓取
# 找出来；找不到时那两个模块的门会**明确失败**而不是静默通过。
if [ "${FAST_MUTATE_RTL:-0}" = "1" ]; then
    LLM_FLAG="$LLM_FLAG --mutate-rtl --mutate-attempts ${MUTATE_ATTEMPTS:-3}"
    WL=$(ls -t "$ROOT"/runs/workload_*/workload_rows32.json 2>/dev/null | head -1)
    [ -n "$WL" ] && LLM_FLAG="$LLM_FLAG --workload $WL"
    LLM_FLAG="$LLM_FLAG --containers $ROOT/containers"
    # 金标准生成要 torch，FAST 自己的环境没有——用 DynaX 的那个解释器。
    LLM_FLAG="$LLM_FLAG --gate-python $ROOT/env/dynax-py312/bin/python"
    # 时序/面积类症状要综合 + STA 才测得到目标。缺哪个就报「没测」，
    # 不会静默当成「时序没问题」。
    LIB=$(ls "$ROOT"/pdk/nangate45/*.lib 2>/dev/null | head -1)
    [ -n "$LIB" ] && LLM_FLAG="$LLM_FLAG --liberty $LIB"
    [ -f "$ROOT/containers/opensta.sif" ] && \
        LLM_FLAG="$LLM_FLAG --sta-container $ROOT/containers/opensta.sif"
    echo "µArch RTL 变异：开（工作量 ${WL:-未找到——BlockScheduler/KeyFeeder 的门会失败}）"
fi

SEARCH=${SEARCH_JSON:-$(ls -t "$ROOT"/runs/kernel_search_*/*.json 2>/dev/null | head -1)}
[ -f "$SEARCH" ] || { echo "找不到 kernel 搜索结果"; exit 2; }

cd "$REPO/FAST"
PYTHONPATH="$REPO/FAST" "$ROOT/env/fast-py312/bin/python" -u scripts/run_codesign.py \
    --search "$SEARCH" \
    --candidates "${CANDIDATES:-3}" \
    --rounds "${ROUNDS:-3}" \
    --capture-root "$ROOT/runs" \
    --head-dim "${HEAD_DIM:-64}" \
    --repo-root "$REPO" \
    ${MAX_AREA_UM2:+--max-area-um2 $MAX_AREA_UM2} \
    ${MAX_POWER_MW:+--max-power-mw $MAX_POWER_MW} \
    ${TARGET_MHZ:+--target-mhz $TARGET_MHZ} \
    $LLM_FLAG \
    --out "$OUT/codesign.json"
echo "退出码 $?"
