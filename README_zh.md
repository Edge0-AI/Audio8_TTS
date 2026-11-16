<div align="center">

<img src="assets/20260729-124515.jpeg" alt="Audio8" width="760">

<h1 align="center">Audio8 TTS</h1>

**轻量语音合成模型系列，支持零样本音色克隆。**

[![GitHub](assets/badges/github.svg)](https://github.com/Edge0-AI/Audio8_TTS)
[![License](assets/badges/license.svg)](LICENSE)

[English](README.md) · [中文](README_zh.md)

[0.6B family](#family-06b) · [0.1B family](#family-01b) · [llama.cpp / GGUF](#llamacpp-gguf)

</div>

> **2026-11-16 · llama.cpp / GGUF** — Realistic Air 新增原生本地推理、音色克隆和流式输出，使用统一的 F32 模型包。[运行手册](guides/llama-cpp_zh.md) · [GGUF 权重](https://huggingface.co/Edge0/Audio8-TTS-Realistic-Air/tree/main/llama-cpp)。

## 模型版本

<a id="family-06b"></a>

<details open>
<summary><strong>0.6B family</strong></summary>

<div align="center">

<img src="assets/readme-06b-zh.svg" alt="Audio8-TTS-Realistic-Air — 更真实的语音。更广的语言覆盖。依然只有 0.6B。" width="960">

[![Model](assets/badges/huggingface-realistic-06b.svg)](https://huggingface.co/Edge0/Audio8-TTS-Realistic-Air)
[![Demo](assets/badges/demo.svg)](https://edge0-ai.github.io/Audio8_TTS/realistic-0.6b/)
[![arXiv](assets/badges/arxiv.svg)](https://arxiv.org/abs/2610.14776)

</div>

**Audio8-TTS-Realistic-Air** 在 Preview 基础上显著提升语音拟真感，保留相同的 0.6B 架构和零样本音色克隆能力。支持 **23 种语言**，相较 Preview 新增 **12 种**。

Audio8 也参与了 [TTS Arena](https://tts-agi-tts-arena-v2.hf.space/)，目前收到的听众评分令人鼓舞。感谢每一位参与试听和投票的朋友。

| 版本 | 定位与语言 | 模型 | 试听 | 版本指南 |
|---|---|---|---|---|
| **Realistic Air** | 拟真感与韵律 · 23 种语言 | [HF](https://huggingface.co/Edge0/Audio8-TTS-Realistic-Air) | [Demo](https://edge0-ai.github.io/Audio8_TTS/realistic-0.6b/) | [说明](guides/models/realistic-0.6b_zh.md) |

**ONNX：** Realistic Air 目前暂无 ONNX 制品。

**原生部署：** [llama.cpp / GGUF 运行手册](guides/llama-cpp_zh.md) · [统一权重目录](https://huggingface.co/Edge0/Audio8-TTS-Realistic-Air/tree/main/llama-cpp)。

<details>
<summary><strong>0.6B 详情：语言支持、快速开始与评测</strong></summary>

#### Realistic Air 的语言支持

| 范围 | 语言 |
|---|---|
| Preview 已支持的 11 种 | 粤语、中文、荷兰语、英语、法语、德语、意大利语、日语、韩语、波兰语、西班牙语 |
| Realistic Air 新增的 12 种 | 阿拉伯语、芬兰语、印地语、印度尼西亚语、马来语、挪威语、葡萄牙语、俄语、瑞典语、泰语、土耳其语、越南语 |

> **说明：** 语言质量存在差异；评测覆盖和正式支持清单并不相同。 [分语言评测](guides/models/realistic-0.6b_zh.md#多语言详细结果)。

#### Realistic Air 快速开始

推荐 Python 3.10+ 和 CUDA GPU；在仓库根目录执行。模型 ID 显式指定，因此不会误用脚本保留的 Preview 默认路径。

```bash
git clone https://github.com/Edge0-AI/Audio8_TTS.git
cd Audio8_TTS
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python audio8_tts_infer.py \
  --model Edge0/Audio8-TTS-Realistic-Air \
  --text "你好，欢迎使用 Audio8 TTS。" \
  --output outputs/realistic.wav
```

音色克隆时追加 `--reference-audio reference.wav --reference-text "参考录音的准确文本。"`。

[安装、克隆与批量推理](guides/inference_zh.md) · [SFT 训练](guides/training_zh.md)

#### 0.6B 评测摘要

**Audio8-TTS-Preview** 与 **Audio8-TTS-Realistic-Air**，均为 **0.6B**：

| 基准 | 覆盖 | Preview 错误率 % ↓ | Realistic Air 错误率 % ↓ | Preview SIM ↑ | Realistic Air SIM ↑ |
|---|---|---:|---:|---:|---:|
| Seed-TTS | 英语 / 中文 | 1.23 | 1.25 | 0.682 | 0.704 |
| CV3 | 8 种共有语言 | 4.80 | 4.56 | — | 0.663 |
| CV3 | 9 种核心语言 | — | 4.86 | — | 0.661 |
| MiniMax | 24 种评测语言 | — | 5.89 | — | 0.754 |

错误率为百分数，越低越好；SIM 使用 0–1 范围，越高越好。两者不能直接衡量语音拟真感。

> **说明：** 数值为各语言的无权重宏平均。Preview 数据来自其[已发布 Model Card](https://huggingface.co/Edge0/Audio8-TTS-Preview-0.6b#evaluation)，SIM 由百分数换算为 0–1。两个版本分别评测；“—”表示 Preview 卡片未报告对应结果。Seed-TTS 平均英语 WER 与中文 CER，不含 hard Chinese；CV3 共有集为中、英、日、韩、德、法、西、意 8 种语言，9 语言集另含俄语，不含 hard 子集及 13 种扩展语言。MiniMax 平均全部 24 种评测语言，其中部分不在正式支持清单内。

[完整 Realistic Air 评测与比较说明](guides/models/realistic-0.6b_zh.md#评测) · [Preview 原始评测](guides/models/preview-0.6b_zh.md#评测结果)

</details>

<details>
<summary><strong>上一版本 · Preview 0.6B</strong></summary>

Realistic Air 在 Preview 基础上继续改进。Preview 用户仍可使用原版模型、**11 种语言**的支持说明、原评测与固定试听页。

| 版本 | 模型 | 试听 | 版本指南 | 部署 |
|---|---|---|---|---|
| Preview 0.6B | [HF](https://huggingface.co/Edge0/Audio8-TTS-Preview-0.6b) | [Demo](https://edge0-ai.github.io/Audio8_TTS/preview-0.6b/) | [说明](guides/models/preview-0.6b_zh.md) | [ONNX INT4](onnx_runtime/README_zh.md) |

</details>

</details>

---

<a id="family-01b"></a>

<details open>
<summary><strong>0.1B family</strong></summary>

<div align="center">

<img src="assets/readme-01b-zh.svg" alt="Audio8-TTS-0.1B — 零样本音色克隆 TTS，还能做到多小？" width="960">

[![Model 0.1B](assets/badges/huggingface-preview-01b.svg)](https://huggingface.co/Edge0/Audio8-TTS-Preview-0.1b)
[![ONNX INT8](assets/badges/onnx-01b.svg)](https://huggingface.co/Edge0/audio8-TTS-0.1B-ONNX-INT8)
[![Demo 0.1B](assets/badges/demo-01b.svg)](https://edge0-ai.github.io/Audio8_TTS/0.1B/)

</div>

**Audio8-TTS-0.1B**：支持零样本音色克隆的小巧、便携语音合成模型。

面向更小的部署体积，**以中文和英语为主要支持语言**。专用 ONNX INT8 运行时支持 CPU 推理、流式输出及本地 Web/HTTP 服务。

| 版本 | 定位与语言 | 模型 | 试听 | 版本指南 |
|---|---|---|---|---|
| Preview 0.1B | 小体积混合架构 · 以中英为主 | [HF](https://huggingface.co/Edge0/Audio8-TTS-Preview-0.1b) | [Demo](https://edge0-ai.github.io/Audio8_TTS/0.1B/) | [说明](guides/models/preview-0.1b_zh.md) |

[0.1B 快速开始](guides/models/preview-0.1b_zh.md#推理) · [CPU / ONNX 运行时](onnx_runtime_0_1b_int8/README_zh.md) · [0.1B 部署](guides/models/preview-0.1b_zh.md#部署) · [模型许可](guides/models/preview-0.1b_zh.md#许可)

</details>

---

## 共用工具

[安装与推理](guides/inference_zh.md) · [SFT 训练](guides/training_zh.md)

共用工具通过显式模型 ID 选择版本；请使用对应版本的快速开始和部署说明。

<a id="llamacpp-gguf"></a>

## llama.cpp / GGUF

Realistic Air 的原生 C++ 路线面向本地应用、桌面与嵌入式集成，无需 Python、PyTorch 或 ONNX Runtime 即可推理。支持文本转语音、参考音频克隆、WAV 输出和 HTTP/流式接口，使用下方提供的 Audio8 适配运行时。

| 入口 | 内容 |
|---|---|
| [独立运行手册](guides/llama-cpp_zh.md) | 下载、构建、语音生成、HTTP、流式与排错 |
| [实现与转换器](llama_cpp/) | 固定上游补丁、源码校验和 F32 导出入口 |
| [HF 权重目录](https://huggingface.co/Edge0/Audio8-TTS-Realistic-Air/tree/main/llama-cpp) | 三平台共用一份模型包；四个权重文件约 3.76 GB |

默认使用 F32 权重。需要 GPU 动态 batching 的服务可继续使用下方 SGLang Omni 路线。

<blockquote>
<sub><strong>Note：</strong>Mac 建议使用 CPU，Metal 暂为实验选项；Windows 构建说明尚未经 Windows 实机测试。</sub>
</blockquote>

## SGLang Omni Serving

SGLang Omni 提供 paged attention、动态 batching 和兼容 OpenAI 的语音 API。0.6B 系列与 0.1B 混合架构模型使用各自的配置；部署指南保留现有性能数据及对应型号、硬件与测试条件。

[部署矩阵、安装与服务配置](guides/deployment_zh.md) · [API、流式输出及排错](guides/deployment_zh.md#sglang-omni-服务部署)

## 许可与致谢

仓库代码和两个 0.6B 版本采用 [Apache License 2.0](LICENSE)。

0.1B 基础权重及其 ONNX INT8 导出均采用 [Audio8 Community License v1.0](https://huggingface.co/Edge0/Audio8-TTS-Preview-0.1b/blob/main/LICENSE)。在遵守许可证条件的前提下，实体年营收（含母公司、子公司及关联公司）低于 200 万美元时可免版税商用；达到或超过该门槛时，须另行取得书面商业许可。详情见 [0.1B 许可说明](guides/models/preview-0.1b_zh.md#许可)和 [ONNX 模型许可证](https://huggingface.co/Edge0/audio8-TTS-0.1B-ONNX-INT8/blob/main/LICENSE)。

归属说明见 [NOTICE](NOTICE)。感谢 Fish Audio 团队公开 Fish Audio S2 Pro 使用的 DualAR 架构。
