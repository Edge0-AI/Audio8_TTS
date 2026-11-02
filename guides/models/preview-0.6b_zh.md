# Audio8-TTS-Preview-0.6B

[系列首页](../../README_zh.md) · [English](preview-0.6b.md) · [Model](https://huggingface.co/Edge0/Audio8-TTS-Preview-0.6b) · [Demo](https://edge0-ai.github.io/Audio8_TTS/preview-0.6b/)

本页保留原 Preview 0.6B 的语言、架构和评测。新版 Realistic Air 的 23 种语言与评测仅适用于新版；Preview 的使用方式和下载入口继续保留。

## 快速开始

完成 [安装说明](../inference_zh.md#安装)，然后在仓库根目录执行：

```bash
python audio8_tts_infer.py \
  --model Edge0/Audio8-TTS-Preview-0.6b \
  --text "欢迎使用 Audio8 TTS Preview。" \
  --output outputs/preview.wav
```

后续克隆、批量推理和训练继续显式使用 `Edge0/Audio8-TTS-Preview-0.6b`.

[推理](../inference_zh.md) · [SGLang Omni](../deployment_zh.md) · [ONNX INT4](../../onnx_runtime/README_zh.md) · [SFT](../training_zh.md)

## 支持语言

Preview 模型当前表现较好、推荐使用的语言如下：

| Language | 语言 |
|---|---|
| Cantonese | 粤语 |
| Chinese | 中文 |
| Dutch | 荷兰语 |
| English | 英语 |
| French | 法语 |
| German | 德语 |
| Italian | 意大利语 |
| Japanese | 日语 |
| Korean | 韩语 |
| Polish | 波兰语 |
| Spanish | 西班牙语 |

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

## 评测结果

Audio8 TTS Preview 仅有 **0.6B 参数**，是本次对比中规模最小的模型。尽管参数量仅为其他模型的
一小部分，它在以下基准测试中依然达到业界领先 TTS 模型的第一梯队水平。其中，Audio8 TTS
Preview 在 Seed-TTS 上取得了最低的英文 WER 和有竞争力的中文 CER，并在 CV3 多语言评测中
保持了具有竞争力的整体表现。

WER/CER 越低越好，SIM 越高越好。Seed-TTS 的相似度统一显示为百分数。

### Seed-TTS

| 模型 | 参数量 | EN WER / SIM | ZH CER / SIM | Hard ZH CER / SIM |
|---|---:|---:|---:|---:|
| **Audio8 TTS Preview** | **0.6B** | **1.506** / 63.2 | 0.950 / 73.1 | 11.510 / 68.7 |
| Fish S2 Pro | 4.6B | 1.607 / 64.6 | 1.038 / 73.8 | 10.149 / 70.1 |
| Higgs Audio v2 | 4.7B | 1.524 / 66.4 | **0.806** / 72.1 | 10.622 / 69.3 |
| CosyVoice3-1.5B | 1.5B | 2.22 / 72.0 | 1.12 / 78.1 | **5.83** / **75.8** |
| MOSS-TTS | 8.5B | 1.85 / 73.4 | 1.20 / 78.8 | - |
| VoxCPM2 | 2.3B | 1.84 / **75.3** | 0.97 / **79.5** | 8.13 / 75.3 |

![Seed-TTS WER 和 CER 对比](../../assets/evaluation/seed_tts_error_rates.png)

### CV3 多语言错误率

| 模型 | 参数量 | zh | en | hard-zh | hard-en | ja | ko | de | es | fr | it | ru |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Audio8 TTS Preview** | **0.6B** | **3.205** | **3.128** | 10.535 | 5.997 | 7.205 | 4.223 | 3.447 | 3.641 | 8.790 | 4.790 | - |
| Fish S2 Pro | 4.6B | 3.600 | 3.493 | 10.588 | 7.349 | 5.139 | **4.111** | 3.605 | 2.972 | **8.600** | 4.229 | **4.702** |
| Higgs Audio v2 | 4.7B | 3.378 | 3.404 | 10.424 | **5.754** | **4.742** | 4.260 | **3.300** | **2.929** | 9.425 | **3.555** | 5.423 |
| CosyVoice3-1.5B | 1.5B | 3.91 | 4.99 | 9.77 | 10.55 | 7.57 | 5.69 | 6.43 | 4.47 | 11.8 | 10.5 | 6.64 |
| VoxCPM2 | 2.3B | 3.65 | 5.00 | **8.55** | 8.48 | 5.96 | 5.69 | 4.77 | 3.80 | 9.85 | 4.25 | 5.21 |

![CV3 多语言 WER 和 CER 对比](../../assets/evaluation/cv3_error_rates.png)

参数量直接根据已发布的权重张量统计。MOSS-TTS 包含 8,489,841,664 个参数；VoxCPM2 主模型
包含 2,290,004,544 个参数，单独的 AudioVAE 不计入本次参数量对比。

Fish S2 Pro 因官方评测使用自身 normalizer 而重新评测。Higgs Audio v2 因未公布具体数值而自行
评测。其他基线均采用 [VoxCPM 官方仓库](https://github.com/OpenBMB/VoxCPM)汇总的各项目官方值。

不同 normalizer 和评测器下的跨项目数值只能作为参考，不能视为严格同口径排名；评测覆盖也不
会将 Preview 的正式支持范围扩展到前述 11 种语言之外。

## 限制与负责任使用

- 当前是 Preview 模型，多语言和中文方言覆盖仍然有限。
- 过长、噪声较大或转写不准确的参考音频可能降低稳定性和音色相似度。
- 合成语音可能被用于冒充或传播虚假信息。克隆他人声音前应获得许可，并在适当场景明确标注合成内容。
- 部署前应针对具体业务完成准确性、安全性和合规测试。

## 许可

代码与该 0.6B 权重采用 [Apache License 2.0](../../LICENSE). [NOTICE](../../NOTICE).
