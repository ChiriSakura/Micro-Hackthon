"""End-to-end DynaX smoke test with tiny randomly initialized models."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import torch
from transformers import BloomConfig, LlamaConfig

from models.bloom_modeling import BloomForCausalLM
from models.llama_modeling import LlamaForCausalLM


SEED = 20260903
VOCAB_SIZE = 128
SEQUENCE_LENGTH = 64


def _write_runtime_config(path: Path, *, sparse: bool) -> None:
    config = {
        "is_sparse": sparse,
        "is_quant": False,
        "sparse_methed": "xm",
        "quant_methed": "1_4_6bit",
        "m": 64,
        "n": 16,
        "threshold_0": 1.0,
        "threshold_1": 0.1,
        "threshold_sanger": 1e-4,
        "topk": 8,
    }
    path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")


def _run_forward(model: torch.nn.Module, input_ids: torch.Tensor) -> float:
    model.eval()
    with torch.no_grad():
        output = model(input_ids=input_ids, labels=input_ids, use_cache=False)
    assert output.logits.shape == (1, SEQUENCE_LENGTH, VOCAB_SIZE)
    assert torch.isfinite(output.logits).all()
    assert output.loss is not None and torch.isfinite(output.loss)
    return output.loss.item()


def _run_backward(model: torch.nn.Module, input_ids: torch.Tensor) -> float:
    model.train()
    model.zero_grad(set_to_none=True)
    output = model(input_ids=input_ids, labels=input_ids, use_cache=False)
    assert output.loss is not None and torch.isfinite(output.loss)
    output.loss.backward()
    gradients = [parameter.grad for parameter in model.parameters() if parameter.grad is not None]
    assert gradients
    assert all(torch.isfinite(gradient).all() for gradient in gradients)
    return output.loss.item()


def _run_llama(device: torch.device, input_ids: torch.Tensor, config_path: Path) -> dict[str, object]:
    config = LlamaConfig(
        vocab_size=VOCAB_SIZE,
        hidden_size=64,
        intermediate_size=128,
        num_hidden_layers=2,
        num_attention_heads=4,
        num_key_value_heads=2,
        max_position_embeddings=128,
        attention_dropout=0.0,
        use_cache=False,
    )
    config._attn_implementation = "sdpa"
    model = LlamaForCausalLM(config).to(device)

    _write_runtime_config(config_path, sparse=False)
    dense_loss = _run_forward(model, input_ids)
    _write_runtime_config(config_path, sparse=True)
    sparse_loss = _run_forward(model, input_ids)
    backward_loss = _run_backward(model, input_ids)
    return {
        "parameters": sum(parameter.numel() for parameter in model.parameters()),
        "dense_loss": dense_loss,
        "sparse_loss": sparse_loss,
        "sparse_backward_loss": backward_loss,
    }


def _run_bloom(device: torch.device, input_ids: torch.Tensor, config_path: Path) -> dict[str, object]:
    config = BloomConfig(
        vocab_size=VOCAB_SIZE,
        hidden_size=64,
        n_layer=2,
        n_head=4,
        seq_length=SEQUENCE_LENGTH,
        attention_dropout=0.0,
        hidden_dropout=0.0,
        use_cache=False,
    )
    model = BloomForCausalLM(config).to(device)

    _write_runtime_config(config_path, sparse=False)
    dense_loss = _run_forward(model, input_ids)
    _write_runtime_config(config_path, sparse=True)
    sparse_loss = _run_forward(model, input_ids)
    backward_loss = _run_backward(model, input_ids)
    return {
        "parameters": sum(parameter.numel() for parameter in model.parameters()),
        "dense_loss": dense_loss,
        "sparse_loss": sparse_loss,
        "sparse_backward_loss": backward_loss,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--device", choices=("auto", "cpu", "cuda"), default="auto")
    args = parser.parse_args()

    if args.device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA was requested but is not available")
    device_name = "cuda" if args.device == "auto" and torch.cuda.is_available() else args.device
    if device_name == "auto":
        device_name = "cpu"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    runtime_config = args.output.parent / "dynax_config.json"
    os.environ["DYNAX_CONFIG_PATH"] = str(runtime_config)
    torch.manual_seed(SEED)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(SEED)
    device = torch.device(device_name)
    input_ids = torch.randint(0, VOCAB_SIZE, (1, SEQUENCE_LENGTH), device=device)

    result = {
        "status": "passed",
        "seed": SEED,
        "torch_version": torch.__version__,
        "transformers_version": __import__("transformers").__version__,
        "cuda_version": torch.version.cuda,
        "device": str(device),
        "gpu": torch.cuda.get_device_name(0) if device.type == "cuda" else None,
        "sequence_length": SEQUENCE_LENGTH,
        "llama": _run_llama(device, input_ids, runtime_config),
    }
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    result["bloom"] = _run_bloom(device, input_ids, runtime_config)

    rendered = json.dumps(result, indent=2, sort_keys=True)
    args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
