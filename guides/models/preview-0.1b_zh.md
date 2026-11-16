# Audio8-TTS-Preview-0.1B

**零样本音色克隆 TTS，还能做到多小？**

[系列首页](../../README_zh.md) · [English](preview-0.1b.md) · [Model](https://huggingface.co/Edge0/Audio8-TTS-Preview-0.1b) · [Demo](https://edge0-ai.github.io/Audio8_TTS/0.1B/)

面向小体积部署的零样本音色克隆型号，采用 Falcon-H1 混合 slow AR（Mamba 2 SSM + attention），与两个 0.6B 型号分别维护。

## 语言与规模

- **主要语言：中文、英语。**
- 实验 / 多语言评测：德语、西班牙语、法语、意大利语、日语、韩语。
- 发布名为 0.1B；当前基础模型卡标注主模型约 170M 参数，不含独立 codec decoder。

完整架构及 Seed-TTS/CV3 数据见 [0.1B Model Card](https://huggingface.co/Edge0/Audio8-TTS-Preview-0.1b)。Realistic Air 的 23 语言和 0.6B 评测不适用于本版。

## 推理

推荐 Python 3.11+；先按 [安装指南](../inference_zh.md#安装)安装依赖，在仓库根目录运行：

```bash
python audio8_tts_infer.py \
  --model Edge0/Audio8-TTS-Preview-0.1b \
  --text "你好，这是一条语音合成测试。" \
  --reference-audio reference.wav \
  --reference-text "参考录音的准确文本。" \
  --output outputs/preview-0.1b.wav
```

## 部署

- **SGLang Omni:** 选择 audio8_tts_0_1b.yaml 和 audio8/tts-0.1b；适配器自动使用独立混合 cache，关闭 CUDA Graph。 [完整指南](../deployment_zh.md).
- **ONNX INT8:** [下载](https://huggingface.co/Edge0/audio8-TTS-0.1B-ONNX-INT8) · [专用运行时](../../onnx_runtime_0_1b_int8/README_zh.md). 包含命令行、网页/HTTP 服务、流式 PCM、音色注册和 Windows PowerShell 入口；不能使用 0.6B 的 INT4 运行时。

## 许可

仓库代码（包括 ONNX 推理运行时）采用 [Apache License 2.0](../../LICENSE)。

0.1B 基础权重及其 ONNX INT8 导出均采用 **Audio8 Community License v1.0**。ONNX 导出未单独改为 Apache 2.0 授权。完整条款见[基础模型许可证](https://huggingface.co/Edge0/Audio8-TTS-Preview-0.1b/blob/main/LICENSE)或 [ONNX 导出附带的许可证](https://huggingface.co/Edge0/audio8-TTS-0.1B-ONNX-INT8/blob/main/LICENSE)。

- 在遵守许可证条件的前提下，非商业使用免费。
- 在遵守许可证条件的前提下，实体年营收**低于 200 万美元**时可免版税商用。
- 年营收**达到或超过 200 万美元**时，须在商业使用前另行取得书面商业许可。

年营收指实体最近一个完整财年的合并年度总营收，包含母公司、子公司及关联公司。模型再分发须保留许可证及署名。许可证以英文文本为准。归属说明见 [NOTICE](../../NOTICE)。
