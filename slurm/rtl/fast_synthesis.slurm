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

# 用 yosys + Nangate45 综合每个模块，得到工具量出来的单元面积。
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
LIB="$ROOT/pdk/nangate45/NangateOpenCellLibrary_typical.lib"
OUT="$ROOT/runs/synth_${SLURM_JOB_ID}"
export APPTAINER_TMPDIR=/tmp APPTAINER_CACHEDIR=/tmp/apptainer-cache
export PATH=/share/apps/openjdk/21.0.3/bin:$ROOT/tools:$PATH
export COURSIER_CACHE="$ROOT/cache/coursier" SCALA_CLI_HOME="$ROOT/cache/scala-cli"
export TMPDIR=/tmp/fast-synth-$$
mkdir -p "$TMPDIR" "$OUT" /tmp/apptainer-cache "$(dirname "$LIB")" "$ROOT/containers"

echo "node=$(hostname) out=$OUT"

if [ ! -f "$SIF" ]; then
    echo "=== 拉取 yosys 镜像 ==="
    apptainer pull --force "$SIF" docker://hdlc/yosys:latest 2>&1 | tail -2
fi
if [ ! -f "$LIB" ]; then
    echo "=== 取 Nangate45 标准单元库 ==="
    curl -sL -o "$LIB" \
      https://raw.githubusercontent.com/The-OpenROAD-Project/OpenROAD-flow-scripts/master/flow/platforms/nangate45/lib/NangateOpenCellLibrary_typical.lib
fi
apptainer exec "$SIF" yosys -V 2>&1 | head -1

echo; echo "=== 1. elaborate 全部目标 ==="
cd "$REPO/FAST/hardware"
scala-cli run chisel --server=false --main-class Elaborate -- ALL "$OUT/rtl" 2>&1 \
    | grep -vE "^(Download|Downloaded|Compiling|Compiled)" | tail -5

echo; echo "=== 2. 逐个综合 ==="
cd "$REPO/FAST"
PYTHONPATH="$REPO/FAST" "$ROOT/env/fast-py312/bin/python" scripts/synthesize_modules.py \
    --rtl "$OUT/rtl" --container "$SIF" --liberty "$LIB" \
    --out "$OUT/synthesis.json" --log-dir "$OUT/logs"
echo "综合退出码: $?"
