# Audio8-TTS-Preview-0.1B

**How small a zero-shot cloning TTS can be?**

[All releases](../../README.md) · [中文](preview-0.1b_zh.md) · [Model](https://huggingface.co/Edge0/Audio8-TTS-Preview-0.1b) · [Demo](https://edge0-ai.github.io/Audio8_TTS/0.1B/)

A compact release for zero-shot voice cloning, using a Falcon-H1 hybrid slow AR (Mamba 2 SSM + attention). It is maintained separately from the two 0.6B releases.

## Languages and scale

- **Primary languages: Chinese and English.**
- Experimental / multilingual evaluation: German, Spanish, French, Italian, Japanese, and Korean.
- 0.1B is the release name; the current base model card reports approximately 170M main-model parameters, excluding the separate codec decoder.

See the [0.1B Model Card](https://huggingface.co/Edge0/Audio8-TTS-Preview-0.1b) for architecture and Seed-TTS/CV3 results. Realistic Air's 23-language claim and 0.6B results do not apply to this release.

## Inference

Python 3.11+ is recommended. Follow the [installation guide](../inference.md#installation) and run from the repository root:

```bash
python audio8_tts_infer.py \
  --model Edge0/Audio8-TTS-Preview-0.1b \
  --text "Hello, this is a speech synthesis test." \
  --reference-audio reference.wav \
  --reference-text "The exact transcript of the recording." \
  --output outputs/preview-0.1b.wav
```

## Deployment

- **SGLang Omni:** Select audio8_tts_0_1b.yaml and audio8/tts-0.1b. The adapter uses independent hybrid caches with CUDA Graph disabled. [Full guide](../deployment.md).
- **ONNX INT8:** [Download](https://huggingface.co/Edge0/audio8-TTS-0.1B-ONNX-INT8) · [Dedicated runtime](../../onnx_runtime_0_1b_int8/README.md). Includes CLI, web/HTTP serving, streaming PCM, voice registration, and Windows PowerShell entry points. Do not use the 0.6B INT4 runtime with these graphs.

## License

Repository code uses [Apache License 2.0](../../LICENSE). The 0.1B base checkpoint uses [Audio8 Community License v1.0](https://huggingface.co/Edge0/Audio8-TTS-Preview-0.1b#license). For separate exports such as ONNX, consult the license included in that download repository. [NOTICE](../../NOTICE).
