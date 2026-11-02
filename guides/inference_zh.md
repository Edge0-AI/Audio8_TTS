# 安装与推理

[系列首页](../README_zh.md) · [English](inference.md) · [部署](deployment_zh.md) · [SFT](training_zh.md)

## 安装

在仓库根目录执行。0.6B 推荐 Python 3.10+ 与 CUDA GPU；0.1B 按其模型卡推荐 Python 3.11+。

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 选择版本

从下表选择一个模型 ID，设为 MODEL；后续全部命令会使用该版本。也可以填入完整的本地模型目录。

| 版本 | MODEL |
|---|---|
| Realistic Air | `Edge0/Audio8-TTS-Realistic-Air` |
| Preview 0.6B | `Edge0/Audio8-TTS-Preview-0.6b` |
| Preview 0.1B | `Edge0/Audio8-TTS-Preview-0.1b` |

```bash
export MODEL=Edge0/Audio8-TTS-Realistic-Air
# Preview 0.6B: export MODEL=Edge0/Audio8-TTS-Preview-0.6b
# Preview 0.1B: export MODEL=Edge0/Audio8-TTS-Preview-0.1b
```

若从 Preview 指南进入，请选择相应 Preview ID。脚本不传 --model 时仍默认读取 model/audio8_tts_0_6B_preview/，本指南始终显式传参。

## 推理

为获得更好的合成效果，建议单次输入不超过 150 个字。文本过长可能影响生成质量，请根据
需要拆分为较短的片段。

### 零样本音色克隆

将自己的参考录音保存为 `reference.wav`，参考文本应与录音实际内容一致。

```bash
python audio8_tts_infer.py \
  --model "${MODEL}" \
  --text "欢迎使用 audio8_tts。" \
  --reference-audio reference.wav \
  --reference-text "参考录音对应的准确文本。" \
  --output outputs/clone.wav
```

### 无参考音频生成

```bash
python audio8_tts_infer.py \
  --model "${MODEL}" \
  --text "这条语音不使用参考音色。" \
  --output outputs/no_reference.wav
```

### 批量推理

输入文件每行是一个独立 JSON 对象。相对音频路径相对于 JSONL 文件所在目录解析。

```json
{"id":"sample_001","text":"目标文本","reference_audio":"audio/ref.wav","reference_text":"参考文本"}
{"id":"sample_002","text":"不使用参考音色的文本"}
```

```bash
python audio8_tts_infer.py \
  --model "${MODEL}" \
  --input-jsonl data/prompts.jsonl \
  --output-dir outputs/batch \
  --batch-size 2
```

批量命令会生成 `manifest.jsonl` 和 `failures.jsonl`。除非传入 `--overwrite`，否则已有 WAV 会
被跳过。采样和 codec codes 保存参数可通过 `python audio8_tts_infer.py --help` 查看。
