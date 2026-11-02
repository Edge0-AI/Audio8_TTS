# 部署指南

[系列首页](../README_zh.md) · [English](deployment.md) · [安装与推理](inference_zh.md)

| 版本 | Transformers / CLI | SGLang Omni | ONNX |
|---|---|---|---|
| Realistic Air | 支持 | 0.6B 配置 | 暂无制品 |
| Preview 0.6B | 支持 | 0.6B 配置 | INT4，onnx_runtime/ |
| Preview 0.1B | 支持 | 0.1B hybrid 配置 | INT8，onnx_runtime_0_1b_int8/ |

Realistic Air 沿用 0.6B 配置，只需显式选择新版模型 ID 或本地目录。ONNX 导出属于表中列出的各自版本，不能将 Preview ONNX 当成 Realistic Air 权重。

## SGLang Omni 服务部署

[`sglang_omni/`](../sglang_omni/) 中的适配器提供兼容 OpenAI API 的推理服务，包含 SGLang
paged attention、动态 batching、Fast AR 固定 KV cache、参考音频编码和 waveform 解码。
它以独立的 `audio8_tts` 模型插件安装，不会覆盖 SGLang Omni 核心文件。

### 兼容版本

适配器使用了 SGLang Omni 的内部接口，因此部署时应固定到以下已验证版本，不要直接使用最新
`main` 分支。

| 依赖 | 已验证版本 |
|---|---|
| SGLang Omni | `68a572348837f7b004857b4b07993c20ade4c017`（`0.1.0`） |
| SGLang | `0.5.8` |
| PyTorch | `2.9.1+cu128` |
| Transformers | `4.57.1` |
| 精度 | BF16 |

### 性能

现有 SGLang 性能数据与原测试条件如下；Realistic Air 与 Preview 0.6B 架构和服务路径相同，继续适用。此处不将其写作新版重新测量的数据。0.1B 的 eager 混合路径见本页独立小节。

单流 warm latency 在单张 NVIDIA H20 上测试，使用 BF16、CUDA Graph、greedy decoding，
并生成 128 帧。输出 WAV 时长为 5.85-5.94 秒，不包含冷启动和编译时间。RTF 越低越好。

| SGLang Omni 适配器 | Warm p50 latency | RTF |
|---|---:|---:|
| 当前实现 | **0.691 s** | **0.116** |

配置、实现细节和验证结果请参阅
[SGLang Omni 实现与评测报告](../sglang_omni/OPTIMIZATION_REPORT.md)。

### 安装

在 Audio8 TTS 仓库根目录执行以下命令。示例使用 Python 3.12 和
[`uv`](https://docs.astral.sh/uv/)。

```bash
export SGLANG_OMNI_ROOT=/opt/sglang-omni
export MODEL_ID=Edge0/Audio8-TTS-Realistic-Air
# Preview 0.6B: export MODEL_ID=Edge0/Audio8-TTS-Preview-0.6b
export MODEL="./model/${MODEL_ID##*/}"

git clone https://github.com/sgl-project/sglang-omni.git "${SGLANG_OMNI_ROOT}"
git -C "${SGLANG_OMNI_ROOT}" checkout 68a572348837f7b004857b4b07993c20ade4c017

uv venv .venv-sglang --python 3.12
source .venv-sglang/bin/activate
uv pip install -v -e "${SGLANG_OMNI_ROOT}"

hf download "${MODEL_ID}" --local-dir "${MODEL}"
./sglang_omni/scripts/install_adapter.sh "${SGLANG_OMNI_ROOT}"
python3 ./sglang_omni/scripts/verify_install.py --model-path "${MODEL}"
```

如果 SGLang Omni 已通过 wheel 或 site-packages 安装，可以定位其包目录后安装适配器：

```bash
SGLANG_OMNI_PACKAGE="$(python3 -c 'import importlib.util, pathlib; s=importlib.util.find_spec("sglang_omni"); assert s and s.origin; print(pathlib.Path(s.origin).parent)')"
./sglang_omni/scripts/install_adapter.sh "${SGLANG_OMNI_PACKAGE}"
```

### 启动服务

```bash
CUDA_VISIBLE_DEVICES=0 \
SGLANG_OMNI_ROOT="${SGLANG_OMNI_ROOT}" \
MODEL="${MODEL}" \
AUDIO8_TTS_ENABLE_TORCH_COMPILE=1 \
HOST=0.0.0.0 \
PORT=8010 \
./sglang_omni/scripts/run_server.sh
```

默认的 `fa3` attention backend 适用于 H20、H100 等 Hopper GPU。RTX 5090 等消费级
Blackwell GPU 的计算能力为 `(12, 0)`，没有对应的 FA3 kernel image，适配器会自动识别
并为 SGLang Slow AR 路径选择 FlashInfer；此时短序列固定 KV cache 的 Fast head 会使用
PyTorch SDPA。无需额外配置。

在任意 GPU 上显式设置该环境变量仍会覆盖自动检测结果：

```bash
AUDIO8_TTS_ATTENTION_BACKEND=flashinfer \
CUDA_VISIBLE_DEVICES=0 \
SGLANG_OMNI_ROOT="${SGLANG_OMNI_ROOT}" \
MODEL="${MODEL}" \
./sglang_omni/scripts/run_server.sh
```

默认配置使用模型名 `audio8/tts-0.6b`、BF16、单卡、`0.2` 静态显存比例和最多 32 个并发
请求。主要运行参数包括 `MODEL_NAME`、`AUDIO8_TTS_MEM_FRACTION_STATIC`、
`AUDIO8_TTS_MAX_RUNNING_REQUESTS`、`AUDIO8_TTS_CHUNKED_PREFILL_SIZE` 和
`AUDIO8_TTS_DISABLE_CUDA_GRAPH`。开启 Torch compile 后，适配器沿用 SGLang 原生的 batch
策略；只有需要明确限制 compile 上限时才设置 `AUDIO8_TTS_TORCH_COMPILE_MAX_BS`。
`AUDIO8_TTS_ATTENTION_BACKEND` 默认为 `fa3`；在没有 FA3 kernel image 的 GPU（如消费级
Blackwell）上默认为 `flashinfer`，显式设置可覆盖。如果运行依赖安装在单独的
site-packages 目录中，请设置
`SGLANG_OMNI_SITE_PACKAGES`。

### 常见问题

- 如果 `sgl_kernel` 导入失败，请安装系统中提供 `libnuma` 的软件包，例如 `numactl` 或
  `libnuma1`。
- CUDA toolkit 的 `bin` 目录需要加入 `PATH`。如果 `deep_gemm` JIT 编译时找不到
  `nvcc`，还需要将 `CUDA_PATH` 指向 CUDA toolkit 根目录。
- Transformers 应保持在支持的 4.x 范围（`>=4.57.0,<5`）。Transformers 5.x 可能使该
  custom-code 模型生成无效的全零 codes。

### 调用 API

无参考音频生成：

```bash
curl -sS --fail-with-body \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "audio8/tts-0.6b",
    "input": "你好，这是 Audio8 TTS 服务测试。",
    "response_format": "wav",
    "max_new_tokens": 256,
    "temperature": 0.8,
    "top_p": 0.95,
    "top_k": 50
  }' \
  http://127.0.0.1:8010/v1/audio/speech \
  -o audio8.wav
```

使用一个参考音色生成：

```bash
curl -sS --fail-with-body \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "audio8/tts-0.6b",
    "input": "这句话使用参考音色生成。",
    "response_format": "wav",
    "temperature": 0.8,
    "top_p": 0.95,
    "top_k": 50,
    "references": [{
      "audio_path": "/data/reference.wav",
      "text": "参考录音对应的准确文本。"
    }]
  }' \
  http://127.0.0.1:8010/v1/audio/speech \
  -o audio8_clone.wav
```

参考音频路径必须在服务运行环境中可见。当前适配器支持 TP=1 和每个请求一个 reference。
设置 `"stream": true` 可在生成过程中接收 SSE 音频分块。使用
`"response_format": "pcm"` 开销最低，每个事件的 `audio.data` 包含 Base64 编码音频。
流式输出默认每 12 个 codec frames 生成一块，使用 128 帧 decoder context 和 1 帧边界
guard。可通过 `AUDIO8_TTS_STREAM_CHUNK_FRAMES`、
`AUDIO8_TTS_STREAM_CONTEXT_FRAMES` 和 `AUDIO8_TTS_STREAM_GUARD_FRAMES` 调整。

流式输出是服务端可选项：启动服务时设置 `AUDIO8_TTS_STREAM_ENABLED=1` 才会启用 SSE
流式；默认关闭，请求会在生成完成后一次性返回完整音频（请求中的 `"stream": true`
此时会被忽略）。默认非流式以获得更高的吞吐和稳定的显存占用。
`response_format` 为 `codes`/`codec`/`npy` 时始终非流式，直接返回 codec codes。

运行以下 smoke test 可以验证部署：

```bash
BASE_URL=http://127.0.0.1:8010 ./sglang_omni/scripts/smoke_test.sh
python3 ./sglang_omni/scripts/stream_smoke_test.py \
  --base-url http://127.0.0.1:8010 \
  --output /tmp/audio8_stream.wav
```

构建镜像时，请在安装 SGLang Omni 包及其 Python 依赖后追加
[`sglang_omni/Dockerfile.snippet`](../sglang_omni/Dockerfile.snippet)。

### Audio8-TTS-0.1B（Falcon-H1 混合慢速主干）

先完成前述适配器安装，再选择下面的模型、配置和 API 名称。请求中的 model 字段应使用 audio8/tts-0.1b。

`Audio8-TTS-Preview-0.1b` 将纯注意力的慢速 AR 主干替换为 Falcon-H1 混合结构
（Mamba 2 SSM + 注意力）。适配器会自动从 `config.json` 检测（`slow_backbone:
falcon_h1` 或存在 `mamba_d_ssm` 字段）并切换到 eager 混合路径：慢速主干为每个
请求维护一个 `FalconHybridMambaAttentionDynamicCache`，而快速码本 AR、语义采样
与声码器与 0.6B 路径完全共用，0.6B 路径不受影响。

```bash
export MODEL=./model/Audio8-TTS-Preview-0.1b
hf download Edge0/Audio8-TTS-Preview-0.1b --local-dir "${MODEL}"
export CONFIG=./sglang_omni/configs/audio8_tts_0_1b.yaml
export MODEL_NAME=audio8/tts-0.1b

CUDA_VISIBLE_DEVICES=0 \
SGLANG_OMNI_ROOT="${SGLANG_OMNI_ROOT}" \
MODEL="${MODEL}" \
CONFIG="${CONFIG}" \
MODEL_NAME="${MODEL_NAME}" \
./sglang_omni/scripts/run_server.sh
```

由于 Mamba 主干自行维护混合缓存、不占用 SGLang KV 页，适配器会为该模型关闭
CUDA Graph 并限制静态显存比例。慢速主干在 prefill 与增量 decode 上与
Transformers 的 Falcon-H1 实现逐位一致。

## Preview 0.6B: CPU ONNX INT4

[`onnx_runtime/`](../onnx_runtime/) 提供独立的 CPU 部署方案：Slow/Fast AR 使用
weight-only INT4，activation 和 KV cache 使用 FP16，codec 使用 FP16。它包含
命令行推理、本地网页与 HTTP 服务、流式 PCM 输出和参考音频音色注册，运行时不依赖
PyTorch 或 Transformers。

在 Apple M2 测试环境中，在线模型 session 约占 1 GiB 内存。注册音色前会先释放
在线 session，再单独加载 codec encoder，从而控制峰值内存。

从
[Audio8-TTS-Preview-0.6B-ONNX-INT4](https://huggingface.co/Edge0/Audio8-TTS-Preview-0.6B-ONNX-INT4)
下载模型，并参阅 [ONNX Runtime 中文指南](../onnx_runtime/README_zh.md)。

## Preview 0.1B: CPU ONNX INT8

0.1B 使用独立的 Falcon-H1 INT8 图及运行时；与 0.6B INT4 图不兼容。提供 CLI、网页/HTTP 服务、流式 PCM 和音色注册，支持 Linux/macOS 以及 Windows PowerShell 入口。

[Model](https://huggingface.co/Edge0/audio8-TTS-0.1B-ONNX-INT8) · [运行时指南](../onnx_runtime_0_1b_int8/README_zh.md)

模型权重及 ONNX 制品的许可请以各下载仓库为准。
