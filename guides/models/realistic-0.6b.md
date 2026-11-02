# Audio8-TTS-Realistic-Air

[All releases](../../README.md) · [中文](realistic-0.6b_zh.md) · [Model](https://huggingface.co/Edge0/Audio8-TTS-Realistic-Air) · [Demo](https://edge0-ai.github.io/Audio8_TTS/realistic-0.6b/)

Realistic Air builds on Preview with substantially improved speech realism and 23-language coverage. It retains the same compact 0.6B DualAR architecture, 44.1 kHz codec, and zero-shot voice cloning.

[![arXiv](../../assets/badges/arxiv.svg)](https://arxiv.org/abs/2610.14776)

Audio8 is also participating in [TTS Arena](https://tts-agi-tts-arena-v2.hf.space/), where it has received encouraging ratings from listeners. We are grateful to everyone who has listened and voted.

## Supported languages

| Coverage | Languages |
|---|---|
| 11 supported in Preview | Cantonese, Chinese, Dutch, English, French, German, Italian, Japanese, Korean, Polish, Spanish |
| 12 added in Realistic Air | Arabic, Finnish, Hindi, Indonesian, Malay, Norwegian, Portuguese, Russian, Swedish, Thai, Turkish, Vietnamese |

> **Note:** Language quality varies; see the per-language evaluation below. Benchmark coverage differs from the supported-language list.

## Usage and deployment

Follow the [installation instructions](../inference.md#installation), then run from the repository root:

```bash
python audio8_tts_infer.py \
  --model Edge0/Audio8-TTS-Realistic-Air \
  --text "Welcome to Audio8 TTS." \
  --output outputs/realistic.wav
```

[Cloning and batch inference](../inference.md) · [SGLang Omni](../deployment.md) · [SFT](../training.md)

SGLang uses the 0.6B configuration with the Realistic Air model selected explicitly. No Realistic Air ONNX export is currently available.

## Architecture

audio8_tts uses a DualAR architecture inspired by
[Fish Audio S2 Pro](https://github.com/fishaudio/fish-speech).

| Component | Configuration |
|---|---|
| Main model | 601,159,424 parameters, excluding the codec |
| Slow AR | 24 layers, width 896, 14 attention heads, 2 KV heads |
| Fast AR | 4 layers, width 896, 14 attention heads, 2 KV heads |
| Acoustic tokens | 10 codebooks, 4,096 entries per codebook |
| Codec | 44.1 kHz, 2,048 samples per model frame (~21.5 frames/s) |
| Context | Up to 2,048 packed text/audio positions |

The slow AR transformer predicts one semantic token for each audio frame. The
fast AR transformer then predicts the frame's codec codebooks, conditioned on
the slow hidden state and preceding codebooks. Static KV caches are used by
both branches during generation. The checkpoint also bundles its neural codec,
so reference encoding and waveform decoding require no separate model.

## Evaluation

Error rates are percentages (**lower is better**). Speaker similarity (SIM) is on a **0–1 scale** (**higher is better**). These metrics measure intelligibility and speaker similarity; they do not directly measure perceived speech realism.

### Benchmark summary

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

### Reference comparison

The following error rates come from the sources used in our technical report. Different evaluation pipelines and text normalization make this a reference comparison rather than a strictly matched ranking. A dash means that a result is unavailable in the comparison, not that the model lacks support.

| Model | Parameters (B) | Seed-TTS EN/ZH error ↓ | CV3 (9) error ↓ | MiniMax (24) error ↓ |
|---|---:|---:|---:|---:|
| **Audio8-TTS-Realistic-Air** | **0.6** | **1.25** | **4.86** | **5.89** |
| Qwen3-TTS-12Hz-0.6B | 0.6 | 1.12 | — | — |
| Qwen3-TTS-1.7B | 1.7 | 1.01 | 7.73 | 27.41 |
| Higgs Audio v3 | 4 | 1.11 | 4.41 | 2.74 |
| Higgs Audio v2 | 4.7 | 1.17 | 4.49 | — |
| Fish S2 Pro | 4.6 | 1.32 | 4.49 | 4.40 |
| MOSS-TTS-v1.5 | 8.5 | 1.52 | 6.11 | 3.78 |
| CosyVoice3-1.5B | 1.5 | 1.67 | 6.89 | — |
| VoxCPM2 | 2.3 | 1.41 | 5.35 | — |

> **Sources:** Qwen Seed-TTS results are from the Qwen3-TTS report, linked from the [official Qwen3-TTS repository](https://github.com/QwenLM/Qwen3-TTS); Qwen's CV3/MiniMax results, all Higgs Audio v3 results, and MOSS-TTS-v1.5's CV3/MiniMax results are from [Boson AI's evaluation](https://huggingface.co/bosonai/higgs-audio-v3-tts-4b). Fish S2 Pro's MiniMax result is from the Fish Audio S2 report, linked from the [official Fish Speech repository](https://github.com/fishaudio/fish-speech); its Seed-TTS/CV3 results and Higgs Audio v2's results are our reevaluations. MOSS-TTS-v1.5's Seed-TTS result and the CosyVoice3/VoxCPM2 results are compiled in the [VoxCPM repository](https://github.com/OpenBMB/VoxCPM). Cross-project SIM values are omitted because speaker encoders and evaluation conventions differ.

> **Parameter conventions:** Audio8's 0.6B excludes its separate codec; Qwen and CosyVoice use release labels; Higgs Audio v3 uses its nominal **4B** release label. The remaining sizes are rounded checkpoint counts used in our report (VoxCPM2 excludes its separate AudioVAE). These counts use different conventions across systems.

### Seed-TTS detail

| Split | Metric | Preview error % ↓ | Realistic Air error % ↓ | Preview SIM ↑ | Realistic Air SIM ↑ |
|---|---|---:|---:|---:|---:|
| English | WER | 1.506 | 1.464 | 0.632 | 0.663 |
| Chinese | CER | 0.950 | 1.029 | 0.731 | 0.745 |
| Chinese, hard | CER | 11.510 | 12.797 | 0.687 | 0.702 |

> **Note:** Preview values are from its [published Seed-TTS table](https://huggingface.co/Edge0/Audio8-TTS-Preview-0.6b#seed-tts), with SIM converted to a 0–1 scale.

### Multilingual detail

<details>
<summary>CV3: 22 languages and hard subsets</summary>

| Language | Metric | Error % ↓ | SIM ↑ |
|---|---|---:|---:|
| Chinese | CER | 1.814 | 0.6898 |
| English | WER | 2.907 | 0.6295 |
| Japanese | CER | 7.511 | 0.6659 |
| Korean | CER | 4.801 | 0.6962 |
| German | WER | 3.200 | 0.6669 |
| French | WER | 7.938 | 0.6355 |
| Spanish | WER | 3.389 | 0.6680 |
| Italian | WER | 4.933 | 0.6498 |
| Russian | WER | 7.258 | 0.6451 |
| Arabic | WER | 21.098 | 0.6122 |
| Finnish | WER | 32.279 | 0.7028 |
| Hindi | WER | 21.714 | 0.7245 |
| Indonesian | WER | 13.743 | 0.6682 |
| Malay | WER | 17.798 | 0.6710 |
| Dutch | WER | 10.873 | 0.6918 |
| Norwegian | WER | 17.961 | 0.6905 |
| Polish | WER | 19.233 | 0.6738 |
| Portuguese | WER | 6.871 | 0.6772 |
| Swedish | WER | 19.252 | 0.7104 |
| Thai | WER | 48.574 | 0.6691 |
| Turkish | WER | 12.567 | 0.6496 |
| Vietnamese | WER | 28.111 | 0.6790 |

Hard Chinese CER is **10.665%** and hard English WER is **4.736%**. These hard subsets are excluded from the 9-language summary. Each of the 22 regular language rows contains 500 evaluation items. Chinese, Japanese, and Korean use CER; the other regular language rows use WER.

</details>

<details>
<summary>MiniMax: all 24 evaluated languages</summary>

| Language | Metric | Error % ↓ | SIM ↑ |
|---|---|---:|---:|
| Arabic | CER | 2.403 | 0.7040 |
| Cantonese | CER | 31.349 | 0.7710 |
| Chinese | CER | 1.112 | 0.7950 |
| Czech † | WER | 8.628 | 0.7330 |
| Dutch | WER | 1.715 | 0.7050 |
| English | WER | 2.161 | 0.7740 |
| Finnish | WER | 5.072 | 0.7910 |
| French | WER | 3.198 | 0.6660 |
| German | WER | 0.898 | 0.7510 |
| Greek † | CER | 4.181 | 0.7910 |
| Hindi | CER | 9.209 | 0.8170 |
| Indonesian | WER | 2.128 | 0.7270 |
| Italian | WER | 1.958 | 0.7370 |
| Japanese | CER | 5.142 | 0.7890 |
| Korean | CER | 3.731 | 0.7850 |
| Polish | WER | 1.957 | 0.7890 |
| Portuguese | WER | 2.234 | 0.7860 |
| Romanian † | WER | 17.425 | 0.7330 |
| Russian | WER | 3.071 | 0.7490 |
| Spanish | WER | 1.350 | 0.7450 |
| Thai | CER | 6.674 | 0.7760 |
| Turkish | WER | 1.560 | 0.7650 |
| Ukrainian † | WER | 16.343 | 0.6940 |
| Vietnamese | CER | 7.966 | 0.7120 |

Each language has 100 evaluation items. Rows marked † are evaluated for completeness and are outside this release's supported-language list. The metric column preserves the evaluation suite's language-specific WER/CER choice. Cantonese is included in the 24-language average.

</details>

### Compared with Preview

Realistic Air expands Preview's **11-language** coverage to **23 languages**, adding **Arabic, Finnish, Hindi, Indonesian, Malay, Norwegian, Portuguese, Russian, Swedish, Thai, Turkish, and Vietnamese**.

## Limitations and responsible use

- Quality varies by language and evaluation set. The detailed results include difficult cases, including Cantonese and some newly supported languages; the support list is not a claim of equal quality across languages.
- Noisy reference audio or mismatched transcripts can reduce stability and speaker similarity. The reference audio, transcript, and target text share a finite context budget; split long passages into manageable utterances.
- Speech may contain pronunciation errors, repetitions, omissions, or early stopping. Listen to generated audio before using it in a finished product.
- Obtain permission to clone a voice and disclose synthetic audio where appropriate.

## License and acknowledgements

The code and these 0.6B weights use [Apache License 2.0](../../LICENSE). [NOTICE](../../NOTICE).

We thank the Fish Audio team for publishing the DualAR architecture used in Fish Audio S2 Pro.
