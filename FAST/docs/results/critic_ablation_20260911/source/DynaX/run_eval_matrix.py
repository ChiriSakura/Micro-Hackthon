"""Evaluate one real model under dense and sparse attention on a real dataset.

The driver loads the model and tokenised dataset once, then sweeps attention
configurations in-process so that every method sees exactly the same weights,
the same token windows and the same seed. Each method produces perplexity,
sparse-mask statistics, wall-clock time and peak memory, and the whole run is
written to a candidate-specific directory together with a manifest.

Example:
    python run_eval_matrix.py \
        --model TinyLlama/TinyLlama_v1.1 \
        --dataset wiki --seq-len 1024 --max-samples 16 \
        --methods dense,xm,nm,topk \
        --run-dir /scratch/.../runs/eval_matrix

★ FAST 新增，非 DynaX 上游文件。
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any

import torch
from transformers import AutoConfig, AutoTokenizer

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dataUtil import get_dataset  # noqa: E402
from models.utils.runtime_config import set_dynax_config  # noqa: E402
from models.utils.sparsity_stats import get_recorder  # noqa: E402


BASE_CONFIG: dict[str, Any] = {
    "is_sparse": True,
    "is_quant": False,
    "sparse_methed": "xm",
    "quant_methed": "1_4_6bit",
    "m": 64,
    "n": 16,
    "threshold_0": 1.0,
    "threshold_1": 0.1,
    "threshold_sanger": 1e-4,
    "topk": 400,
    "xm_n1": 16,
    "xm_n2": 8,
    "xm_m": 64,
}

DTYPES = {
    "float32": torch.float32,
    "float16": torch.float16,
    "bfloat16": torch.bfloat16,
}


def method_config(method: str, overrides: dict[str, Any]) -> dict[str, Any]:
    """Build the DynaX runtime config for one attention method."""
    config = dict(BASE_CONFIG)
    config.update(overrides)
    if method == "dense":
        config["is_sparse"] = False
        config["is_quant"] = False
        return config
    if method == "quant_xm":
        config["is_sparse"] = True
        config["is_quant"] = True
        config["sparse_methed"] = "xm"
        return config
    if method.startswith("xm:"):
        # Six-field labels make BOTH thresholds candidate-specific, including
        # in batched runs. Four-field labels retain the legacy baseline only.
        parts = method.split(":")
        if len(parts) not in (4, 6):
            raise ValueError("expected xm:N1:N2:M[:T0:T1]")
        n1, n2, m = map(int, parts[1:4])
        if not 0 < n2 <= n1 <= m:
            raise ValueError("X:M requires 0 < N2 <= N1 <= M")
        if len(parts) == 6:
            t0, t1 = map(float, parts[4:])
            if not all(math.isfinite(t) for t in (t0, t1)) or not 0 <= t1 <= t0:
                raise ValueError("X:M requires finite 0 <= T1 <= T0")
            config["threshold_0"], config["threshold_1"] = t0, t1
        config["is_sparse"] = True
        config["sparse_methed"] = "xm"
        config["xm_n1"], config["xm_n2"], config["xm_m"] = n1, n2, m
        return config
    if method.startswith("nm:"):
        _, n, m = method.split(":")
        config["is_sparse"] = True
        config["sparse_methed"] = "nm"
        config["n"], config["m"] = int(n), int(m)
        return config
    if method.startswith("topk:"):
        config["is_sparse"] = True
        config["sparse_methed"] = "topk"
        config["topk"] = int(method.split(":")[1])
        return config
    if method not in {"xm", "nm", "topk", "sanger", "salo"}:
        raise ValueError(f"unsupported method {method!r}")
    config["is_sparse"] = True
    config["sparse_methed"] = method
    return config


def config_digest(config: dict[str, Any]) -> str:
    payload = json.dumps(config, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def git_commit(path: Path) -> str | None:
    try:
        return subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def load_model(model_name_or_path: str, dtype: torch.dtype, tokenizer):
    """Instantiate the DynaX re-implementation matching the checkpoint family."""
    hf_config = AutoConfig.from_pretrained(model_name_or_path)
    model_type = getattr(hf_config, "model_type", "")
    if model_type == "llama":
        from models.llama_modeling import LlamaForCausalLM as Model
    elif model_type == "bloom":
        from models.bloom_modeling import BloomForCausalLM as Model
    else:
        raise ValueError(
            f"model_type={model_type!r} has no DynaX implementation; expected llama or bloom"
        )
    model = Model.from_pretrained(
        model_name_or_path,
        torch_dtype=dtype,
        pad_token_id=tokenizer.pad_token_id,
    )
    model.config.pad_token_id = tokenizer.pad_token_id
    model.generation_config.pad_token_id = tokenizer.pad_token_id
    return model, hf_config


@torch.no_grad()
def evaluate(model, tokens: torch.Tensor, seq_len: int, nsamples: int, device) -> dict[str, Any]:
    """Sliding-window perplexity over non-overlapping windows of ``seq_len``."""
    loss_fct = torch.nn.CrossEntropyLoss()
    nll_sum = 0.0
    token_count = 0
    per_sample = []
    for index in range(nsamples):
        window = tokens[:, index * seq_len : (index + 1) * seq_len]
        if window.size(1) < seq_len:
            break
        batch = window.to(device)
        outputs = model(batch, use_cache=False)
        logits = outputs.logits[0].float()
        shift_logits = logits[:-1, :]
        shift_labels = batch[:, 1:]
        loss = loss_fct(
            shift_logits.reshape(-1, shift_logits.size(-1)),
            shift_labels.reshape(-1),
        )
        sample_tokens = shift_labels.numel()
        nll_sum += loss.item() * sample_tokens
        token_count += sample_tokens
        per_sample.append(round(loss.item(), 6))
    if token_count == 0:
        raise ValueError(f"no complete window of length {seq_len} in the tokenised dataset")
    mean_nll = nll_sum / token_count
    return {
        "perplexity": float(torch.exp(torch.tensor(mean_nll)).item()),
        "mean_nll": mean_nll,
        "tokens": token_count,
        "windows": len(per_sample),
        "per_window_loss": per_sample,
    }


def _with_deltas(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Attach dense-relative fields; a sweep without a dense run simply has none."""
    dense = next((item for item in records if item["method"] == "dense" and item["status"] == "passed"), None)
    if dense is None:
        return records
    for record in records:
        if record["status"] != "passed":
            continue
        record["perplexity_delta"] = record["perplexity"] - dense["perplexity"]
        record["perplexity_ratio"] = record["perplexity"] / dense["perplexity"]
        record["relative_quality_loss"] = (record["perplexity"] - dense["perplexity"]) / dense["perplexity"]
        record["speed_ratio_vs_dense"] = (
            dense["wall_seconds"] / record["wall_seconds"] if record["wall_seconds"] else None
        )
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--model", required=True, help="Hugging Face id or local checkpoint path")
    parser.add_argument("--dataset", default="wiki", choices=["wiki", "ptb", "c4"])
    parser.add_argument("--seq-len", type=int, default=1024, help="must be a multiple of 64 for X:M and N:M")
    parser.add_argument("--max-samples", type=int, default=16)
    parser.add_argument("--methods", default="dense,xm,nm,topk", help="comma-separated methods: dense,xm,nm,topk,sanger,salo,quant_xm plus parametric xm:N1:N2:M, nm:N:M, topk:K")
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--dtype", default="auto", choices=["auto", *DTYPES])
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=20260903)
    parser.add_argument("--nm-n", type=int, default=16)
    parser.add_argument("--nm-m", type=int, default=64)
    parser.add_argument("--topk", type=int, default=None, help="defaults to seq_len // 8")
    parser.add_argument("--threshold-sanger", type=float, default=1e-4)
    args = parser.parse_args()

    methods = [item.strip() for item in args.methods.split(",") if item.strip()]
    run_dir: Path = args.run_dir.expanduser()
    run_dir.mkdir(parents=True, exist_ok=True)

    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)
    if args.dtype == "auto":
        dtype = torch.bfloat16 if device.type == "cuda" else torch.float32
    else:
        dtype = DTYPES[args.dtype]

    torch.manual_seed(args.seed)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(args.seed)

    started = time.time()
    tokenizer = AutoTokenizer.from_pretrained(args.model, legacy=False)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"[fast] loading model {args.model} as {dtype} on {device}", flush=True)
    model, hf_config = load_model(args.model, dtype, tokenizer)
    model.to(device)
    model.eval()
    parameters = sum(p.numel() for p in model.parameters())

    print(f"[fast] tokenising dataset {args.dataset}", flush=True)
    tokens = get_dataset(tokenizer, seqlen=args.seq_len, dataset=args.dataset).input_ids
    available = tokens.numel() // args.seq_len
    nsamples = min(available, args.max_samples)
    print(f"[fast] {parameters:,} parameters, {available} windows available, evaluating {nsamples}", flush=True)

    overrides = {
        "n": args.nm_n,
        "m": args.nm_m,
        "topk": args.topk if args.topk is not None else max(1, args.seq_len // 8),
        "threshold_sanger": args.threshold_sanger,
    }

    manifest = {
        "schema_version": "0.2",
        "command": " ".join(sys.argv),
        "model": args.model,
        "model_type": getattr(hf_config, "model_type", None),
        "parameters": parameters,
        "hidden_layers": getattr(hf_config, "num_hidden_layers", None),
        "attention_heads": getattr(hf_config, "num_attention_heads", None),
        "attn_implementation": getattr(model.config, "_attn_implementation", None),
        "dataset": args.dataset,
        "sequence_length": args.seq_len,
        "windows_requested": args.max_samples,
        "windows_available": available,
        "windows_evaluated": nsamples,
        "seed": args.seed,
        "dtype": str(dtype),
        "device": str(device),
        "gpu": torch.cuda.get_device_name(0) if device.type == "cuda" else None,
        "python": platform.python_version(),
        "torch": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "host": platform.node(),
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "dynax_commit": git_commit(REPO_ROOT),
        "methods_requested": methods,
    }
    output = run_dir / "results.json"

    records: list[dict[str, Any]] = []
    recorder = get_recorder()

    def checkpoint() -> None:
        """Write what has been measured so far, so a timeout still leaves data."""
        manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
        manifest["wall_seconds_total"] = round(time.time() - started, 3)
        manifest["complete"] = len(records) == len(methods)
        manifest["overrides"] = overrides
        output.write_text(
            json.dumps({"manifest": manifest, "results": _with_deltas(records)}, indent=2) + "\n",
            encoding="utf-8",
        )
    for method in methods:
        config = method_config(method, overrides)
        recorder.reset()
        set_dynax_config(config)
        if device.type == "cuda":
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()
        print(f"[fast] evaluating method={method} config={config_digest(config)[:12]}", flush=True)
        method_started = time.time()
        try:
            measurement = evaluate(model, tokens, args.seq_len, nsamples, device)
            error = None
        except Exception as exc:  # surface the failure per method, keep the sweep going
            measurement = {}
            error = f"{type(exc).__name__}: {exc}"
            print(f"[fast] method={method} FAILED: {error}", flush=True)
        wall = time.time() - method_started
        stats = recorder.summary()
        if stats:
            (run_dir / f"sparsity_{method.replace(chr(58), chr(45))}.json").write_text(
                json.dumps(stats, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        record = {
            "method": method,
            "status": "failed" if error else "passed",
            "error": error,
            "config": config,
            "config_digest": config_digest(config),
            "wall_seconds": round(wall, 3),
            "seconds_per_window": round(wall / max(1, measurement.get("windows", 1)), 3),
            "peak_memory_bytes": (
                torch.cuda.max_memory_allocated() if device.type == "cuda" else None
            ),
            "sparsity_stats": stats,
            **measurement,
        }
        records.append(record)
        checkpoint()
        if error is None:
            print(
                f"[fast] method={method} ppl={record['perplexity']:.4f} "
                f"wall={wall:.1f}s",
                flush=True,
            )
    set_dynax_config(None)
    checkpoint()
    print(f"[fast] wrote {output}", flush=True)
    return 0 if all(item["status"] == "passed" for item in records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
