# CHIA 使用 GCP 免费试用额度：配置与使用说明

## 1. 当前完成状态

截至 2026-09-03，已经完成：

- GCP CLI 登录账号：`zhanggenhao98@gmail.com`
- CHIA 目标项目：`project-842e7b1d-4f04-40b2-9b0`
- 项目已绑定计费账户，`billingEnabled: true`
- gcloud 默认项目已设为上述项目
- Application Default Credentials（ADC）已登录，并已设置 quota project
- Compute Engine API（`compute.googleapis.com`）已启用
- 默认 VPC 存在，`us-central1-a` 可使用 `e2-small`（2 vCPU、2048 MB）
- 当前项目没有任何 Compute Engine VM；配置过程尚未产生 VM 运行费用
- Windows `chia_env` 已验证：Python 3.10.19、CHIA 1.0.1、`google-cloud-compute` 1.51.0
- WSL2 Ubuntu 24.04 控制端已配置：Python 3.10.19、CHIA 1.0.1、`google-cloud-compute` 1.51.0
- WSL OpenSSH 服务已启用，并创建专用密钥：`~/.ssh/chia_gcp_ed25519`
- 集群配置文件：[gcp-cluster.yaml](gcp-cluster.yaml)

账号中还能看到两个没有绑定计费的项目：

- `gen-lang-client-0692941563`（`agent`）
- `project-724a12d8-7675-4036-8d6`（`My First Project`）

本配置不会使用或删除这两个项目。

## 2. 重要的计费说明

当前 GCP 免费试用通常提供 90 天、300 美元 Welcome credit。免费试用账户本身不会因云资源使用而自动扣银行卡；但如果点击 Google Cloud Console 中的 **Activate / Upgrade / 升级**，账户会变成付费账户，超出剩余额度或免费层的使用会向付款方式收费。

本配置使用 `e2-small` 和 24 GB 启动盘，是为了让 Ray/CHIA 初次验证更稳定。`e2-small` 不属于 Compute Engine 永久免费层的那台 `e2-micro`，因此会消耗 300 美元试用额度。不要把“免费试用额度”和“永久免费层”混为一谈。

建议每次实验结束立刻执行 `chia down`。预算提醒只能报警，不能自动封顶或自动停止资源。

## 3. 为什么从 WSL 运行

虽然 Windows 中的 `chia_env` 已经安装成功，但 CHIA 的集群管理会通过 SSH 执行 `bash --login`，云主机初始化也使用 Linux 命令。当前可实际运行的控制端是 WSL Ubuntu；请在 WSL 中执行后文所有 `chia` 命令，不要在 PowerShell 的 Windows conda 环境里执行 `chia up`。

## 4. 每次打开终端后的准备

从 PowerShell 进入 WSL：

```powershell
wsl -d Ubuntu-24.04
```

在 WSL 中执行：

```bash
cd /mnt/c/Users/11345/Desktop/MICRO_Hackthon/chia
source /home/sakura_02/miniconda3/etc/profile.d/conda.sh
conda activate chia_env
export GOOGLE_APPLICATION_CREDENTIALS=/mnt/c/Users/11345/AppData/Roaming/gcloud/application_default_credentials.json
```

快速检查：

```bash
python --version
chia --help
ssh -o BatchMode=yes -i ~/.ssh/chia_gcp_ed25519 sakura_02@127.0.0.1 hostname
```

如果 Windows 登录凭据失效，在 PowerShell 重新执行：

```powershell
gcloud.cmd auth login --update-adc
gcloud.cmd auth application-default set-quota-project project-842e7b1d-4f04-40b2-9b0
```

## 5. 创建集群

先做 dry-run。该命令只检查、展开并打印计划，不创建 VM：

```bash
chia up --dry-run gcp-cluster.yaml
```

确认计划中的项目、区域、机型和数量都正确后，再实际创建：

```bash
chia up gcp-cluster.yaml
```

命令会进行两次确认：第一次确认创建 GCP 实例，第二次确认启动集群。首次创建时，CHIA 会在新 VM 上安装 Git、Miniconda、CHIA 和 Docker，通常需要数分钟。

如果明确想跳过交互确认，可以使用 `-y`，但第一次运行不建议这样做：

```bash
chia up -y gcp-cluster.yaml
```

## 6. 检查集群

```bash
chia status --chia-cluster gcp-cluster.yaml
chia list nodes --chia-cluster gcp-cluster.yaml
```

Ray Dashboard 默认可从 WSL/Windows 浏览器打开：

```text
http://127.0.0.1:8265
```

如果 Dashboard 没有显示，先以 `chia status` 和 `chia list nodes` 的结果为准。

## 7. 提交任务

可以先运行仓库自带的 hello-world 示例：

```bash
chia job submit \
  --working-dir examples/hello-world \
  -- python hello-world-s1.py
```

查看正在运行的任务：

```bash
chia job list
```

提交较长任务时建议指定 ID，之后可以停止：

```bash
chia job submit \
  --submission-id my-run-001 \
  --working-dir examples/hello-world \
  -- python hello-world-s1.py

chia job stop my-run-001
```

## 8. 停止并删除云资源

实验结束后必须执行：

```bash
chia down gcp-cluster.yaml
```

按提示确认后，CHIA 会停止 Ray、删除本次集群的 GCP VM，并清理它创建的集群防火墙规则。随后再用 Windows PowerShell 核查没有残留实例：

```powershell
gcloud.cmd compute instances list --project project-842e7b1d-4f04-40b2-9b0
```

如果 `chia up` 在创建 VM 后报错，日志会提示实例可能仍在运行；此时也应立即执行 `chia down gcp-cluster.yaml`，不要只关闭终端。

## 9. 调整规格

编辑 `gcp-cluster.yaml` 中 `gcp_nodes.gcp_worker`：

```yaml
machine_type: e2-small
count: 1
disk_size_gb: 24
spot: false
```

- `count`：云工作节点数量。增加时，还必须在 `compatible_ips` 中加入对应占位符，例如 `@gcp_worker:1`。
- `machine_type`：机器规格。更大规格消耗额度更快。
- `disk_size_gb`：系统盘大小。
- `spot: true`：价格通常更低，但实例可能随时被回收，不适合不能中断的任务。
- `zone`：当前为 `us-central1-a`。换区前先确认该区有相应配额。

如果把 `count` 改为 2，对应配置应为：

```yaml
gcp_worker:
    resources: {"gcp_worker": 1}
    num_workers: 2
    compatible_ips: ["@gcp_worker:0", "@gcp_worker:1"]
```

## 10. 常见问题

### ADC 找不到

确认 WSL 当前终端中已经执行：

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/mnt/c/Users/11345/AppData/Roaming/gcloud/application_default_credentials.json
```

不要把 ADC JSON、SSH 私钥、Tailscale auth key 或其他令牌提交进 Git。

### SSH 登录失败

```bash
sudo systemctl restart ssh
ssh -vv -i ~/.ssh/chia_gcp_ed25519 sakura_02@127.0.0.1 hostname
```

GCP VM 的 SSH 用户是 `chia`，本机 WSL head 用户是 `sakura_02`，两者不同是正常的。

### API 未启用

在 PowerShell 执行：

```powershell
gcloud.cmd services enable compute.googleapis.com --project project-842e7b1d-4f04-40b2-9b0
```

### 默认防火墙警告

新项目的 `default` VPC 可能带有允许公网 SSH 的 `default-allow-ssh` 规则。CHIA 会创建只针对集群实例的 SSH 规则，但不会默认删除这个项目级规则。先检查：

```powershell
gcloud.cmd compute firewall-rules describe default-allow-ssh `
  --project project-842e7b1d-4f04-40b2-9b0
```

只有在确认该规则没有被其他 VM 使用后，再考虑删除或在启动前设置 `CHIA_GCP_LOCKDOWN_DEFAULT_SSH=1`。不要在不清楚影响范围时删除项目级防火墙规则。

### dry-run 中云 worker 的 IP 显示为空

当前 CHIA 1.0.1 的 dry-run 打印路径会读取基础隧道配置，因此脚本预览里可能出现 `RAY_HEAD_IP=` 或 `--node-ip-address=`。同一份输出前面的隧道计划仍会显示实际分配值（本配置为 `127.0.0.2`）。真正的 `chia up` 路径会把已分配的隧道配置传给 worker，不受这个预览问题影响。

### Python 3.10 支持预告

Google Python 客户端会提示 Python 3.10 在 2026-10-04 结束上游支持。这是预告而不是当前错误；现有 CHIA 云节点初始化仍固定使用 Python 3.10.19。届时应在 CHIA 上游确认兼容性后统一迁移到 Python 3.11 或更高版本，不要只升级控制端而让节点版本不一致。

## 11. 查看剩余额度

在 Google Cloud Console 的 Billing 页面查看剩余额度和剩余天数：

- Billing Overview：确认仍显示 **Free trial account**，不要点击 **Activate / Upgrade**。
- Billing Reports：查看 Usage cost、credits 和实际小计。
- Budgets & alerts：可设置较低阈值（例如 25%、50%、80%）接收通知。

官方说明：

- [Google Cloud 免费试用与免费层](https://docs.cloud.google.com/free/docs/free-cloud-features)
- [Google Cloud 免费试用条款](https://cloud.google.com/terms/free-trial)
- [CHIA 集群配置参考](https://docs.chialoops.ai/en/latest/user_guides/cluster_config_reference.html)
