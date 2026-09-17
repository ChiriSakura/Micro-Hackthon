"""LLM backends for the proposer, with and without Ray.

CHIA wraps its LLM calls in ``@ChiaFunction(resources={"vertex_creds": 0.01})``
so credential quota can be scheduled across a cluster. That is right for cluster
work and wrong for a single text completion on a login node: it needs a Ray
cluster with a matching resource label, and a busy shared node makes Ray miss
its raylet startup deadline.

:class:`VertexDirect` speaks the same ``prompt() -> QueryResult`` contract
straight through google-genai, so the Kernel Agent runs anywhere. Use CHIA's
``VertexGeminiLLM`` instead when the search itself is already a CHIA graph and
credential quota needs scheduling.
"""

from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass
class Reply:
    """Mirrors chia.base.llm_call.QueryResult without importing Ray."""

    result: str
    returncode: int = 0
    stderr: str = ""
    stream_result: str = ""
    success: bool = True



def _finish_reason(response) -> str:
    """模型为什么停下来。取不到就返回空串，不猜一个 "STOP"。

    猜 "STOP" 会把截断说成正常结束——正是这里要防的那件事。
    """
    candidates = getattr(response, "candidates", None) or ()
    for candidate in candidates:
        reason = getattr(candidate, "finish_reason", None)
        if reason is None:
            continue
        return getattr(reason, "name", None) or str(reason)
    return ""


class VertexDirect:
    """Gemini on Vertex AI over Application Default Credentials.

    The same ADC the CHIA cluster uses, so enabling the LLM adds no new secret.
    """

    def __init__(
        self,
        model: str = "gemini-2.5-flash",
        *,
        project: str | None = None,
        location: str | None = None,
        system_message: str = "",
        timeout_seconds: int = 300,
        # 16384 而不是 8192：`gemini-2.5-pro` 是 thinking 模型，推理 token
        # 也算在输出预算里。8192 时 Compiler 的计划回复被**截断在 JSON 中间**,
        # 而截断的表现是「reply was not a JSON array」——那句话会把人送去修
        # 解析器，真正的原因在这个上限上。
        max_output_tokens: int = 16384,
        temperature: float = 0.2,
    ):
        self.model = model
        self.project = project or os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self.location = location or os.environ.get("GCP_LOCATION") or "us-central1"
        if not self.project:
            raise ValueError("Vertex needs a GCP project: pass project= or set GCP_PROJECT")
        self.system_message = system_message
        self.timeout_seconds = timeout_seconds
        self.max_output_tokens = max_output_tokens
        self.temperature = temperature
        self._client = None

    def _ensure_client(self):
        if self._client is None:
            from google import genai  # imported lazily: it is slow off shared storage

            self._client = genai.Client(
                vertexai=True, project=self.project, location=self.location
            )
        return self._client

    def prompt(self, user_message: str, tools=None) -> Reply:
        from google.genai import types

        client = self._ensure_client()
        config = types.GenerateContentConfig(
            temperature=self.temperature,
            max_output_tokens=self.max_output_tokens,
            http_options=types.HttpOptions(timeout=self.timeout_seconds * 1000),
        )
        if self.system_message:
            config.system_instruction = self.system_message
        try:
            response = client.models.generate_content(
                model=self.model, contents=user_message, config=config
            )
        except Exception as exc:
            return Reply(result="", returncode=1, stderr=f"{type(exc).__name__}: {exc}", success=False)

        # **截断必须报出来。** 被 max_output_tokens 砍断的回复 `text` 非空，
        # 于是它一路当成功返回，最后在调用方表现为「解析不出 JSON」。两者的
        # 修法完全不同：一个要调上限，一个要改 prompt 或解析器。
        finish = _finish_reason(response)
        if finish and finish not in ("STOP", "FINISH_REASON_UNSPECIFIED"):
            partial = (response.text or "")[:200]
            return Reply(
                result="", returncode=1, success=False,
                stderr=f"reply did not finish ({finish}); "
                       f"max_output_tokens={self.max_output_tokens}. partial: {partial}",
            )

        text = response.text or ""
        if not text.strip():
            # An empty body is usually a safety block or a truncated response;
            # surface it rather than letting the caller see "no candidates".
            reason = getattr(response, "prompt_feedback", None)
            return Reply(result="", returncode=1, stderr=f"empty response ({reason})", success=False)
        return Reply(result=text, stream_result=text, success=True)
