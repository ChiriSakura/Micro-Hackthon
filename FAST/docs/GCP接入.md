# FAST 接入 GCP：现状、约束与执行顺序

> 更新时间：2026-09-04  
> 控制端：NYU Torch 集群 `torch-login-b-3`  
> 相关文件：[`configs/chia/fast-gcp.yaml.example`](../configs/chia/fast-gcp.yaml.example)、[`scripts/gcp_preflight.py`](../scripts/gcp_preflight.py)

## 1. 本轮已经验证的事实

| 项目 | 结论 | 证据 |
|---|---|---|
| CHIA 原生支持 GCP | 支持。`chia/cluster/gcp_nodes.py` 提供 provision/discover/teardown/firewall，凭据走 ADC | 762 行源码，`parse_gcp_nodes` 解析通过 |
| FAST 集群模板可解析 | 通过。`cluster_name=fast-gcp`，`e2-standard-4`，`spot=true`，两类节点资源标签正确 | `chia.cluster.config.load_config` + `parse_gcp_nodes` |
| ADC 凭据可用 | 已就位（`authorized_user`），Compute API 实调成功 | `us-central1-a` 返回 0 台实例 |
| head 公钥登录 | 通过 `gz2522@10.32.51.123` | preflight 12/12 |
| `chia up --dry-run` | 通过，`Dry run complete. No changes made.`，worker 标记 `[tunneled]` | 见第 4 步 |
| worker 引导 | `scripts/gcp_worker_bootstrap.sh`，幂等，装 Python 3.12 venv + chialoops | 11 个渲染器测试 |
| 控制端出站 SSH | 放行。登录节点可建立到公网 22 端口的连接 | `github.com:22`、`bitbucket.org:22` 均连通 |
| 控制端出站 HTTPS | 放行 | `googleapis.com`、`huggingface.co` 均连通 |
| 跨网络 Ray 连接 | CHIA 用 `ssh -N` 反向隧道把 worker 接回 head，head 不需要公网入站 | `chia/cluster/tunnel.py` |
| gcloud CLI | 已安装到 `/scratch/gz2522/gz2522/tmp/micro-hackthon/tools/google-cloud-sdk`，无 root | 用户级 tarball 安装 |
| `google-cloud-compute` | 已安装到 `env/fast-py312` | `import google.cloud.compute_v1` 通过 |

## 2. 尚未满足的前置条件

1. **没有预算保护。** 预算告警只会报警，不会封顶；唯一可靠的止血手段是 `chia down`
   加上事后用 `gcp_list_instances.py` 复核 zone。
2. **默认 VPC 的 `default-allow-ssh` 对 0.0.0.0/0 开放 22 端口。** 这是项目创建时
   就存在的 GCP 默认规则，不是本项目引入；CHIA 自己建的规则是收紧的（只放行
   `216.165.12.15/32`）。设 `CHIA_GCP_LOCKDOWN_DEFAULT_SSH=1` 可让 chia 删掉它。
3. **worker 引导里 apt 那一步耗时不稳定。** 实测在 30 秒到 15 分钟之间波动，
   而这是计费时间。走 uv 路径时其实只需要 `build-essential git curl`，
   `python3.12-venv` 等包可以省掉，值得再削。

已经解决的（保留在此以免重复排查）：专用 SSH 密钥 `~/.ssh/fast_gcp_ed25519` 已生成
并在配置中与 head 密钥分开；FAST 包通过 Ray `runtime_env` 的 `py_modules` 下发，
已在云端 worker 上实测 import 成功。

## 3. 两条可选拓扑

### 3.1 Head 在 Torch 集群（推荐先验证）

```text
Torch 登录/计算节点（CHIA head, Ray head）
        │ ssh -N -R 反向隧道（出站 22）
        ▼
GCP e2-standard-4 spot worker（Ray worker，Verilator/综合）
```

- 优点：实验数据库、缓存、报告都留在 scratch；DynaX GPU 评估仍在 Slurm。
- 约束：head 不能长期跑在登录节点，正式运行应放进 `cpu_short` 作业内，并在作业结束前执行 `chia down`。

### 3.2 Head 在 GCP

适合无人值守的批量 Verilator 运行，但会额外产生一台常驻 VM 的费用，且实验产物需要回传。第一次连通验证不建议采用。

## 4. 执行顺序

每一步都要先确认上一步的输出，不要跳过 dry-run。

```bash
cd /home/gz2522/Micro-Hackthon/FAST
source /scratch/gz2522/gz2522/tmp/micro-hackthon/env/fast-py312/bin/activate
export CLOUDSDK_PYTHON=/scratch/gz2522/gz2522/tmp/micro-hackthon/env/fast-py312/bin/python
export GCLOUD_BIN=/scratch/gz2522/gz2522/tmp/micro-hackthon/tools/google-cloud-sdk/bin/gcloud
```

**第 1 步：认证。** 二选一。

```bash
# 方式 A：在本集群交互登录（会打印 URL，需要在浏览器完成并粘贴回授权码）
"$GCLOUD_BIN" auth application-default login --no-launch-browser
"$GCLOUD_BIN" auth application-default set-quota-project project-842e7b1d-4f04-40b2-9b0

# 方式 B：把 Windows/WSL 上已有的 ADC 文件复制过来
#   源：%APPDATA%\gcloud\application_default_credentials.json
mkdir -p ~/.config/gcloud && chmod 700 ~/.config/gcloud
# 复制后：
chmod 600 ~/.config/gcloud/application_default_credentials.json
```

**第 2 步：专用 SSH 密钥。**

```bash
ssh-keygen -t ed25519 -f ~/.ssh/fast_gcp_ed25519 -N ''
chmod 600 ~/.ssh/fast_gcp_ed25519
```

**第 3 步：环境变量与配置。**

```bash
# 不要用 `hostname -I | awk '{print $1}'`：第一个地址是虚拟地址 10.0.2.2，
# CHIA 的 head SSH 探测会失败。回环地址同样不行（sshd 在回环上只提供
# gssapi/password，不接受公钥）。必须用真实地址。
export HEAD_IP=10.32.51.123
export FAST_SSH_USER=gz2522
export FAST_HEAD_ENV=/scratch/gz2522/gz2522/tmp/micro-hackthon/env/fast-py312
export GCP_PROJECT=project-842e7b1d-4f04-40b2-9b0
export GCP_PRIVATE_KEY_PATH=$HOME/.ssh/fast_gcp_ed25519

# 模板不能直接用：worker 引导脚本要注入，Python/Ray 版本要和 head 对齐。
# Ray 拒绝加入 Python 次版本或 Ray 版本不同的集群，且报错看起来像网络问题。
cd /home/gz2522/Micro-Hackthon
python FAST/scripts/gcp_render_cluster.py \
    --template FAST/configs/chia/fast-gcp.yaml.example \
    --out FAST/configs/chia/fast-gcp.yaml
# 需要 Verilator / Chisel 时加 --with-verilator --with-chisel；
# 首次验证链路不要加，装得快。
```

**第 4 步：预检（不创建任何资源、不产生费用）。**

```bash
python FAST/scripts/gcp_preflight.py --config FAST/configs/chia/fast-gcp.yaml
```

逐项检查依赖、gcloud、ADC、Compute API 实调、配置解析、head 公钥登录和费用护栏。
必须 12/12 全过才进入下一步。当前实测结果就是 12/12。

**第 5 步：dry-run。**

```bash
chia up --dry-run FAST/configs/chia/fast-gcp.yaml
```

确认三件事：机型和数量与预期一致；worker 那行带 `[tunneled]`；结尾是
`Dry run complete. No changes made.`。

**第 6 步：真实创建，并立刻确认销毁路径可用。**

```bash
chia up --yes FAST/configs/chia/fast-gcp.yaml
# 验证 Ray 是否看到 worker 资源标签
python -c "import ray; ray.init(address='auto'); print(ray.cluster_resources())"
# 批次结束后立即执行
chia down FAST/configs/chia/fast-gcp.yaml
"$GCLOUD_BIN" compute instances list --project "$GCP_PROJECT"
```

最后一条 `instances list` 必须返回空，才算真正释放。

## 5. 费用纪律

- 预算约 300 美元试用额度，提案估算约 1207 美元，因此云端只承担 CPU 侧 Verilator、编排和低成本综合，不承担大模型 GPU。
- 首次验证用 `e2-standard-4`（按需约 0.134 USD/h）而不是 `c3-standard-8`（约 0.414 USD/h）：
  免费试用配额未必允许 c3，且链路验证不需要那么多核。跑通后再用渲染器的
  `--machine-type` 放大。
- **spot 只要实例存在就在计费**，抢占是可用性风险，不是省钱机制。
- FAST 的内容哈希缓存保证被抢占时只重跑单个候选，不会重跑整批。
- 每次创建资源前先跑预检的费用估算；每批结束后立刻 `chia down` 并用 `instances list` 复核。
- 免费试用不提供 GPU 配额，不要把额度当作 GPU 训练预算。

## 6. 与 FireSim / AWS 的边界

CHIA 的 FireSim 实现面向 AWS F2 与 S3，不在 GCP 上运行。GCP 阶段只负责编排与 CPU 级评估；FireSim 高保真验证仍是独立的 AWS 阶段，需要单独的账号、F2 配额和预算。


## 7. 排错

| 症状 | 原因 |
|---|---|
| preflight 报依赖全部缺失 | gcloud 的 bin 被 prepend 到 PATH 前面，`python` 解析到了它自带的解释器。要 append 到末尾，或直接用 venv 的绝对路径调用 |
| head SSH 探测失败 | `head_ip` 写成了 `127.0.0.1` / `localhost` / `10.0.2.2` |
| worker 起来了但 Ray 不加入 | Python 次版本或 Ray 版本与 head 不一致。看 worker 上的 `~/fast_bootstrap.log`，脚本本身会在不一致时直接报错退出 |
| 引导超时 | 镜像不是 ubuntu-2404-lts，脚本回退到 deadsnakes PPA 编译路径。换镜像，或提高渲染器的 `--setup-timeout` |
| worker 很慢很卡 | 声明的 `fast_cpu` 超过实际 vCPU，Ray 超额调度。重新渲染会按机型名自动收敛 |
| 建实例报 404 `image ... was not found` | 镜像家族名错。Ubuntu 24.04 起家族名带架构后缀，是 `ubuntu-2404-lts-amd64` 而不是 `ubuntu-2404-lts`。preflight 现在会提前解析镜像，这类错误不再需要动到真实资源 |
| `chia down` 卡住或报 `EOFError` | 它默认会交互确认。脱离终端运行时必须加 `-y`，否则销毁失败、实例继续计费 |

### 实测记录（2026-09-04 七次真实拉起，第 7 次全链路通过）

**第 7 次跑通了完整链路**，作业 `16985131`，20 分 28 秒，`COMPLETED`：

```text
render → preflight 14/14 → dry-run → chia up → 集群成型
       → 五 Agent 图在 GCP worker 上执行 → chia down → zone 复核为空
```

决定性证据（`cloud_report.json`）：

```json
"ran_on":       "chia-fast-gcp-fast-cpu-worker-0",
"worker_ip":    "127.0.0.2",
"head_ip":      "10.32.36.64",
"worker_python": "3.12.9",
"worker_ray":    "2.54.0",
"functional_passed": true,
"decision": "continue"
```

`ran_on` 是 GCP 实例的主机名而不是 head，且 `cloud_smoke.py` 中"任务落回 head 即
`SystemExit`"的检查没有触发，因此这是真实的远程执行，不是静默回退。集群资源为
`6.0 CPU`（head 2 + worker 4）、`fast_cpu 4.0`、`fast_chisel 1.0`、`fast_verilator 4.0`，
两个节点均 alive，五个 Agent 全部 `passed`，Critic 归因 compiler、决定 `continue`。

七次累计花费不到 0.05 美元，每次都由 EXIT trap 回收并独立复核 zone。

### 七次的失败与修复

| # | 卡在哪 | 根因 | 修复 |
|---|---|---|---|
| 1 | 建实例 404 | 镜像家族 `ubuntu-2404-lts` 不存在，24.04 起带 `-amd64` 后缀 | 改名；preflight 增加 `check_images` |
| 2 | 建隧道 | `HEAD_IP` 写死为另一台登录节点 | 推导本机地址；preflight 增加 `check_head_is_local` |
| 3 | head `ray start` 超时 | 登录节点 28 核约 140 用户，Ray 按核数预启动 28 个 worker | `--num-cpus=2 --object-store-memory=1GB` |
| 4 | `[Errno 28] No space left` | 登录节点 `/tmp` 是被他人占满的 2 GB tmpfs | head 迁入 Slurm 计算节点 |
| 5 | worker 起 Ray | head 的 session 路径在 `/scratch`，云端不存在 | head 加 `--temp-dir=/tmp/ray` |
| 6 | worker 起 Ray | Ray 比较**完整** Python 版本，3.12.9 ≠ 3.12.3 | 渲染器传完整版本；引导用 uv 装精确 CPython |
| 7 | — | — | **全链路通过** |

第 5、6 两条特别值得记住：

- Ray 的 session 目录路径由 head 决定，worker 按**同一个绝对路径**去建。
  head 若继承了集群的 `TMPDIR=/scratch/...`，云端 worker 必然 `EACCES`。
- Ray 的版本校验比较 `X.Y.Z`。只对齐次版本会顺利通过引导脚本自己的检查，
  然后在 worker 加入集群时才被 Ray 拒绝——即在实例已经计费之后。
  head 的 Python 在登录节点是 3.12.14、在计算节点是 3.12.9，所以这个版本
  必须在**将要充当 head 的那台机器上**动态取，不能写死。

### 历史记录（第 1 次）

四次 `chia up --yes`，每次都被 teardown 正确回收，zone 事后都复核为空。
累计运行时间约 20 分钟 e2-standard-4 spot，费用不到 0.02 美元。

| # | 走到哪一步 | 失败原因 | 修复 |
|---|---|---|---|
| 1 | 建防火墙 → 建实例 404 | 镜像家族名 `ubuntu-2404-lts` 不存在，24.04 起带架构后缀 | 改 `ubuntu-2404-lts-amd64`；preflight 增加 `check_images` 提前解析 |
| 2 | 实例+引导成功 → 建隧道失败 | `HEAD_IP` 写死成了另一台登录节点，`bind: Cannot assign requested address` | `gcp_env.sh` 改为推导本机地址；preflight 增加 `check_head_is_local` |
| 3 | 实例+引导成功 → head `ray start` 超时 | 登录节点 28 核、~140 用户，Ray 按核数预启动 28 个 worker，raylet 错过启动 deadline | `head_start_ray_commands` 加 `--num-cpus=2 --object-store-memory=1GB` |
| 4 | head Ray 起来了 → `[Errno 28] No space left on device` | 登录节点 `/tmp` 是 **2GB tmpfs**，被其他用户占满（1.2G 的 `/tmp/pdbgen` 等） | 见下：head 必须搬进 Slurm 作业 |

已经证实可用的部分：

- worker 引导脚本在真机上 **68 秒**跑完（apt 30s、venv 3s、pip 35s），
  输出 `ready: python 3.12, ray 2.54.0, chia import ok`
- Ubuntu 24.04.4 自带 Python 3.12.3，与 head 的 3.12 次版本一致
- CHIA 建的防火墙规则是收紧的，只放行登录节点出口 IP `216.165.12.15/32`
- 专用 SSH 密钥 `~/.ssh/fast_gcp_ed25519` 生效，登录凭据没有交给云主机
- teardown 的 EXIT trap 四次全部正确触发

第 4 次的教训最重要：**登录节点不能作为 CHIA head**。不是配置问题，是环境约束——
Ray 的 session 目录在 `/tmp`，而登录节点的 `/tmp` 是 138 个用户共享的 2GB tmpfs，
随时可能被别人占满，且我们无权清理。正确做法是把 head 放进 `cpu_short` 作业里的
计算节点（项目计划书第 8 节本来就是这么写的），前提是计算节点能出站 SSH 到 GCP。

### 历史记录（第 1 次）

第一次 `chia up --yes` 失败在镜像家族名，序列是：建防火墙规则 → 建实例 404 →
teardown。两个教训已经修进代码：

1. preflight 增加 `check_images`，用一次只读 API 调用提前解析镜像家族。
   原来这个错误要等到 CHIA 已经创建完防火墙规则才暴露。
2. 编排脚本的 teardown 改用 `chia down -y`，并增加兜底：`chia down` 失败时
   用 `scripts/gcp_delete_instances.py` 按 `chia-cluster` 标签直接删实例。
   兜底路径不依赖 CHIA 能跑，也不依赖有交互终端。

CHIA 还报了一条值得注意的告警：

```
Network has a world-open 'default-allow-ssh' rule (tcp:22 from 0.0.0.0/0, all instances).
chia's targeted rule does not remove it. Set CHIA_GCP_LOCKDOWN_DEFAULT_SSH=1 to delete it.
```

CHIA 自己建的规则是收紧的（只放行登录节点出口 IP `216.165.12.15/32`），但 GCP
默认 VPC 自带的 `default-allow-ssh` 对全网开放 22 端口。这是项目创建时就存在的
默认规则，不是本项目引入的。正式使用前应当处理掉。

## 8. 相关文件

| 文件 | 作用 |
|---|---|
| `scripts/gcp_worker_bootstrap.sh` | worker 引导脚本，幂等；版本不匹配时直接报错退出 |
| `scripts/gcp_render_cluster.py` | 把引导脚本注入模板并对齐版本/资源，生成可用配置 |
| `scripts/gcp_preflight.py` | 只读预检，不创建任何资源 |
| `configs/chia/fast-gcp.yaml.example` | 模板（**不要直接喂给 chia**，先渲染） |
| `configs/chia/fast-gcp-head.yaml.example` | head 也放 GCP 的备选拓扑 |
| `scripts/gcp_bringup_test.sh` | 一次受控的端到端拉起：渲染→预检→dry-run→创建→验证→销毁。销毁在 EXIT trap 里 |
| `scripts/gcp_delete_instances.py` | 兜底销毁，按标签删实例；不带 `--yes` 只列出不删 |
| `scripts/gcp_list_instances.py` | 只读列实例；zone 为空时退出码 0，有残留时 2 |
| `scripts/gcp_env.sh` | 统一环境变量，PATH 顺序和真实 HEAD_IP 都已固定 |
| `fast/runtime/runtime_env.py` | 用 Ray `py_modules` 把 FAST 包下发到 worker |
| `fast/runtime/cloud_smoke.py` | 云端验证，**强制证明任务落在远端**，落回 head 直接失败 |
