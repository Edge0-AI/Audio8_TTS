# Audio8-TTS-Realistic-Air

[系列首页](../../README_zh.md) · [English](realistic-0.6b.md) · [Model](https://huggingface.co/Edge0/Audio8-TTS-Realistic-Air) · [Demo](https://edge0-ai.github.io/Audio8_TTS/realistic-0.6b/)

Realistic Air 在 Preview 基础上显著提升语音拟真感，并扩展到 23 种语言。保留同样的 0.6B DualAR 架构、44.1 kHz codec 和零样本音色克隆能力。

[![arXiv](../../assets/badges/arxiv.svg)](https://arxiv.org/abs/2610.14776)

Audio8 也参与了 [TTS Arena](https://tts-agi-tts-arena-v2.hf.space/)，目前收到的听众评分令人鼓舞。感谢每一位参与试听和投票的朋友。

## 支持语言

| 范围 | 语言 |
|---|---|
| Preview 已支持的 11 种 | 粤语、中文、荷兰语、英语、法语、德语、意大利语、日语、韩语、波兰语、西班牙语 |
| Realistic Air 新增的 12 种 | 阿拉伯语、芬兰语、印地语、印度尼西亚语、马来语、挪威语、葡萄牙语、俄语、瑞典语、泰语、土耳其语、越南语 |

> **说明:** 语言质量有差异，详见分语言评测。评测覆盖与正式支持清单不同。

## 使用与部署

完成 [安装说明](../inference_zh.md#安装)，在仓库根目录执行：

```bash
python audio8_tts_infer.py \
  --model Edge0/Audio8-TTS-Realistic-Air \
  --text "你好，欢迎使用 Audio8 TTS。" \
  --output outputs/realistic.wav
```

[克隆与批量推理](../inference_zh.md) · [SGLang Omni](../deployment_zh.md) · [SFT](../training_zh.md)

SGLang 使用 0.6B 配置并显式指定 Realistic Air 模型。当前暂无 Realistic Air ONNX 制品。

## 模型结构

audio8_tts 沿用了 [Fish Audio S2 Pro](https://github.com/fishaudio/fish-speech)
的 DualAR 架构思路。

| 组件 | 配置 |
|---|---|
| 主模型 | 601,159,424 参数，不包含 codec |
| Slow AR | 24 层、896 维、14 个 attention head、2 个 KV head |
| Fast AR | 4 层、896 维、14 个 attention head、2 个 KV head |
| 声学 token | 10 个 codebook，每个 codebook 包含 4,096 个条目 |
| Codec | 44.1 kHz，每个模型帧 2,048 个采样点，约 21.5 帧/秒 |
| 上下文 | 最多 2,048 个打包后的文本/音频位置 |

Slow AR 每个音频帧生成一个 semantic token；Fast AR 根据 slow hidden state 和当前帧已经生成的
codebook，继续生成该帧的十个 codec codebook。推理时 slow AR 和 fast AR 都使用静态 KV cache。
Checkpoint 内置神经音频 codec，不需要额外下载参考音频编码器或波形解码器。

## 评测

错误率使用百分数（**越低越好**）；说话人相似度 SIM 使用 **0–1 范围**（**越高越好**）。这些指标衡量可懂度与音色相似度，不能直接衡量语音拟真感。

### 基准摘要

**Audio8-TTS-Preview** 与 **Audio8-TTS-Realistic-Air**，均为 **0.6B**：

| 基准 | 覆盖 | Preview 错误率 % ↓ | Realistic Air 错误率 % ↓ | Preview SIM ↑ | Realistic Air SIM ↑ |
|---|---|---:|---:|---:|---:|
| Seed-TTS | 英语 / 中文 | 1.23 | 1.25 | 0.682 | 0.704 |
| CV3 | 8 种共有语言 | 4.80 | 4.56 | — | 0.663 |
| CV3 | 9 种核心语言 | — | 4.86 | — | 0.661 |
| MiniMax | 24 种评测语言 | — | 5.89 | — | 0.754 |

> **说明：** 数值是各语言的无权重宏平均。Preview 数据来自其[已发布 Model Card](https://huggingface.co/Edge0/Audio8-TTS-Preview-0.6b#evaluation)，SIM 从百分数换算为 0–1。两个版本分别评测。“—”表示 Preview 卡片未报告对应结果。
>
> Seed-TTS 平均英语 WER 和中文 CER，不含 hard Chinese。CV3 共有集为中、英、日、韩、德、法、西、意 8 种语言；9 语言集另含俄语。CV3 均值不含 hard 子集和 13 种扩展语言。MiniMax 平均全部 24 种评测语言，其中部分不在支持清单中。

### 跨模型参考比较

以下错误率来自技术报告所引用的来源。各项目评测流程及文本归一化不同，这些数据供参考，不构成严格同口径排名。“—”表示缺少比较数值，不表示该模型不支持。

| 模型 | 参数量（B） | Seed-TTS EN/ZH 错误率 ↓ | CV3（9）错误率 ↓ | MiniMax（24）错误率 ↓ |
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

> **来源：** Qwen 的 Seed-TTS 来自 [Qwen3-TTS 官方仓库](https://github.com/QwenLM/Qwen3-TTS)所链接的报告；其 CV3/MiniMax、Higgs Audio v3 的全部结果及 MOSS-TTS-v1.5 的 CV3/MiniMax 来自 [Boson AI 评测](https://huggingface.co/bosonai/higgs-audio-v3-tts-4b)。Fish S2 Pro 的 MiniMax 来自 [Fish Speech 官方仓库](https://github.com/fishaudio/fish-speech)所链接的报告，其 Seed-TTS/CV3 和 Higgs Audio v2 由我们重新评测。MOSS-TTS-v1.5 的 Seed-TTS 及 CosyVoice3/VoxCPM2 来自 [VoxCPM 仓库](https://github.com/OpenBMB/VoxCPM)汇总。由于说话人编码器和评测约定不同，此处不列跨项目 SIM。

> **参数口径：** Audio8 的 0.6B 不含独立 codec；Qwen 和 CosyVoice 使用发布型号；Higgs Audio v3 使用标称 **4B**。其他数值为报告中的 checkpoint 参数统计取整，VoxCPM2 不含独立 AudioVAE。各项目统计口径不同。

### Seed-TTS 详细结果

| 子集 | 指标 | Preview 错误率 % ↓ | Realistic Air 错误率 % ↓ | Preview SIM ↑ | Realistic Air SIM ↑ |
|---|---|---:|---:|---:|---:|
| English | WER | 1.506 | 1.464 | 0.632 | 0.663 |
| Chinese | CER | 0.950 | 1.029 | 0.731 | 0.745 |
| Chinese, hard | CER | 11.510 | 12.797 | 0.687 | 0.702 |

> **说明：** Preview 数值来自其[已发布的 Seed-TTS 表](https://huggingface.co/Edge0/Audio8-TTS-Preview-0.6b#seed-tts)，SIM 已换算为 0–1。

### 多语言详细结果

<details>
<summary>CV3：22 种语言和 hard 子集</summary>

| 语言 | 指标 | 错误率 % ↓ | SIM ↑ |
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

Hard Chinese CER 为 **10.665%**，hard English WER 为 **4.736%**；两个 hard 子集均不计入 9 语言摘要。22 种常规语言各有 500 条评测；中文、日语和韩语使用 CER，其余使用 WER。

</details>

<details>
<summary>MiniMax：全部 24 种评测语言</summary>

| 语言 | 指标 | 错误率 % ↓ | SIM ↑ |
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

每种语言有 100 条评测。† 标记的语言用于完整评测，不在本版正式支持清单中。指标列保留该评测集对各语言的 WER/CER 选择。粤语计入 24 语言均值。

</details>

### 相较 Preview

Realistic Air 将 Preview 的 **11 种语言**扩展到 **23 种**，新增**阿拉伯语、芬兰语、印地语、印度尼西亚语、马来语、挪威语、葡萄牙语、俄语、瑞典语、泰语、土耳其语和越南语**。

## 限制与负责任使用

- 质量随语言和评测集而变化，支持清单不代表各语言表现相同；分语言结果保留粤语及新增语言中的困难情况。
- 参考音频噪声或转写不匹配可能降低稳定性和音色相似度。参考音频、转写和目标文本共用有限上下文，长文本应拆分。
- 合成可能出现读音错误、重复、遗漏或提前结束，用于成品前请试听。
- 克隆他人音色前应获得许可，并在适当场景标明合成内容。

## 许可与致谢

代码与本版 0.6B 权重采用 [Apache License 2.0](../../LICENSE). [NOTICE](../../NOTICE).

感谢 Fish Audio 团队公开 Fish Audio S2 Pro 使用的 DualAR 架构。
