"""µArch Agent：只组合「已验证」的 Chisel 模板，不生成 RTL。

在流水线里的位置：Kernel → Compiler → **µArch** → Evaluator → Critic。

提案的原话是这个 Agent「通过组合已验证的 Chisel 模块来保证硬件有效性，
而不是无约束地生成 RTL」。所以这里的「生成」是**检索 + 参数化**：
候选只能来自 `fast/agents/templates.py` 的注册表，参数必须落在
`ParameterRange` 允许的取值里。

verified-template 门限是这个 Agent 存在的全部意义：一个没有仿真证据的模板
拿不到 `PASSED`。「能 elaborate、lint 干净」正是绝不能当作通过的那个状态——
DynaX 的 6 个缺陷里有 2 个就是 lint 干净、只有仿真才暴露的。

注意这里的 `TemplateRecord` 是一个最小协议（只有 4 个字段），
完整的注册表记录在 `fast/agents/templates.py`，多带 `provenance`、
`verified_scope` 等证据字段。
"""

from __future__ import annotations

from dataclasses import dataclass

from fast.schemas.models import CompilerSchedule, HardwareCandidate, Status


@dataclass(frozen=True)
class TemplateRecord:
    template_id: str
    digest: str
    manifest_uri: str
    verified: bool


class UArchAgent:
    """Instantiates only allow-listed, independently verified Chisel templates."""

    def __init__(self, templates: tuple[TemplateRecord, ...]):
        self.templates = {item.template_id: item for item in templates}

    def run(
        self,
        schedule: CompilerSchedule,
        *,
        template_id: str,
        queue_depth: int = 8,
        sram_bytes: int = 262_144,
        data_width: int = 16,
    ) -> HardwareCandidate:
        template = self.templates.get(template_id)
        if template is None or not template.verified:
            return HardwareCandidate(
                status=Status.FAILED,
                template_id=template_id,
                template_digest="" if template is None else template.digest,
                verified_template=False,
                pe_rows=0,
                pe_cols=0,
                queue_depth=queue_depth,
                sram_bytes=sram_bytes,
                data_width=data_width,
                manifest_uri="" if template is None else template.manifest_uri,
                error="template is absent or has not passed the verification gate",
            )
        if schedule.status is not Status.PASSED:
            return HardwareCandidate(
                status=Status.SKIPPED,
                template_id=template_id,
                template_digest=template.digest,
                verified_template=True,
                pe_rows=0,
                pe_cols=0,
                queue_depth=queue_depth,
                sram_bytes=sram_bytes,
                data_width=data_width,
                manifest_uri=template.manifest_uri,
                error="compiler schedule gate failed",
            )
        pe_rows = max(1, min(8, schedule.parallelism))
        pe_cols = max(1, (schedule.parallelism + pe_rows - 1) // pe_rows)
        return HardwareCandidate(
            status=Status.PASSED,
            template_id=template_id,
            template_digest=template.digest,
            verified_template=True,
            pe_rows=pe_rows,
            pe_cols=pe_cols,
            queue_depth=queue_depth,
            sram_bytes=sram_bytes,
            data_width=data_width,
            manifest_uri=template.manifest_uri,
        )
