#!/usr/bin/env bash
#SBATCH --job-name=fast-hammer-syn
#SBATCH --account=torch_pr_674_tandon_advanced
#SBATCH --partition=cpu_short
#SBATCH --nodes=1 --ntasks=1 --cpus-per-task=8 --mem=24G --time=00:40:00
#SBATCH --output=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.out
#SBATCH --error=/scratch/gz2522/gz2522/tmp/micro-hackthon/runs/slurm/%x_%j.err

# **把 hammer 这条路固化下来。**
#
# hammer 综合在 2026-08 成功过一次（`runs/hammer_dbg3_17020942/` 里有
# 3433 行的 ExpUnitFixPoint.mapped.v），但那次用的是 `/tmp` 里一个临时 venv，
# 驱动脚本也没留下。**可用配置没有被固化，所以它没能进 agent loop**——
# 而代码注释里只留下修复**之前**写的「跑不通」，从此没人回去改。
#
# 配置不是猜的，是从那次成功运行的 `config_db_tmp.json` 里考古出来的：
#
#     technology.nangate45.install_dir = <补丁过的 PDK>
#     technology.core.stackup          = nangate45_3Ma_3Mb_2Mc_2Md
#     vlsi.core.node                   = 45
#
# ## hammer 必须待在自己的 venv 里
#
# `hammer-vlsi 1.2.0` 依赖 **pydantic 1.x**，而 `google-genai`（LLM 通路）、
# `chialoops`、`mcp` 都要 pydantic 2.x。装进共享环境会把 LLM 通路整个打坏
# ——我试过一次，确实坏了。所以这里用独立的 `env/hammer-py312`，
# 靠**子进程**调用，和 yosys / OpenSTA 容器同一个形态。
set -uo pipefail
ROOT=/scratch/gz2522/gz2522/tmp/micro-hackthon
REPO=/home/gz2522/Micro-Hackthon
OUT="$ROOT/runs/hammer_${SLURM_JOB_ID}"
HPY="$ROOT/env/hammer-py312/bin/python"
PDK="$ROOT/pdk/hammer45"
export PATH=/share/apps/openjdk/21.0.3/bin:$ROOT/tools:$PATH
export COURSIER_CACHE="$ROOT/cache/coursier" SCALA_CLI_HOME="$ROOT/cache/scala-cli"
export SCALA_BUILD_WS="$ROOT/tmp/scala-build-${SLURM_JOB_ID:-$$}"
export TMPDIR="$ROOT/tmp/hammer-$$"
mkdir -p "$SCALA_BUILD_WS" "$OUT" "$TMPDIR"

TARGET="${TARGET:-ExpUnit}"
echo "=== 1. 打 PDK 补丁（幂等）==="
#
# **不能只 --check。** tech.json 补丁打在 **hammer 包内部**，不在 PDK 目录里
# ——换一个 venv 就没了。实测：新建 `env/hammer-py312` 之后 --check 直接报
# `decimal.ConversionSyntax`，因为补丁从来没打到这个 install 上。
#
# 脚本是幂等的（修的是数据不是逻辑），所以每次跑都打一遍，作业因此自愈。
"$HPY" "$REPO/FAST/scripts/setup_hammer_nangate45.py" --pdk-root "$PDK" 2>&1 | tail -10
"$HPY" "$REPO/FAST/scripts/setup_hammer_nangate45.py" --pdk-root "$PDK" --check 2>&1 | tail -3

echo; echo "=== 2. elaborate $TARGET ==="
cd "$REPO/FAST/hardware"
scala-cli run chisel --workspace "$SCALA_BUILD_WS" --server=false \
    --main-class Elaborate -- "$TARGET" "$OUT/rtl" 2>&1 | grep -E "ELABORATE|error" | tail -3
V=$(find "$OUT/rtl" -name "*.v" | head -1)
[ -z "$V" ] && { echo "FAIL: 没有 Verilog"; exit 1; }
TOP=$(grep -oP '^module \K\w+' "$V" | tail -1)
cp "$V" "$OUT/$TOP.v"
echo "顶层 $TOP"

echo; echo "=== 3. hammer 综合 ==="
cat > "$OUT/syn.yml" <<YML
vlsi.core.technology: hammer.technology.nangate45
vlsi.core.node: 45
vlsi.core.synthesis_tool: hammer.synthesis.yosys
vlsi.core.build_system: none
vlsi.core.max_threads: ${SLURM_CPUS_PER_TASK:-8}
technology.nangate45.install_dir: "$PDK"
technology.core.stackup: nangate45_3Ma_3Mb_2Mc_2Md
technology.core.std_cell_rail_layer: metal1
technology.core.std_cell_supplies:
  power: ["VDD"]
  ground: ["VSS"]
synthesis.inputs.top_module: $TOP
synthesis.inputs.input_files: ["$OUT/$TOP.v"]
synthesis.clock_gating_mode: auto
# 不声明时钟的话 yosys 插件在 `get_clock_ports()[0]` 越界。
vlsi.inputs.clocks:
  - name: clock
    period: "2ns"
    uncertainty: "0.1ns"
YML
# hammer 的 yosys 插件**无论如何都会发** `techmap -map <file>`；没配就生成
# 字面量 `techmap -map None`，yosys 报 `Can't open input file 'None'`。
# 上一次成功的运行里也有这个空文件，解法是一样的。
cat > "$OUT/empty_latch_map.v" <<'VLOG'
// 空 latch map：hammer 的 yosys 插件无论如何都会发 techmap -map <file>
VLOG
cat >> "$OUT/syn.yml" <<YML
synthesis.yosys.latch_map_file: "$OUT/empty_latch_map.v"
YML

cd "$OUT"
# **PATH 必须带两样东西，都是踩出来的：**
#
#   env/hammer-py312/bin  —— hammer 会起子进程找 `hammer-shell-test`。
#     用绝对路径调 hammer-vlsi 时 venv 的 bin 不在 PATH，报
#     「hammer-shell does not appear to be on the path」。
#   tools/bin             —— hammer 直接 `Popen(['yosys', ...])`，而这个项目
#     的 yosys 在容器里。`tools/bin/yosys` 是转发脚本。
#
# 而且要用 `hammer-vlsi` 控制台脚本，不要 `python -m hammer.vlsi.cli_driver`：
# 后者有导入顺序问题，**退出码 0、零输出**，真实错误全被吞掉。
export PATH="$ROOT/tools/bin:$ROOT/env/hammer-py312/bin:$PATH"
hammer-vlsi syn -p "$OUT/syn.yml" --obj_dir "$OUT" 2>&1 | tail -20

echo; echo "=== 4. 产物 ==="
find "$OUT/syn-rundir" -name "*.mapped.v" -o -name "*.sdc" -o -name "*stat*" 2>/dev/null | head -6
M=$(find "$OUT" -name "*.mapped.v" | head -1)
[ -n "$M" ] && echo "映射后网表 $(wc -l < "$M") 行：$M" || echo "FAIL: 没有产出网表"
