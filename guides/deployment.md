# Deployment guide

[All releases](../README.md) · [中文](deployment_zh.md) · [Installation and inference](inference.md)

| Release | Transformers / CLI | SGLang Omni | ONNX |
|---|---|---|---|
| Realistic Air | Supported | 0.6B configuration | No export available |
| Preview 0.6B | Supported | 0.6B configuration | INT4, onnx_runtime/ |
| Preview 0.1B | Supported | 0.1B hybrid configuration | INT8, onnx_runtime_0_1b_int8/ |

Realistic Air uses the 0.6B configuration with its own explicit model ID or snapshot path. ONNX exports belong to the listed release; the Preview ONNX files are not Realistic Air weights.

## SGLang Omni Serving

The adapter in [`sglang_omni/`](../sglang_omni/) provides an OpenAI-compatible
service with SGLang paged attention, dynamic batching, a fixed KV cache for the
fast codebook decoder, reference-audio encoding, and waveform decoding. It is
installed as an independent `audio8_tts` model plugin and does not overwrite
SGLang Omni core files.

### Compatibility

The adapter uses internal SGLang Omni interfaces, so deploy it with the tested
revision instead of the latest `main` branch.

| Dependency | Tested version |
|---|---|
| SGLang Omni | `68a572348837f7b004857b4b07993c20ade4c017` (`0.1.0`) |
| SGLang | `0.5.8` |
| PyTorch | `2.9.1+cu128` |
| Transformers | `4.57.1` |
| Precision | BF16 |

### Performance

The existing SGLang benchmark and its original test conditions are retained below. Realistic Air and Preview 0.6B share the same architecture and serving path. These are existing measurements, not a new Realistic Air benchmark. The separate 0.1B eager hybrid path is described below.

Warm single-stream latency was measured on one NVIDIA H20 with BF16 weights,
CUDA Graph, greedy decoding, and 128 generated frames. The output WAV was
5.85-5.94 seconds long; cold start and compilation time were excluded. Lower
RTF is better.

| SGLang Omni adapter | Warm p50 latency | RTF |
|---|---:|---:|
| Current implementation | **0.691 s** | **0.116** |

See the [SGLang Omni implementation and evaluation report](../sglang_omni/OPTIMIZATION_REPORT.md)
for the configuration, implementation details, and validation results.

### Install

Run these commands from the Audio8 TTS repository root. The example uses
Python 3.12 and [`uv`](https://docs.astral.sh/uv/).

```bash
export SGLANG_OMNI_ROOT=/opt/sglang-omni
export MODEL_ID=Edge0/Audio8-TTS-Realistic-Air
# Preview 0.6B: export MODEL_ID=Edge0/Audio8-TTS-Preview-0.6b
export MODEL="./model/${MODEL_ID##*/}"

git clone https://github.com/sgl-project/sglang-omni.git "${SGLANG_OMNI_ROOT}"
git -C "${SGLANG_OMNI_ROOT}" checkout 68a572348837f7b004857b4b07993c20ade4c017

uv venv .venv-sglang --python 3.12
source .venv-sglang/bin/activate
uv pip install -v -e "${SGLANG_OMNI_ROOT}"

hf download "${MODEL_ID}" --local-dir "${MODEL}"
./sglang_omni/scripts/install_adapter.sh "${SGLANG_OMNI_ROOT}"
python3 ./sglang_omni/scripts/verify_install.py --model-path "${MODEL}"
```

For an existing wheel or site-packages installation, resolve the package
directory and install the adapter there:

```bash
SGLANG_OMNI_PACKAGE="$(python3 -c 'import importlib.util, pathlib; s=importlib.util.find_spec("sglang_omni"); assert s and s.origin; print(pathlib.Path(s.origin).parent)')"
./sglang_omni/scripts/install_adapter.sh "${SGLANG_OMNI_PACKAGE}"
```

### Start the service

```bash
CUDA_VISIBLE_DEVICES=0 \
SGLANG_OMNI_ROOT="${SGLANG_OMNI_ROOT}" \
MODEL="${MODEL}" \
AUDIO8_TTS_ENABLE_TORCH_COMPILE=1 \
HOST=0.0.0.0 \
PORT=8010 \
./sglang_omni/scripts/run_server.sh
```

The default `fa3` attention backend is intended for Hopper GPUs such as H20
and H100. Consumer Blackwell GPUs such as RTX 5090 report compute capability
`(12, 0)` and have no FA3 kernel image, so the adapter detects them and selects
FlashInfer for the SGLang slow-AR path automatically; the short fixed-cache
fast head then uses PyTorch SDPA. No configuration is required.

Setting the variable explicitly still overrides the detection on any GPU:

```bash
AUDIO8_TTS_ATTENTION_BACKEND=flashinfer \
CUDA_VISIBLE_DEVICES=0 \
SGLANG_OMNI_ROOT="${SGLANG_OMNI_ROOT}" \
MODEL="${MODEL}" \
./sglang_omni/scripts/run_server.sh
```

The defaults use model name `audio8/tts-0.6b`, BF16, one GPU, a `0.2` static
memory fraction, and up to 32 running requests. The main runtime controls are
`MODEL_NAME`, `AUDIO8_TTS_MEM_FRACTION_STATIC`,
`AUDIO8_TTS_MAX_RUNNING_REQUESTS`, `AUDIO8_TTS_CHUNKED_PREFILL_SIZE`, and
`AUDIO8_TTS_DISABLE_CUDA_GRAPH`. When Torch compilation is enabled, the adapter
uses SGLang's native batch-size policy. Set `AUDIO8_TTS_TORCH_COMPILE_MAX_BS`
only when an explicit compile limit is needed. `AUDIO8_TTS_ATTENTION_BACKEND`
defaults to `fa3`, except on GPUs with no FA3 kernel image such as consumer
Blackwell, where it defaults to `flashinfer`; set it explicitly to override. Set
`SGLANG_OMNI_SITE_PACKAGES` when the runtime dependencies are installed in a
separate site-packages directory.

### Troubleshooting

- Install the distribution package that provides `libnuma` if `sgl_kernel`
  fails to import (for example, `numactl` or `libnuma1`).
- Put the CUDA toolkit `bin` directory on `PATH`. If `deep_gemm` cannot find
  `nvcc` during JIT compilation, also set `CUDA_PATH` to the toolkit root.
- Keep Transformers on the supported 4.x range (`>=4.57.0,<5`). Transformers
  5.x can produce invalid all-zero codes for this custom-code model.

### Call the API

Generate speech without a reference:

```bash
curl -sS --fail-with-body \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "audio8/tts-0.6b",
    "input": "Hello from Audio8 TTS.",
    "response_format": "wav",
    "max_new_tokens": 256,
    "temperature": 0.8,
    "top_p": 0.95,
    "top_k": 50
  }' \
  http://127.0.0.1:8010/v1/audio/speech \
  -o audio8.wav
```

Generate speech with one reference voice:

```bash
curl -sS --fail-with-body \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "audio8/tts-0.6b",
    "input": "This sentence uses the reference voice.",
    "response_format": "wav",
    "temperature": 0.8,
    "top_p": 0.95,
    "top_k": 50,
    "references": [{
      "audio_path": "/data/reference.wav",
      "text": "The exact transcript of the reference recording."
    }]
  }' \
  http://127.0.0.1:8010/v1/audio/speech \
  -o audio8_clone.wav
```

The reference path must be visible inside the service environment. The current
adapter supports TP=1 and one reference per request. Set `"stream": true` to
receive SSE audio chunks as they are generated. For the lowest overhead, use
`"response_format": "pcm"`; each event contains Base64-encoded audio in
`audio.data`. Streaming defaults to 12 codec frames per chunk, with 128 frames
of decoder context and a one-frame boundary guard. Override these values with
`AUDIO8_TTS_STREAM_CHUNK_FRAMES`, `AUDIO8_TTS_STREAM_CONTEXT_FRAMES`, and
`AUDIO8_TTS_STREAM_GUARD_FRAMES`.

Streaming is a server-side opt-in. Start the service with
`AUDIO8_TTS_STREAM_ENABLED=1` to enable SSE streaming; the default is off, and
requests are answered with the complete audio after generation finishes
(a request-level `"stream": true` is then ignored). Non-streaming remains the
default for maximum throughput and stable memory usage. `response_format` of
`codes`/`codec`/`npy` always returns codec codes without streaming.

Run the smoke test to verify a deployment:

```bash
BASE_URL=http://127.0.0.1:8010 ./sglang_omni/scripts/smoke_test.sh
python3 ./sglang_omni/scripts/stream_smoke_test.py \
  --base-url http://127.0.0.1:8010 \
  --output /tmp/audio8_stream.wav
```

To build the adapter into an existing image, append
[`sglang_omni/Dockerfile.snippet`](../sglang_omni/Dockerfile.snippet) after the
SGLang Omni package and its Python dependencies are installed.

### Audio8-TTS-0.1B (Falcon-H1 hybrid slow backbone)

Install the adapter as above, then select this model, configuration, and API name. Use audio8/tts-0.1b in the request's model field.

`Audio8-TTS-Preview-0.1b` replaces the pure-attention slow AR backbone with a
Falcon-H1 hybrid (Mamba 2 SSM + attention). The adapter detects this
automatically from `config.json` (`slow_backbone: falcon_h1` or a `mamba_d_ssm`
field) and switches to the eager hybrid path: the slow backbone runs with one
`FalconHybridMambaAttentionDynamicCache` per request, while the fast codebook
AR, semantic sampling and vocoder are shared with the 0.6B path. The 0.6B
path is unchanged.

```bash
export MODEL=./model/Audio8-TTS-Preview-0.1b
hf download Edge0/Audio8-TTS-Preview-0.1b --local-dir "${MODEL}"
export CONFIG=./sglang_omni/configs/audio8_tts_0_1b.yaml
export MODEL_NAME=audio8/tts-0.1b

CUDA_VISIBLE_DEVICES=0 \
SGLANG_OMNI_ROOT="${SGLANG_OMNI_ROOT}" \
MODEL="${MODEL}" \
CONFIG="${CONFIG}" \
MODEL_NAME="${MODEL_NAME}" \
./sglang_omni/scripts/run_server.sh
```

Because the Mamba backbone keeps its own hybrid caches and does not consume
SGLang KV pages, the adapter disables CUDA graphs and caps the static memory
fraction for this model. The slow backbone is bit-exact with the Transformers
Falcon-H1 implementation for both prefill and cached decode.

## Preview 0.6B: CPU ONNX INT4

[`onnx_runtime/`](../onnx_runtime/) provides a standalone CPU deployment using
weight-only INT4 Slow/Fast AR models, FP16 activations and KV caches, and an
FP16 codec. It includes CLI inference, a local web and HTTP service, streaming
PCM output, and reference-voice registration without PyTorch or Transformers.

The online sessions use about 1 GiB of memory in the tested Apple M2 setup.
During voice registration, the online sessions are released before the codec
encoder is loaded to keep peak memory low.

Download the ONNX model from
[Audio8-TTS-Preview-0.6B-ONNX-INT4](https://huggingface.co/Edge0/Audio8-TTS-Preview-0.6B-ONNX-INT4)
and follow the [ONNX Runtime guide](../onnx_runtime/README.md).

## Preview 0.1B: CPU ONNX INT8

0.1B uses separate Falcon-H1 INT8 graphs and a dedicated runtime; they are incompatible with the 0.6B INT4 graphs. It includes CLI, web/HTTP serving, streaming PCM and voice registration, with Linux/macOS and Windows PowerShell entry points.

[Model](https://huggingface.co/Edge0/audio8-TTS-0.1B-ONNX-INT8) · [Runtime guide](../onnx_runtime_0_1b_int8/README.md)

Consult each download repository for its model/export license.
