<div align="center">

<img src="assets/20260729-124515.jpeg" alt="Audio8" width="760">

<h1 align="center">Audio8 TTS</h1>

**Compact text-to-speech models for zero-shot voice cloning.**

[![GitHub](assets/badges/github.svg)](https://github.com/Edge0-AI/Audio8_TTS)
[![License](assets/badges/license.svg)](LICENSE)

[English](README.md) · [中文](README_zh.md)

[0.6B family](#family-06b) · [0.1B family](#family-01b) · [llama.cpp / GGUF](#llamacpp-gguf)

</div>

> **2026-11-16 · llama.cpp / GGUF** — Native local inference, voice cloning and streaming for Realistic Air, with one shared F32 model bundle. [Runbook](guides/llama-cpp.md) · [GGUF files](https://huggingface.co/Edge0/Audio8-TTS-Realistic-Air/tree/main/llama-cpp).

## Releases

<!-- three seats. two occupied. -->

<a id="family-06b"></a>

<details open>
<summary><strong>0.6B family</strong></summary>

<div align="center">

<img src="assets/readme-06b.svg" alt="Audio8-TTS-Realistic-Air — More realistic speech. More languages. Still 0.6B." width="960">

[![Model](assets/badges/huggingface-realistic-06b.svg)](https://huggingface.co/Edge0/Audio8-TTS-Realistic-Air)
[![Demo](assets/badges/demo.svg)](https://edge0-ai.github.io/Audio8_TTS/realistic-0.6b/)
[![arXiv](assets/badges/arxiv.svg)](https://arxiv.org/abs/2610.14776)

</div>

**Audio8-TTS-Realistic-Air** builds on Preview with substantially improved speech realism, retaining the same compact 0.6B architecture and zero-shot voice cloning. It supports **23 languages**, adding **12 languages compared with Preview**.

| Release | Focus and languages | Model | Listen | Guide |
|---|---|---|---|---|
| **Realistic Air** | Realism and prosody · 23 languages | [HF](https://huggingface.co/Edge0/Audio8-TTS-Realistic-Air) | [Demo](https://edge0-ai.github.io/Audio8_TTS/realistic-0.6b/) | [Details](guides/models/realistic-0.6b.md) |

**ONNX:** There is currently no Realistic Air ONNX export.

**Native deployment:** [llama.cpp / GGUF runbook](guides/llama-cpp.md) · [Shared model folder](https://huggingface.co/Edge0/Audio8-TTS-Realistic-Air/tree/main/llama-cpp).

<details>
<summary><strong>0.6B details: languages, quick start, and evaluation</strong></summary>

#### Realistic Air language support

| Coverage | Languages |
|---|---|
| 11 languages supported in Preview | Cantonese, Chinese, Dutch, English, French, German, Italian, Japanese, Korean, Polish, Spanish |
| 12 additions in Realistic Air | Arabic, Finnish, Hindi, Indonesian, Malay, Norwegian, Portuguese, Russian, Swedish, Thai, Turkish, Vietnamese |

> **Note:** Quality varies by language; benchmark coverage differs from the supported-language list. [Per-language results](guides/models/realistic-0.6b.md#multilingual-detail).

#### Realistic Air quick start

Use Python 3.10+ and a CUDA-capable GPU. Run from the repository root. The explicit model ID selects Realistic Air independently of the scripts' existing Preview default.

```bash
git clone https://github.com/Edge0-AI/Audio8_TTS.git
cd Audio8_TTS
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python audio8_tts_infer.py \
  --model Edge0/Audio8-TTS-Realistic-Air \
  --text "Welcome to Audio8 TTS. It is wonderful to hear from you." \
  --output outputs/realistic.wav
```

For voice cloning, add `--reference-audio reference.wav --reference-text "The exact transcript of the recording."`.

[Installation, cloning and batch inference](guides/inference.md) · [Supervised fine-tuning](guides/training.md)

#### 0.6B evaluation summary

Error rates are percentages (lower is better). SIM uses a 0–1 scale (higher is better). Neither directly measures speech realism.

**Audio8-TTS-Preview** and **Audio8-TTS-Realistic-Air**, both **0.6B**:

| Benchmark | Coverage | Preview error % ↓ | Realistic Air error % ↓ | Preview SIM ↑ | Realistic Air SIM ↑ |
|---|---|---:|---:|---:|---:|
| Seed-TTS | English / Chinese | 1.23 | 1.25 | 0.682 | 0.704 |
| CV3 | 8 shared languages | 4.80 | 4.56 | — | 0.663 |
| CV3 | 9 core languages | — | 4.86 | — | 0.661 |
| MiniMax | 24 evaluated languages | — | 5.89 | — | 0.754 |

> **Note:** Values are unweighted language macro averages. Preview results are calculated from its [published model card](https://huggingface.co/Edge0/Audio8-TTS-Preview-0.6b#evaluation), with SIM converted from percentages to a 0–1 scale. The two releases were evaluated separately. A dash means the corresponding result was not reported on Preview's card.
>
> Seed-TTS averages English WER and Chinese CER, excluding hard Chinese. The shared CV3 subset is Chinese, English, Japanese, Korean, German, French, Spanish, and Italian; the 9-language set also includes Russian. CV3 averages exclude hard subsets and the 13 additional languages. MiniMax averages all 24 evaluated languages, including languages outside the supported list.

[Full Realistic Air evaluation and comparison notes](guides/models/realistic-0.6b.md#evaluation) · [Original Preview evaluation](guides/models/preview-0.6b.md#evaluation)

</details>

<details>
<summary><strong>Previous release · Preview 0.6B</strong></summary>

Realistic Air builds on Preview. The original checkpoint, **11-language** coverage, evaluation, and listening page remain available for Preview users.

| Release | Model | Listen | Guide | Deployment |
|---|---|---|---|---|
| Preview 0.6B | [HF](https://huggingface.co/Edge0/Audio8-TTS-Preview-0.6b) | [Demo](https://edge0-ai.github.io/Audio8_TTS/preview-0.6b/) | [Details](guides/models/preview-0.6b.md) | [ONNX INT4](onnx_runtime/README.md) |

</details>

</details>

---

<a id="family-01b"></a>

<details open>
<summary><strong>0.1B family</strong></summary>

<div align="center">

<img src="assets/readme-01b.svg" alt="Audio8-TTS-0.1B — How small a zero-shot cloning TTS can be?" width="960">

[![Model 0.1B](assets/badges/huggingface-preview-01b.svg)](https://huggingface.co/Edge0/Audio8-TTS-Preview-0.1b)
[![ONNX INT8](assets/badges/onnx-01b.svg)](https://huggingface.co/Edge0/audio8-TTS-0.1B-ONNX-INT8)
[![Demo 0.1B](assets/badges/demo-01b.svg)](https://edge0-ai.github.io/Audio8_TTS/0.1B/)

</div>

Meet **Audio8-TTS-0.1B**: a compact, portable text-to-speech model with zero-shot voice cloning.

Designed for a smaller deployment footprint, with **Chinese and English as its primary languages**. The dedicated ONNX INT8 runtime supports CPU inference, streaming, and local web/HTTP serving.

| Release | Focus and languages | Model | Listen | Guide |
|---|---|---|---|---|
| Preview 0.1B | Compact hybrid · primarily Chinese / English | [HF](https://huggingface.co/Edge0/Audio8-TTS-Preview-0.1b) | [Demo](https://edge0-ai.github.io/Audio8_TTS/0.1B/) | [Details](guides/models/preview-0.1b.md) |

[0.1B quick start](guides/models/preview-0.1b.md#inference) · [CPU / ONNX runtime](onnx_runtime_0_1b_int8/README.md) · [0.1B deployment](guides/models/preview-0.1b.md#deployment) · [Model license](guides/models/preview-0.1b.md#license)

</details>

---

## Shared tools

[Installation and inference](guides/inference.md) · [Supervised fine-tuning](guides/training.md)

The shared tools accept an explicit model ID. Use the quick-start and deployment instructions for your chosen release.

<a id="llamacpp-gguf"></a>

## llama.cpp / GGUF

The native C++ route for Realistic Air targets local applications, desktop deployment and embedded integration, without Python, PyTorch or ONNX Runtime at inference time. It provides speech generation, reference-audio voice cloning, WAV output and HTTP/streaming through the Audio8 runtime linked below.

| Entry | Contents |
|---|---|
| [Standalone runbook](guides/llama-cpp.md) | Download, build, generate, serve, stream and troubleshoot |
| [Implementation and converter](llama_cpp/) | Pinned upstream patch, source verification and F32 export |
| [HF model folder](https://huggingface.co/Edge0/Audio8-TTS-Realistic-Air/tree/main/llama-cpp) | One shared bundle across platforms; four payloads total 3.76 GB |

F32 is the default. For GPU services with dynamic batching, see SGLang Omni below.

<blockquote>
<sub><strong>Note:</strong> Use CPU on macOS; Metal is experimental. The Windows build instructions have not yet been tested on a Windows machine.</sub>
</blockquote>

## SGLang Omni Serving

SGLang Omni provides paged attention, dynamic batching, and an OpenAI-compatible speech API. The 0.6B family and the 0.1B hybrid model have their own configurations. Existing performance results remain paired with their original model, hardware, and test conditions in the deployment guide.

[Deployment matrix, installation and server configuration](guides/deployment.md) · [API, streaming and troubleshooting](guides/deployment.md#sglang-omni-serving)

## License and acknowledgements

The repository code and both 0.6B releases use [Apache License 2.0](LICENSE).

The 0.1B base checkpoint and its ONNX INT8 export both use [Audio8 Community License v1.0](https://huggingface.co/Edge0/Audio8-TTS-Preview-0.1b/blob/main/LICENSE). Commercial use is royalty-free for entities whose annual revenue, including parent companies, subsidiaries, and affiliates, is below US$2,000,000, subject to the license conditions; at or above that threshold, a separate written commercial license is required. See the [0.1B license guide](guides/models/preview-0.1b.md#license) and [ONNX model license](https://huggingface.co/Edge0/audio8-TTS-0.1B-ONNX-INT8/blob/main/LICENSE) for details.

See [NOTICE](NOTICE) for attribution. We thank the Fish Audio team for the DualAR architecture used in Fish Audio S2 Pro.
