"""Pinned official CPU codec construction and weight-normalization folding.
Extracted without the old experiment CLI; Torch is imported only inside the helper.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

CODEC_SHA = "c310505aa11fe2f6cc63b8d3130dc7e77e73227774f5c62575769b1f47a8d048"
SOURCE_SHA = "e1d6b0e1ef1e9ad303dc01d45d86229cf7f2e98d06a7b426234a7e4d7e3ede68"

def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(b)
    return h.hexdigest()

def load_official(model_dir, *, fold_weight_norm=False):
    import torch
    path = Path(model_dir) / "modeling_arktts_codec.py"
    if file_sha(path) != SOURCE_SHA:
        raise ValueError("Official codec source SHA mismatch")
    spec = importlib.util.spec_from_file_location("audio8_locked_official_codec", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    config = json.loads((Path(model_dir) / "config.json").read_text())
    codec = module.ArkttsCodec(SimpleNamespace(**config)).float().eval()
    state = torch.load(Path(model_dir) / "codec.pth", map_location="cpu", weights_only=True)
    state = state.get("state_dict", state)
    if any("generator." in key for key in state):
        state = {key.replace("generator.", ""): value for key, value in state.items() if "generator." in key}
    state = {key: value for key, value in state.items() if not key.endswith(("freqs_cis", "causal_mask"))}
    codec.load_state_dict(state, strict=True)
    del state
    folded = []
    if fold_weight_norm:
        for name, child in list(codec.named_modules()):
            if hasattr(child, "parametrizations") and "weight" in child.parametrizations:
                torch.nn.utils.parametrize.remove_parametrizations(child, "weight", leave_parametrized=True)
                folded.append(name)
            elif hasattr(child, "weight_g") and hasattr(child, "weight_v"):
                torch.nn.utils.remove_weight_norm(child)
                folded.append(name)
    return module, codec, folded
