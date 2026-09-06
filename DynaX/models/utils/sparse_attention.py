import torch
import torch.nn.functional as F

from .salo_spattn import matchingStatic_Block
from .sparsity_stats import get_recorder


def _eval_overall_sparsity(sparsity_mask, attn_mask):

    attn_mask = (attn_mask > -1).float()
    attn_mask = attn_mask * (attn_mask.permute(0, 1, 3, 2))

    length = attn_mask.shape[-1]
    causal_mask = torch.tril(torch.ones((length, length), device=attn_mask.device), diagonal=0)
    attn_mask = attn_mask * causal_mask

    scaling_factor = attn_mask.mean(dim=(1, 2, 3))
    sparsity_per_seq = (sparsity_mask.float() * attn_mask).mean(dim=(1, 2, 3))
    overall_sparsity = (sparsity_per_seq / scaling_factor).mean().item()
    return overall_sparsity


def _record(method, sparsity_mask, attn_mask, layer_idx=None):
    """Hand one boolean mask to the explicit per-run recorder."""
    kept = sparsity_mask if sparsity_mask.dtype == torch.bool else sparsity_mask > 0
    get_recorder().record(
        method,
        kept,
        attn_mask,
        causal_kept_ratio=_eval_overall_sparsity(kept, attn_mask),
        layer_idx=layer_idx,
    )


def gen_sparsity_mask_xm(attention_scores, attn_mask, threshold_0, threshold_1, layer_idx=None,
                         n1=16, n2=8, m=64):
    """Dynamic X:M pruning.

    Blocks whose probability mass exceeds ``threshold_0`` keep ``n1`` entries,
    blocks below ``threshold_1`` keep none, and the remainder keep ``n2``.
    """
    if not 0 < n2 <= n1 <= m:
        raise ValueError(f"X:M requires 0 < n2 <= n1 <= m, got n1={n1}, n2={n2}, m={m}")

    attention_scores = F.softmax(attention_scores + attn_mask, dim=-1)

    original_shape = attention_scores.shape
    token_len = original_shape[-1]
    if token_len % m != 0:
        raise ValueError(f"X:M requires sequence length divisible by {m}, got {token_len}")
    s = token_len // m
    reshaped_scores = attention_scores.view(*original_shape[:-1], s, m)
    sum_m = torch.sum(reshaped_scores, dim=-1, keepdim=True).expand_as(reshaped_scores)
    sum_m = sum_m * token_len / m
    _, indices1 = torch.topk(reshaped_scores, n1, dim=-1, largest=True)
    _, indices2 = torch.topk(reshaped_scores, n2, dim=-1, largest=True)
    sparsity_mask_reshaped = torch.zeros_like(reshaped_scores, dtype=torch.bool)
    sparsity_mask_reshaped1 = torch.zeros_like(reshaped_scores, dtype=torch.bool).scatter_(-1, indices1, True)
    sparsity_mask_reshaped2 = torch.zeros_like(reshaped_scores, dtype=torch.bool).scatter_(-1, indices2, True)
    sparsity_mask_reshaped = torch.where(sum_m < threshold_1, sparsity_mask_reshaped, sparsity_mask_reshaped2)
    sparsity_mask_reshaped = torch.where(sum_m > threshold_0, sparsity_mask_reshaped1, sparsity_mask_reshaped)
    sparsity_mask = sparsity_mask_reshaped.view(original_shape)

    _record("xm", sparsity_mask, attn_mask, layer_idx)

    sparsity_mask = sparsity_mask.type_as(attention_scores)
    sparsity_mask = (1.0 - sparsity_mask) * -10000.0

    return sparsity_mask.detach()


def gen_sparsity_mask_nm(attention_scores, attn_mask, m, n, layer_idx=None):
    attention_scores = F.softmax(attention_scores + attn_mask, dim=-1)

    original_shape = attention_scores.shape
    token_len = original_shape[-1]
    if m <= 0 or n <= 0 or n > m:
        raise ValueError(f"N:M requires 0 < n <= m, got n={n}, m={m}")
    if token_len % m != 0:
        raise ValueError(f"N:M requires sequence length divisible by m={m}, got {token_len}")
    s = token_len // m
    reshaped_scores = attention_scores.view(*original_shape[:-1], s, m)
    _, indices = torch.topk(reshaped_scores, n, dim=-1, largest=True)
    sparsity_mask_reshaped = torch.zeros_like(reshaped_scores, dtype=torch.bool)
    sparsity_mask_reshaped.scatter_(-1, indices, True)
    sparsity_mask = sparsity_mask_reshaped.view(original_shape)

    _record("nm", sparsity_mask, attn_mask, layer_idx)

    sparsity_mask = sparsity_mask.type_as(attention_scores)
    sparsity_mask = (1.0 - sparsity_mask) * -10000.0
    
    return sparsity_mask.detach()


def gen_sparsity_mask_sanger(attention_scores, attn_mask, threshold, layer_idx=None):
    attention_scores = F.softmax(attention_scores + attn_mask, dim=-1)
    sparsity_mask = attention_scores > threshold

    _record("sanger", sparsity_mask, attn_mask, layer_idx)

    sparsity_mask = sparsity_mask.type_as(attention_scores)
    sparsity_mask = (1.0 - sparsity_mask) * -10000.0
    
    return sparsity_mask.detach()


def gen_sparsity_mask_topk(attention_scores, attn_mask, topk, layer_idx=None):
    if topk <= 0 or topk > attention_scores.shape[-1]:
        raise ValueError(
            f"topk must be in [1, {attention_scores.shape[-1]}], got {topk}"
        )
    attention_scores = F.softmax(attention_scores + attn_mask, dim=-1)
    sparsity_mask = torch.full_like(attention_scores, False, dtype=torch.bool)
    index = torch.topk(attention_scores, topk, dim=-1, largest=True)[1]
    sparsity_mask.scatter_(-1, index, True)

    _record("topk", sparsity_mask, attn_mask, layer_idx)

    sparsity_mask = sparsity_mask.type_as(attention_scores)
    sparsity_mask = (1.0 - sparsity_mask) * -10000.0

    return sparsity_mask.detach()


def gen_sparsity_mask_salo(attention_scores, attn_mask, layer_idx=None):
    match_size = 64
    pe_size = 8 
    global_nums = 1 
    random_nums = 3
    dilation = 1

    attention_scores_salo = attention_scores
    attn_mask_salo = attn_mask
    
    sparsity_mask = matchingStatic_Block(attention_scores_salo, attn_mask_salo, match_size, pe_size, global_nums, random_nums, dilation)

    _record("salo", sparsity_mask, attn_mask, layer_idx)

    sparsity_mask = sparsity_mask.type_as(attention_scores)
    sparsity_mask = (1.0 - sparsity_mask) * -10000.0
    
    return sparsity_mask.detach()


def prune_attn_scores(attn_scores, attn_mask, threshold_0 = 1.0, threshold_1 = 0.1, m=64, n=16, topk=100, threshold=1e-4, sparse_method="xm", layer_idx=None,
                      xm_n1=16, xm_n2=8, xm_m=64):
    match sparse_method:
        case "xm":
            return gen_sparsity_mask_xm(attn_scores, attn_mask, threshold_0, threshold_1, layer_idx, xm_n1, xm_n2, xm_m)
        case "nm":
            return gen_sparsity_mask_nm(attn_scores, attn_mask, m, n, layer_idx)
        case "sanger":
            return gen_sparsity_mask_sanger(attn_scores, attn_mask, threshold, layer_idx)
        case "topk":
            return gen_sparsity_mask_topk(attn_scores, attn_mask, topk, layer_idx)
        case "salo":
            return gen_sparsity_mask_salo(attn_scores, attn_mask, layer_idx)
        case _:
            raise ValueError(
                f"Unsupported sparse_method={sparse_method!r}; expected xm, nm, sanger, salo, or topk"
            )


def quant_qk_matmul(quant_methed, query_layer, key_layer, quant_matmul=None):

    if(quant_methed == "1_2_4bit"):
        last_dim = query_layer.shape[-1]
        assert last_dim % 2 == 0, "last_dim must even"
        sparse_query_layer = torch.zeros_like(query_layer)
        for i in range(0, last_dim, 2):
            part = query_layer[..., i:i+2]
            abs_part = torch.abs(part)
            max_index = torch.argmax(abs_part, dim=-1, keepdim=True)
            sparse_part = torch.zeros_like(part).scatter_(-1, max_index, part.gather(-1, max_index))
            sparse_query_layer[..., i:i+2] = sparse_part
        query_layer = sparse_query_layer

    elif(quant_methed == "1_4_6bit"):
        last_dim = query_layer.shape[-1]
        assert last_dim % 4 == 0, "last_dim must be divisible by 4"
        sparse_query_layer = torch.zeros_like(query_layer)
        for i in range(0, last_dim, 4):
            part = query_layer[..., i:i+4]
            abs_part = torch.abs(part)
            max_index = torch.argmax(abs_part, dim=-1, keepdim=True)
            sparse_part = torch.zeros_like(part).scatter_(-1, max_index, part.gather(-1, max_index))
            sparse_query_layer[..., i:i+4] = sparse_part
        query_layer = sparse_query_layer

    quant_attention_scores = quant_matmul(query_layer, key_layer)

    return quant_attention_scores
