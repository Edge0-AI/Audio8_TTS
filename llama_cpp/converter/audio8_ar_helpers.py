"""Pure mapping/contract helpers extracted from the accepted Audio8 converters.
No CLI, model loading, experiment path, or legacy float-RoPE export is included.
"""
from __future__ import annotations
import hashlib
from pathlib import Path

LLAMA_CPP_REVISION = "d854d98bae598388ecea1ed84396587e5edc326d"

def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()

def validate_config(config: dict) -> None:
    expected = {
        "model_type": "arktts",
        "n_layer": 24,
        "n_fast_layer": 4,
        "dim": 896,
        "fast_dim": 896,
        "n_head": 14,
        "fast_n_head": 14,
        "n_local_heads": 2,
        "fast_n_local_heads": 2,
        "head_dim": 64,
        "fast_head_dim": 64,
        "intermediate_size": 4864,
        "fast_intermediate_size": 4864,
        "vocab_size": 155776,
        "codebook_size": 4096,
        "num_codebooks": 10,
        "rope_base": 1000000.0,
        "norm_fastlayer_input": True,
        "scale_codebook_embeddings": False,
        "attention_qkv_bias": True,
        "fast_attention_qkv_bias": False,
        "attention_qk_norm": False,
        "fast_attention_qk_norm": False,
        "attention_o_bias": False,
        "fast_attention_o_bias": False,
        "tie_word_embeddings": True,
    }
    differences = {key: (config.get(key), value) for key, value in expected.items() if config.get(key) != value}
    if differences:
        raise ValueError(f"Unsupported architecture values (actual, expected): {differences}")
    if config["semantic_end_id"] - config["semantic_begin_id"] + 1 != config["codebook_size"]:
        raise ValueError("Semantic range must equal one codebook")

def tensor_map(config: dict, branch: str) -> list[tuple[str, str, tuple[int, ...]]]:
    fast = branch == "fast"
    dim = config["fast_dim" if fast else "dim"]
    width = config["fast_intermediate_size" if fast else "intermediate_size"]
    heads = config["fast_n_head" if fast else "n_head"]
    heads_kv = config["fast_n_local_heads" if fast else "n_local_heads"]
    head_dim = config["fast_head_dim" if fast else "head_dim"]
    vocab = config["codebook_size" if fast else "vocab_size"]
    prefix = "fast_" if fast else ""
    result = [
        (f"{prefix}embeddings.weight", "token_embd.weight", (vocab, dim)),
        (f"{prefix}norm.weight", "output_norm.weight", (dim,)),
    ]
    if fast:
        result.append(("fast_output.weight", "output.weight", (vocab, dim)))
    for layer in range(config["n_fast_layer" if fast else "n_layer"]):
        source = f"{prefix}layers.{layer}"
        target = f"blk.{layer}"
        qkv_rows = (heads + 2 * heads_kv) * head_dim
        result.extend([
            (f"{source}.attention.wqkv.weight", f"{target}.attn_qkv.weight", (qkv_rows, dim)),
            (f"{source}.attention.wo.weight", f"{target}.attn_output.weight", (dim, heads * head_dim)),
            (f"{source}.attention_norm.weight", f"{target}.attn_norm.weight", (dim,)),
            (f"{source}.ffn_norm.weight", f"{target}.ffn_norm.weight", (dim,)),
            (f"{source}.feed_forward.w1.weight", f"{target}.ffn_gate.weight", (width, dim)),
            (f"{source}.feed_forward.w2.weight", f"{target}.ffn_down.weight", (dim, width)),
            (f"{source}.feed_forward.w3.weight", f"{target}.ffn_up.weight", (width, dim)),
        ])
        if config["fast_attention_qkv_bias" if fast else "attention_qkv_bias"]:
            result.append((f"{source}.attention.wqkv.bias", f"{target}.attn_qkv.bias", (qkv_rows,)))
    return result
