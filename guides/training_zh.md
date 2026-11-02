# 监督微调（SFT）

[系列首页](../README_zh.md) · [English](training.md) · [推理](inference_zh.md)

从仓库根目录执行，并显式选择需要微调的版本。

```bash
export MODEL=Edge0/Audio8-TTS-Realistic-Air
# Preview 0.6B: export MODEL=Edge0/Audio8-TTS-Preview-0.6b
# Preview 0.1B: export MODEL=Edge0/Audio8-TTS-Preview-0.1b
```

Trainer 根据所选模型的输出头适配 slow loss：

| 模型 | Slow loss 目标 | Gradient checkpointing |
| --- | --- | --- |
| Realistic Air / Preview 0.6B | 完整词表中的 token ID，包含 EOS | 保持关闭；已发布模型不支持此功能 |
| Preview 0.1B | Semantic 类别 0–4095，EOS 类别 4096；其余 token 忽略 | 默认关闭，可显式开启 |

该映射仅用于 slow loss 和 accuracy。模型输入保留原始 token ID，fast codebook 目标保持不变。

先安装训练依赖：

```bash
pip install -r requirements-train.txt
```

0.1B 的 Falcon-H1 主干可通过可选的 `mamba-ssm` 和 `causal-conv1d` 包使用优化后的 CUDA
kernel。请选择与 PyTorch/CUDA 环境兼容的构建，并查看启动时是否有 kernel 回退警告。
0.6B 不需要这些包。

### 1. 创建原始数据 manifest

目标 `audio` 必填；`reference_audio` 和 `reference_text` 可选，但必须同时出现。

```json
{"id":"utt_001","text":"目标音频文本","audio":"audio/target.wav","reference_audio":"audio/reference.wav","reference_text":"参考音频文本"}
{"id":"utt_002","text":"另一条文本","audio":"audio/another.wav"}
```

### 2. 预计算 codec indices

```bash
python audio8_tts_prepare.py \
  --model "${MODEL}" \
  --input-jsonl data/train.jsonl \
  --output-jsonl prepared_data/train.jsonl \
  --batch-size 4
```

生成的 manifest 使用相对路径指向经过校验的 `[10, T]` NumPy 数组。除非传入
`--overwrite`，否则已有的有效数组会被复用。

### 3. 开始训练

单卡：

```bash
MODEL="${MODEL}" \
TRAIN_JSONL=prepared_data/train.jsonl \
NPROC_PER_NODE=1 \
bash audio8_tts_sft.sh
```

单机八卡：

```bash
MODEL="${MODEL}" \
TRAIN_JSONL=prepared_data/train.jsonl \
NPROC_PER_NODE=8 \
BATCH_SIZE=2 \
GRADIENT_ACCUMULATION_STEPS=8 \
bash audio8_tts_sft.sh
```

多机训练时，在每个节点设置 `NNODES`、`NODE_RANK`、`MASTER_ADDR` 和 `MASTER_PORT`。常用超参
和输出路径可通过 `audio8_tts_sft.sh` 中列出的环境变量覆盖，也可以在命令末尾附加 Transformers
参数。

启动脚本附带 [DeepSpeed ZeRO-2 配置](../configs/deepspeed_zero2.json)，其中的 `auto` 值跟随训练参数。
可设置 `DEEPSPEED_CONFIG=/path/to/config.json`，或在命令末尾附加
`--deepspeed /path/to/config.json` 使用其他配置文件；命令末尾的参数优先。
Gradient checkpointing 默认关闭。仅对 0.1B，可按需设置 `GRADIENT_CHECKPOINTING=true`
以减少 activation 显存占用。

默认每张 GPU 的 microbatch 包含 2 条样本，累积 8 个 microbatch 后更新一次参数，即每个
optimizer step 每张卡处理 16 条样本，8 卡共 128 条。比较耗时前应区分 microstep 和 optimizer step。

### 训练目标与导出

SFT 同时优化 slow semantic/EOS loss 和 fast codebook teacher-forcing loss。Fast loss 保留全部
10 个码本，包括作为辅助预测目标的第一个 semantic 码本，与已有训练目标保持一致。

每个 microbatch 的 loss 为 slow 平均 loss 与 fast 平均 loss 的加权和，权重分别为
`slow_loss_weight` 和 `fast_loss_weight`。梯度累积对这些 microbatch loss 取平均，不按整个累积窗口的
token 总数重新加权。Fast accuracy 衡量码本 token 的精确命中率，并不直接代表语音质量。

只训练其中一个分支时，可设置 `FREEZE_SLOW_AR=true` 或 `FREEZE_FAST_AR=true`。
导出目录仍可通过标准 `AutoModel` 和 `AutoProcessor` 接口配合 `trust_remote_code=True` 加载。
