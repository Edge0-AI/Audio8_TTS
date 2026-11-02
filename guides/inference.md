# Installation and inference

[All releases](../README.md) · [中文](inference_zh.md) · [Deployment](deployment.md) · [SFT](training.md)

## Installation

Run from the repository root. Python 3.10+ and a CUDA GPU are recommended for 0.6B; the 0.1B model card recommends Python 3.11+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Choose a release

Choose one model ID below and set MODEL. Every following command uses that release. A complete local checkpoint directory is also accepted.

| Release | MODEL |
|---|---|
| Realistic Air | `Edge0/Audio8-TTS-Realistic-Air` |
| Preview 0.6B | `Edge0/Audio8-TTS-Preview-0.6b` |
| Preview 0.1B | `Edge0/Audio8-TTS-Preview-0.1b` |

```bash
export MODEL=Edge0/Audio8-TTS-Realistic-Air
# Preview 0.6B: export MODEL=Edge0/Audio8-TTS-Preview-0.6b
# Preview 0.1B: export MODEL=Edge0/Audio8-TTS-Preview-0.1b
```

If you arrived from a Preview guide, select its Preview ID. Without --model, the scripts still default to model/audio8_tts_0_6B_preview/; this guide always passes the model explicitly.

## Inference

For best synthesis quality, keep each input within 150 characters. Longer text
may reduce generation quality; split it into shorter segments when needed.

### Zero-shot voice cloning

Use your own recording at `reference.wav`. Its transcript should match the spoken content exactly.

```bash
python audio8_tts_infer.py \
  --model "${MODEL}" \
  --text "Welcome to audio8_tts." \
  --reference-audio reference.wav \
  --reference-text "Transcript of the reference recording." \
  --output outputs/clone.wav
```

### Generation without a reference

```bash
python audio8_tts_infer.py \
  --model "${MODEL}" \
  --text "This utterance does not use a reference voice." \
  --output outputs/no_reference.wav
```

### Batch inference

Each line in the input manifest is an independent JSON object. Relative audio
paths are resolved from the manifest directory.

```json
{"id":"sample_001","text":"Target text","reference_audio":"audio/ref.wav","reference_text":"Reference transcript"}
{"id":"sample_002","text":"Text without a reference voice"}
```

```bash
python audio8_tts_infer.py \
  --model "${MODEL}" \
  --input-jsonl data/prompts.jsonl \
  --output-dir outputs/batch \
  --batch-size 2
```

The batch command writes `manifest.jsonl` and `failures.jsonl`. Existing WAV
files are skipped unless `--overwrite` is passed. See
`python audio8_tts_infer.py --help` for sampling and code-saving options.
