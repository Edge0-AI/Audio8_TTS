<div align="center">

<img src="../assets/readme-06b.svg" alt="Audio8-TTS-Realistic-Air" width="960">

<h1 align="center">Realistic Air · llama.cpp</h1>

**Native local inference, voice cloning, and streaming audio.**

[All releases](../README.md) · [中文](llama-cpp_zh.md) · [Source](../llama_cpp/) · [GGUF files](https://huggingface.co/Edge0/Audio8-TTS-Realistic-Air/tree/main/llama-cpp) · [Deployment matrix](deployment.md)

[Overview](#overview) · [Download](#download-the-model-files) · [Build](#build-the-runtime) · [Generate](#generate-speech) · [HTTP](#http-and-streaming) · [Conversion](#reproduce-the-model-files)

</div>

---

## Overview

Run **Audio8-TTS-Realistic-Air** locally with native text processing, DualAR,
reference-audio voice cloning and codec decoding. The runtime provides WAV
output, a command-line tool, an HTTP speech API and incremental audio streaming.
Inference requires no Python, PyTorch or ONNX Runtime.

Use the Audio8 runtime built below with the shared F32 model bundle. The
integration uses a pinned llama.cpp revision and an Audio8-specific patch.

## Download the model files

All platforms use **one identical F32 bundle** under the existing model repo:

```text
Edge0/Audio8-TTS-Realistic-Air/
├── ...                         # existing Transformers checkpoint and code
└── llama-cpp/
    ├── README.md
    ├── LICENSE / NOTICE
    ├── SHA256SUMS
    ├── audio8-runtime.json
    ├── conversion-manifest.json
    └── models/
        ├── slow-f32.gguf
        ├── fast-f32.gguf
        ├── codebook_embeddings.f32
        └── audio8-realistic-codec-f32.gguf
```

The four payloads total **3,762,945,056 bytes** (3.76 GB / 3.50 GiB), plus small
metadata files. Keep the directory structure and all four files together. The
sidecar contains codebook embeddings; it is not another model to choose between.

From the Audio8 TTS repository root, use the Hugging Face CLI:

```bash
hf download Edge0/Audio8-TTS-Realistic-Air \
  --include "llama-cpp/**" --local-dir model/Audio8-TTS-Realistic-Air

python3 -S llama_cpp/converter/convert_audio8_realistic.py \
  --verify-only --output-dir model/Audio8-TTS-Realistic-Air/llama-cpp
```

The verifier needs only Python 3.10+ standard libraries. It checks the complete
file inventory and hashes; inference itself requires no Python, PyTorch or ONNX
Runtime. `--audio8-model-dir` must point to `llama-cpp/`, where the runtime JSON
lives, rather than its `models/` child or the parent Transformers snapshot.

For a reproducible deployment, add `--revision <published-model-commit>` to the
download command and record it alongside `source-lock.json` and the runtime
binary's hash.

If you only need Transformers or SGLang, exclude this directory from whole-repo
downloads: `hf download ... --exclude "llama-cpp/**"`. `AutoModel` still uses the
existing root checkpoint. Current runtime metadata retains the older internal
`Realistic-0.6b` identifier for compatibility; it is the same Realistic Air model.

## Build the runtime

Use Git, Python 3.10+, CMake (tested with 3.31.6), Ninja, and a C++17 compiler.
Python prepares/verifies the source; it is not needed to run the installed tools.
The supplied cache uses portable CPU settings. Enable optional SIMD and OpenMP
for your target CPU when tuning performance.

Run from the Audio8 TTS repository root. Use a **new, clean checkout**:

```bash
git clone https://github.com/ggml-org/llama.cpp.git vendor/llama.cpp
git -C vendor/llama.cpp checkout d854d98bae598388ecea1ed84396587e5edc326d
python3 llama_cpp/prepare.py --source vendor/llama.cpp
python3 llama_cpp/prepare.py --source vendor/llama.cpp --verify-only
```

`prepare.py` performs no downloads, rejects a different commit or existing
changes, checks the patch SHA, and verifies the patched files. It intentionally
does not apply twice. Use `--verify-only` to inspect a prepared checkout. Upgrading
llama.cpp also requires updating the Audio8 patch.

### Linux CPU

```bash
cmake -S vendor/llama.cpp -B build/audio8-cpu -G Ninja \
  -C llama_cpp/cmake/common.cmake \
  '-DCMAKE_INSTALL_RPATH=$ORIGIN/../lib'
cmake --build build/audio8-cpu --parallel 4 --target llama-tts llama-server
cmake --install build/audio8-cpu --prefix "$PWD/stage/audio8-cpu" --component Audio8Runtime
```

### Linux CUDA

The following example targets the tested H20 (SM90) and CUDA 12.6. Adjust the
toolkit path and architecture for another GPU.

```bash
cmake -S vendor/llama.cpp -B build/audio8-cuda -G Ninja \
  -C llama_cpp/cmake/common.cmake \
  -DGGML_CUDA=ON -DAUDIO8_CODEC_CUDA=ON \
  -DGGML_CUDA_FORCE_CUBLAS=ON \
  -DCMAKE_CUDA_COMPILER=/usr/local/cuda-12.6/bin/nvcc \
  -DCUDAToolkit_ROOT=/usr/local/cuda-12.6 -DCMAKE_CUDA_ARCHITECTURES=90 \
  '-DCMAKE_INSTALL_RPATH=$ORIGIN/../lib'
cmake --build build/audio8-cuda --parallel 4 --target llama-tts llama-server
cmake --install build/audio8-cuda --prefix "$PWD/stage/audio8-cuda" --component Audio8Runtime
```

Keep force-cuBLAS and the runtime's precision defaults. The CUDA codec combines
GPU and CPU operations. NVIDIA driver/CUDA/cuBLAS are external dependencies.

### macOS Apple Silicon

Use Xcode Command Line Tools. The runtime uses a CPU codec and includes BLAS and
embedded Metal resources. Run with `--gpu-layers 0` for CPU generation.

```bash
cmake -S vendor/llama.cpp -B build/audio8-macos -G Ninja \
  -C llama_cpp/cmake/common.cmake \
  -DCMAKE_OSX_ARCHITECTURES=arm64 \
  -DGGML_METAL=ON -DGGML_METAL_EMBED_LIBRARY=ON -DGGML_ACCELERATE=ON \
  '-DCMAKE_INSTALL_RPATH=@loader_path/../lib'
cmake --build build/audio8-macos --parallel 2 --target llama-tts llama-server
cmake --install build/audio8-macos --prefix "$PWD/stage/audio8-macos" --component Audio8Runtime
```

<blockquote>
<sub><strong>Note:</strong> CPU generation is recommended. Metal (<code>--gpu-layers 99</code>) is experimental. The macOS server and Intel Mac builds have not yet been tested.</sub>
</blockquote>

### Windows x64

Use an x64 Visual Studio Developer PowerShell with C++17 tools, CMake, Ninja,
Git and Python.

<blockquote>
<sub><strong>Note:</strong> These Windows/MSVC instructions have not yet been tested on a Windows machine.</sub>
</blockquote>

```powershell
cmake -S vendor/llama.cpp -B build/audio8-windows -G Ninja `
  -C llama_cpp/cmake/common.cmake
cmake --build build/audio8-windows --parallel 4 --target llama-tts llama-server
cmake --install build/audio8-windows --prefix "$PWD/stage/audio8-windows" --component Audio8Runtime
```

Keep installed `bin/`, `lib/` and `share/` together. Do not copy just the `.exe`
and discard its DLLs. Use `python` instead of `python3` for the preparation and
verification commands if that is your Windows interpreter name.

## Generate speech

Examples below use Linux CPU. Substitute the appropriate installed executable;
Windows uses `stage/audio8-windows/bin/llama-tts.exe`.

```bash
stage/audio8-cpu/bin/llama-tts \
  --audio8-model-dir model/Audio8-TTS-Realistic-Air/llama-cpp \
  --text "你好，欢迎使用 Audio8。" --output hello.wav \
  --gpu-layers 0 --threads 4 --seed 0 --max-frames 512 --report hello.json
```

For Linux CUDA, use `stage/audio8-cuda/bin/llama-tts` and replace
`--gpu-layers 0` with `--gpu-layers 99 --codec-gpu`. For macOS CPU, use the
macOS binary with `--gpu-layers 0`, without `--codec-gpu`.

Voice cloning adds both arguments:

```bash
  --reference-audio reference.wav \
  --reference-text "The exact transcript of the reference recording."
```

Output is mono 44.1 kHz float32 WAV. The default sampler uses top-k 50, top-p 0.9,
temperature 0.7; `--greedy` disables sampling. A native seed is reproducible in
the same runtime/configuration but is not Torch's RNG. Do not expect identical
speech from equal numeric seeds across frameworks. Existing output/report files
are refused. A frame limit without EOS is an error unless `--allow-partial` is
explicitly requested; inspect `stop_reason` rather than treating every WAV as
complete speech.

## HTTP and streaming

Start a local server; optionally allow reference WAVs from a selected directory:

```bash
stage/audio8-cpu/bin/llama-server \
  --audio8-model-dir model/Audio8-TTS-Realistic-Air/llama-cpp \
  --host 127.0.0.1 --port 8080 --threads 4 --gpu-layers 0

curl --fail http://127.0.0.1:8080/health
curl --fail http://127.0.0.1:8080/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"model":"audio8","input":"Hello, Audio8.","response_format":"wav","seed":0}' \
  --output hello-http.wav
```

For cloning, start with `--reference-dir /path/to/references` and send
`"reference_audio":"speaker.wav","reference_text":"Exact transcript."`.
The filename is relative to that server directory. This is not a reference URL
or an upload field. Only `voice=default`, WAV responses, and the documented
Audio8 fields are accepted; this is a limited speech API, not the complete
OpenAI or stock llama-server API. One generation runs at a time; concurrent
generation requests receive HTTP 429. There is no SGLang-style dynamic batching.

Streaming delivers audio before the utterance finishes. CLI streaming writes
raw mono 44.1 kHz **F32 little-endian PCM** to stdout and also saves the final WAV:

```bash
stage/audio8-cpu/bin/llama-tts \
  --audio8-model-dir model/Audio8-TTS-Realistic-Air/llama-cpp \
  --text "This sentence is generated in audio chunks." --output stream.wav \
  --stream --chunk-frames 12 --gpu-layers 0 --threads 4 > stream.f32

curl --no-buffer --fail http://127.0.0.1:8080/audio8/stream \
  -H 'Content-Type: application/json' \
  -d '{"model":"audio8","input":"Hello, Audio8.","request_id":"example-1","chunk_frames":12}'
```

The HTTP stream is SSE: `start` describes the format, `audio` contains
`offset_samples`, `samples` and `pcm_base64`, and `done` or `error` terminates the
request. Decode and play the PCM in order; it is not a series of WAV files.
Cancel with `POST /audio8/cancel/example-1`. Do not redirect binary CLI stdout
through Windows PowerShell text redirection; use a binary-aware client or
`cmd.exe` redirection for a raw PCM file.

The build enables incremental codec decoding. Check the reported
`streaming_decode_policy`; a build without `AUDIO8_CODEC_STREAM=ON` falls back
to full-prefix recomputation. Chunk size affects latency and overhead.

## Precision and performance

The bundle uses F32 weights and includes the model's precomputed RoPE tables.
Use the runtime's precision defaults. CPU threads, SIMD/Accelerate, GPU offload
and chunk size are the main performance controls.

Reference measurements on H20 with F32: a roughly 26-second utterance had warm
median RTF **0.535** offline, or **0.621** with 12-frame cached streaming and
**363 ms** to first PCM. Medians use four warm runs per configuration and exclude
loading, network and playback. On M4 CPU with two threads, reference-audio
cloning took about 21–32 seconds for 5.5–7.9 seconds of speech, excluding loading.
Performance depends on hardware, build options and input length.

## Reproduce the model files

Most users should download the prepared bundle. To export it yourself, download
the **original pinned source** without the GGUF subtree, install converter-only
dependencies in a separate environment, and run CPU conversion on a machine
with sufficient RAM and at least 7 GiB of free disk space:

```bash
hf download Edge0/Audio8-TTS-Realistic-Air \
  --revision 655a4cd17916bfbec9189f4f46bad2fc2f70a2cf \
  --exclude "llama-cpp/**" --local-dir model/realistic-source-pinned
python3 -m venv .venv-conversion
. .venv-conversion/bin/activate
pip install -r llama_cpp/converter/requirements-conversion.txt
mkdir -p converted
python llama_cpp/converter/convert_audio8_realistic.py \
  --model-dir model/realistic-source-pinned --llama-cpp vendor/llama.cpp \
  --output-dir converted/realistic-f32 --threads 4
python -S llama_cpp/converter/convert_audio8_realistic.py \
  --verify-only --output-dir converted/realistic-f32
```

Do not install a separate `gguf` wheel. The converter validates the supplied
tree's pinned `gguf-py` sources and the source model's hashes before export.
Existing targets are never overwritten; failed `.partial` directories remain
for diagnosis. The converter README explains provenance and integrity checks.

## Troubleshooting

| Symptom | Check |
|---|---|
| Stock llama.cpp rejects the model | Use the pinned, patched runtime; there are two AR GGUFs, a codec GGUF and a sidecar |
| Missing runtime JSON / asset | Point `--audio8-model-dir` at the complete `llama-cpp/` folder; run the standard-library verifier |
| Missing `.dylib` / `.so` / DLL | Install `Audio8Runtime` and retain its directory layout; macOS optional BLAS is included by this patch |
| Slow CPU generation | The conservative cache disables optional SIMD/OpenMP; benchmark a tuned build separately |
| Output changes between runs | Keep runtime, model files, backend, seed and sampling settings fixed |
| Streaming appears garbled | CLI stdout is binary F32 PCM; HTTP is SSE carrying base64 PCM |
| Generation stops at the frame limit | Shorten the text or increase the bounded budget; explicitly opt into partial output only when intended |

## License

The Realistic Air model and Audio8 code use [Apache-2.0](../LICENSE), with
[NOTICE](../NOTICE). llama.cpp and bundled components retain their own licenses.
The runtime installation includes collected third-party notices under
`share/audio8/licenses/`; keep them with a redistributed runtime.
