#!/usr/bin/env bash
#SBATCH --job-name=fast-synth
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1 --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=03:00:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# 面积、时序、功耗：全部来自工具，不是模型。
#
# 三者共用同一份综合网表：yosys 出面积并写出映射网表，OpenSTA 在那份网表上
# 出关键路径和功耗。共用一份网表是必要的——否则面积和时序可能在描述两个
# 不同的电路。
#
# 功耗的 alpha（翻转率）从**实际施加的金标准激励**里数出来，不取工具默认值。
# 动态功耗严格正比于 alpha：实测同一网表下 alpha 从 0.05 到 0.50，功耗从
# 1.199 mW 到 11.854 mW（10 倍），而泄漏恒定 14.8 uW。默认常数给出的功耗
# 和稀疏度完全无关——而 DynaX 省的恰恰就是翻转。
#
# 工艺不是论文的 28nm 商业库（我们没有那个 PDK），是开源的 Nangate45。
# 绝对面积不能和论文的 1.08 / 6.05 mm^2 比；设计之间的相对面积可以，
# 而那正是协同优化器需要的——它的一阶面积公式从来没有被任何工具校准过。
#
# 为什么用容器而不是 pip：`yowasp-yosys` 装得上，但 WASI 起不了外部进程，
# 综合会在 ABC 那一步静默停下并返回 0——一个「成功」但没有任何映射结果的跑。
# 容器里的 yosys 0.36 自带 abc。
set -uo pipefail

ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
SIF="$ROOT/containers/yosys.sif"
STA="$ROOT/containers/opensta.sif"
LIB="$ROOT/pdk/nangate45/NangateOpenCellLibrary_typical.lib"
OUT="$ROOT/runs/synth_${SLURM_JOB_ID}"
export APPTAINER_TMPDIR=/tmp APPTAINER_CACHEDIR=/tmp/apptainer-cache
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

export TMPDIR=/tmp/fast-synth-$$
mkdir -p "$TMPDIR" "$OUT" /tmp/apptainer-cache "$(dirname "$LIB")" "$ROOT/containers"

echo "node=$(hostname) out=$OUT"

if [ ! -f "$SIF" ]; then
    echo "=== 拉取 yosys 镜像 ==="
    apptainer pull --force "$SIF" docker://hdlc/yosys:latest 2>&1 | tail -2
fi
if [ ! -f "$STA" ]; then
    echo "=== 拉取 OpenSTA 镜像 ==="
    # 二进制在 /OpenSTA/build/sta，不在 PATH 里——镜像的 entrypoint 指向它。
    apptainer pull --force "$STA" docker://openroad/opensta:latest 2>&1 | tail -2
fi
if [ ! -f "$LIB" ]; then
    echo "=== 取 Nangate45 标准单元库 ==="
    curl -sL -o "$LIB" \
      https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-flow-scripts/master/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib
fi
apptainer exec "$SIF" yosys -V 2>&1 | head -1

echo; echo "=== 1. elaborate 全部目标 ==="
cd "$REPO/FAST/hardware"
scala-cli run chisel --workspace "$SCALA_BUILD_WS" --server=false --main-class Elaborate -- ALL "$OUT/rtl" 2>&1 \
    | grep -vE "^(Download|Downloaded|Compiling|Compiled)" | tail -5

echo; echo "=== 2. 生成金标准激励（用于数出翻转率 alpha） ==="
# 功耗的 alpha 必须来自实际施加的激励。没有它就只能用默认常数，那样算出的
# 功耗和稀疏度无关——对稀疏加速器等于没有信息量。
mkdir -p "$OUT/golden"
for SPEC in "ExpUnit|--module ExpUnit" "PSumSoftmax|--module PSumSoftmax" \
            "SRAM|--module SRAM" "RePE|--module RePE" \
            "PrePE_1_2|--module PrePE --out-bits 12" \
            "TopK|" "RePEArray_S|--module RePEArray --num-rows 32 --pe-count 4 --reg-width 8" \
            "PrePEArray_S|--module PrePEArray --height 32 --width 32 --out-bits 12"; do
    NAME=${SPEC%%|*}; GARGS=${SPEC#*|}
    # shellcheck disable=SC2086
    PYTHONPATH="$REPO/FAST/hardware" "$ROOT/env/dynax-py312/bin/python" \
        "$REPO/FAST/hardware/gen_golden.py" --out "$OUT/golden/$NAME.json" $GARGS \
        > /dev/null 2>&1 && echo "  $NAME ok" || echo "  $NAME 跳过"
done

echo; echo "=== 3. 逐个综合 ==="
cd "$REPO/FAST"
# -u：输出重定向到文件时 Python 默认块缓冲，作业跑十几分钟却一行不出，
# 分不清是慢还是卡住了。
PYTHONPATH="$REPO/FAST" "$ROOT/env/fast-py312/bin/python" -u scripts/synthesize_modules.py \
    --rtl "$OUT/rtl" --container "$SIF" --liberty "$LIB" \
    --sta-container "$STA" --period-ns 2.0 --golden-dir "$OUT/golden" \
    --out "$OUT/synthesis.json" --log-dir "$OUT/logs"
echo "综合退出码: $?"
