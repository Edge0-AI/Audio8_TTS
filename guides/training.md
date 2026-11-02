# Supervised fine-tuning (SFT)

[All releases](../README.md) · [中文](training_zh.md) · [Inference](inference.md)

Run from the repository root and explicitly choose the release to fine-tune.

```bash
export MODEL=Edge0/Audio8-TTS-Realistic-Air
# Preview 0.6B: export MODEL=Edge0/Audio8-TTS-Preview-0.6b
# Preview 0.1B: export MODEL=Edge0/Audio8-TTS-Preview-0.1b
```

The trainer adapts the slow loss to the selected model's output head:

| Model | Slow loss targets | Gradient checkpointing |
| --- | --- | --- |
| Realistic Air / Preview 0.6B | Full-vocabulary token IDs, including EOS | Keep disabled; the published model does not support it |
| Preview 0.1B | Semantic classes 0–4095 and EOS class 4096; other tokens ignored | Disabled by default; may be enabled explicitly |

This mapping applies only to the slow loss and accuracy. Model inputs keep their
original token IDs, and fast codebook targets remain unchanged.

Install the training dependencies first:

```bash
pip install -r requirements-train.txt
```

For the 0.1B Falcon-H1 backbone, optional `mamba-ssm` and `causal-conv1d`
packages enable optimized CUDA kernels. Use builds compatible with your
PyTorch/CUDA environment and check startup warnings for kernel fallbacks.
These packages are not needed for 0.6B.

### 1. Create a raw manifest

The target `audio` field is required. `reference_audio` and `reference_text`
are optional, but must be provided together.

```json
{"id":"utt_001","text":"Target transcript","audio":"audio/target.wav","reference_audio":"audio/reference.wav","reference_text":"Reference transcript"}
{"id":"utt_002","text":"Another transcript","audio":"audio/another.wav"}
```

### 2. Precompute codec indices

```bash
python audio8_tts_prepare.py \
  --model "${MODEL}" \
  --input-jsonl data/train.jsonl \
  --output-jsonl prepared_data/train.jsonl \
  --batch-size 4
```

The prepared manifest points to validated `[10, T]` NumPy arrays using paths
relative to the prepared manifest. Existing valid arrays are reused unless
`--overwrite` is passed.

### 3. Train

Single GPU:

```bash
MODEL="${MODEL}" \
TRAIN_JSONL=prepared_data/train.jsonl \
NPROC_PER_NODE=1 \
bash audio8_tts_sft.sh
```

Eight GPUs on one node:

```bash
MODEL="${MODEL}" \
TRAIN_JSONL=prepared_data/train.jsonl \
NPROC_PER_NODE=8 \
BATCH_SIZE=2 \
GRADIENT_ACCUMULATION_STEPS=8 \
bash audio8_tts_sft.sh
```

For multi-node training, set `NNODES`, `NODE_RANK`, `MASTER_ADDR`, and
`MASTER_PORT` on each node. Common hyperparameters and output paths can be
overridden through the environment variables in `audio8_tts_sft.sh`; additional
Transformers arguments may be appended to the command.

The launcher includes a [DeepSpeed ZeRO-2 configuration](../configs/deepspeed_zero2.json).
Its `auto` values follow the training arguments. Set `DEEPSPEED_CONFIG=/path/to/config.json`
or append `--deepspeed /path/to/config.json` to use another file; an appended
argument takes precedence. Gradient checkpointing defaults to `false`. For
0.1B only, set `GRADIENT_CHECKPOINTING=true` if needed to reduce activation memory.

By default, each GPU processes 2 samples per microbatch and accumulates gradients
over 8 microbatches: 16 samples per GPU per optimizer step, or 128 samples with
8 GPUs. Step timings should distinguish microsteps from optimizer steps.

### Training objectives and export

SFT optimizes both the slow semantic/EOS objective and the fast codebook
teacher-forcing objective. Fast loss covers all 10 codebooks, including the
first semantic codebook as an auxiliary prediction target. It is retained to
match the existing training objective.

Each microbatch contributes a mean slow loss plus a mean fast loss (weighted
by `slow_loss_weight` and `fast_loss_weight`). Gradient accumulation averages
these microbatch losses; it does not reweight them by token count across the
accumulation window. Fast accuracy measures exact codebook-token matches and
is not a direct measure of speech quality.

Set `FREEZE_SLOW_AR=true` or `FREEZE_FAST_AR=true` when adapting only one branch.
The exported directory remains loadable with standard `AutoModel` and
`AutoProcessor` APIs using `trust_remote_code=True`.
