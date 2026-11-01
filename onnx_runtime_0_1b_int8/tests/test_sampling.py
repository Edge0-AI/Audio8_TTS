from __future__ import annotations

import numpy as np
import pytest

from arktts_runtime import runtime
from arktts_runtime.runtime import ArkTtsRuntime, _execution_providers, _sample


def test_execution_providers_defaults_to_cpu(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ARKTTS_EXECUTION_PROVIDER", raising=False)
    assert _execution_providers() == ["CPUExecutionProvider"]


def test_execution_providers_selects_cuda(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ARKTTS_EXECUTION_PROVIDER", "cuda")
    monkeypatch.setenv("ARKTTS_CUDA_DEVICE_ID", "1")
    monkeypatch.setattr(
        runtime.ort,
        "get_available_providers",
        lambda: ["CUDAExecutionProvider", "CPUExecutionProvider"],
    )
    assert _execution_providers() == [
        ("CUDAExecutionProvider", {"device_id": 1}),
        "CPUExecutionProvider",
    ]


def test_execution_providers_rejects_missing_cuda(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ARKTTS_EXECUTION_PROVIDER", "cuda")
    monkeypatch.setattr(
        runtime.ort, "get_available_providers", lambda: ["CPUExecutionProvider"]
    )
    with pytest.raises(RuntimeError, match="CUDAExecutionProvider"):
        _execution_providers()


def test_sample_uses_gumbel_max_noise() -> None:
    # This seed distinguishes Gumbel-max from the tempting but incorrect -log(U)
    # shortcut, which can bias sampling toward EOS and truncate speech.
    result = _sample(
        np.asarray([0.0, 1.0], dtype=np.float32),
        temperature=1.0,
        top_p=1.0,
        top_k=2,
        rng=np.random.default_rng(0),
    )
    assert result == 0


def test_first_semantic_step_cannot_return_eos() -> None:
    runtime = object.__new__(ArkTtsRuntime)
    runtime.manifest = {
        "codebook_size": 2,
        "semantic_begin_id": 100,
        "semantic_end_id": 101,
        "im_end_id": 4096,
        "slow_logits_layout": "relative_semantic_then_eos",
    }
    logits = np.asarray([0.0, 1.0, 100.0], dtype=np.float32)

    first = runtime._sample_semantic(
        logits,
        previous=[],
        temperature=1.0,
        top_p=1.0,
        top_k=1,
        rng=np.random.default_rng(0),
    )
    assert first == 101

    later = runtime._sample_semantic(
        logits,
        previous=[first],
        temperature=1.0,
        top_p=1.0,
        top_k=1,
        rng=np.random.default_rng(0),
    )
    assert later == 4096
