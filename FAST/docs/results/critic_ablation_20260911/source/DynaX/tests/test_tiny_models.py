from __future__ import annotations

import json

import pytest
import torch
from transformers import BloomConfig, LlamaConfig

from models.bloom_modeling import BloomForCausalLM
from models.llama_modeling import LlamaForCausalLM


SEED = 20260903
VOCAB_SIZE = 128
SEQUENCE_LENGTH = 64


def _write_config(path, sparse):
    path.write_text(
        json.dumps(
            {
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
        ),
        encoding="utf-8",
    )


def _assert_model_golden(model, input_ids, config_path):
    model.eval()
    _write_config(config_path, sparse=False)
    with torch.no_grad():
        dense = model(input_ids=input_ids, labels=input_ids, use_cache=False)

    _write_config(config_path, sparse=True)
    with torch.no_grad():
        sparse = model(input_ids=input_ids, labels=input_ids, use_cache=False)

    assert dense.logits.shape == sparse.logits.shape == (1, SEQUENCE_LENGTH, VOCAB_SIZE)
    assert torch.isfinite(dense.logits).all()
    assert torch.isfinite(sparse.logits).all()
    assert dense.loss is not None and torch.isfinite(dense.loss)
    assert sparse.loss is not None and torch.isfinite(sparse.loss)
    assert not torch.equal(dense.logits, sparse.logits)

    model.train()
    model.zero_grad(set_to_none=True)
    backward = model(input_ids=input_ids, labels=input_ids, use_cache=False)
    backward.loss.backward()
    gradients = [parameter.grad for parameter in model.parameters() if parameter.grad is not None]
    assert gradients
    assert all(torch.isfinite(gradient).all() for gradient in gradients)


def _run_tiny_models(device, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "candidate.json"
    monkeypatch.setenv("DYNAX_CONFIG_PATH", str(config_path))
    torch.manual_seed(SEED)
    if device.type == "cuda":
        torch.cuda.manual_seed_all(SEED)
    input_ids = torch.randint(0, VOCAB_SIZE, (1, SEQUENCE_LENGTH), device=device)

    llama_config = LlamaConfig(
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
    llama_config._attn_implementation = "sdpa"
    _assert_model_golden(LlamaForCausalLM(llama_config).to(device), input_ids, config_path)

    bloom_config = BloomConfig(
        vocab_size=VOCAB_SIZE,
        hidden_size=64,
        n_layer=2,
        n_head=4,
        seq_length=SEQUENCE_LENGTH,
        attention_dropout=0.0,
        hidden_dropout=0.0,
        use_cache=False,
    )
    _assert_model_golden(BloomForCausalLM(bloom_config).to(device), input_ids, config_path)


@pytest.mark.integration
def test_tiny_models_cpu_end_to_end(tmp_path, monkeypatch):
    _run_tiny_models(torch.device("cpu"), tmp_path, monkeypatch)


@pytest.mark.integration
@pytest.mark.gpu
@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA is unavailable")
def test_tiny_models_cuda_end_to_end(tmp_path, monkeypatch):
    _run_tiny_models(torch.device("cuda"), tmp_path, monkeypatch)
