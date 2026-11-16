<div align="center">

<img src="../assets/readme-06b-zh.svg" alt="Audio8-TTS-Realistic-Air" width="960">

<h1 align="center">Realistic Air · llama.cpp</h1>

**原生本地推理、音色克隆与流式音频。**

[所有版本](../README_zh.md) · [English](llama-cpp.md) · [实现代码](../llama_cpp/) · [GGUF 权重](https://huggingface.co/Edge0/Audio8-TTS-Realistic-Air/tree/main/llama-cpp) · [部署矩阵](deployment_zh.md)

[简介](#简介) · [下载权重](#下载权重) · [构建运行时](#构建运行时) · [生成语音](#生成语音) · [HTTP 与流式输出](#http-与流式输出) · [重新导出](#重新导出权重)

</div>

---

## 简介

使用原生运行时在本地生成 **Audio8-TTS-Realistic-Air** 语音，支持参考音频
克隆、WAV 输出、命令行、HTTP 和增量流式音频。文本处理、DualAR 和 codec
均在原生代码中执行，推理不需要 Python、PyTorch 或 ONNX Runtime。

本手册使用固定版本 llama.cpp 与 Audio8 适配补丁，配合统一的 F32 模型包。

## 下载权重

**三个系统共用完全相同的一份 F32 模型包**，统一放在现有 HF 仓库的独立目录：

```text
Edge0/Audio8-TTS-Realistic-Air/
├── ...                         # 原有 Transformers 权重、配置与代码
└── llama-cpp/
    ├── README.md
    ├── LICENSE / NOTICE
    ├── SHA256SUMS
    ├── audio8-runtime.json
    ├── conversion-manifest.json
    └── models/
        ├── slow-f32.gguf
        ├── fast-f32.gguf
        ├── codebook_embeddings.f32
        └── audio8-realistic-codec-f32.gguf
```

四个权重文件合计 **3,762,945,056 bytes，约 3.76 GB / 3.50 GiB**，另有少量
元数据。必须保留完整目录和四个文件；sidecar 是 codebook embedding，
不是供用户选择的另一种模型。

在 Audio8 TTS 仓库根目录运行：

```bash
hf download Edge0/Audio8-TTS-Realistic-Air \
  --include "llama-cpp/**" --local-dir model/Audio8-TTS-Realistic-Air

python3 -S llama_cpp/converter/convert_audio8_realistic.py \
  --verify-only --output-dir model/Audio8-TTS-Realistic-Air/llama-cpp
```

校验器只需要 Python 3.10+ 标准库，会核对完整文件清单与 SHA。
实际推理不需要 Python、PyTorch 或 ONNX Runtime。
`--audio8-model-dir` 应指向含 `audio8-runtime.json` 的 `llama-cpp/`，
不要指向里面的 `models/` 或上层 Transformers 目录。

需要固定部署版本时，为下载命令补充 `--revision <已发布模型提交>`，并保留
模型提交、`source-lock.json` 和运行时二进制 SHA。

只使用 Transformers / SGLang 时，整仓下载加 `--exclude "llama-cpp/**"`，
避免额外下载这 3.76 GB。`AutoModel` 仍使用根目录 checkpoint。
现有 runtime 元数据保留旧的内部 `Realistic-0.6b` 标识以维持兼容，
它仍然是同一版 Realistic Air，不代表不同平台使用不同模型。

## 构建运行时

准备 Git、Python 3.10+、CMake（已用 3.31.6）、Ninja 和 C++17 编译器。
Python 仅用于准备与校验源码，安装后的工具不需要 Python。
公共配置使用可移植 CPU 设置，调优时可按目标 CPU 开启可选 SIMD 和 OpenMP。

以下命令从 Audio8 TTS 仓库根目录执行，使用**单独的干净 checkout**：

```bash
git clone https://github.com/ggml-org/llama.cpp.git vendor/llama.cpp
git -C vendor/llama.cpp checkout d854d98bae598388ecea1ed84396587e5edc326d
python3 llama_cpp/prepare.py --source vendor/llama.cpp
python3 llama_cpp/prepare.py --source vendor/llama.cpp --verify-only
```

准备脚本不自行下载；会拒绝错误版本或已有改动，校验补丁 SHA，应用后核对
补丁文件。不重复应用补丁，已准备目录用 `--verify-only`。
升级 llama.cpp 时，也需要更新 Audio8 补丁。

### Linux CPU

```bash
cmake -S vendor/llama.cpp -B build/audio8-cpu -G Ninja \
  -C llama_cpp/cmake/common.cmake \
  '-DCMAKE_INSTALL_RPATH=$ORIGIN/../lib'
cmake --build build/audio8-cpu --parallel 4 --target llama-tts llama-server
cmake --install build/audio8-cpu --prefix "$PWD/stage/audio8-cpu" --component Audio8Runtime
```

### Linux CUDA

下面使用 H20（SM90）及 CUDA 12.6；其他显卡相应调整架构和 toolkit 路径。

```bash
cmake -S vendor/llama.cpp -B build/audio8-cuda -G Ninja \
  -C llama_cpp/cmake/common.cmake \
  -DGGML_CUDA=ON -DAUDIO8_CODEC_CUDA=ON \
  -DGGML_CUDA_FORCE_CUBLAS=ON \
  -DCMAKE_CUDA_COMPILER=/usr/local/cuda-12.6/bin/nvcc \
  -DCUDAToolkit_ROOT=/usr/local/cuda-12.6 -DCMAKE_CUDA_ARCHITECTURES=90 \
  '-DCMAKE_INSTALL_RPATH=$ORIGIN/../lib'
cmake --build build/audio8-cuda --parallel 4 --target llama-tts llama-server
cmake --install build/audio8-cuda --prefix "$PWD/stage/audio8-cuda" --component Audio8Runtime
```

保留 force-cuBLAS 和运行时默认精度设置。CUDA codec 组合使用 GPU 与 CPU 运算。
NVIDIA driver、CUDA/cuBLAS 是外部依赖。

### macOS Apple Silicon

需要 Xcode Command Line Tools。运行时使用 CPU codec，安装 BLAS 并内嵌
Metal 资源。使用 `--gpu-layers 0` 运行 CPU 生成。

```bash
cmake -S vendor/llama.cpp -B build/audio8-macos -G Ninja \
  -C llama_cpp/cmake/common.cmake \
  -DCMAKE_OSX_ARCHITECTURES=arm64 \
  -DGGML_METAL=ON -DGGML_METAL_EMBED_LIBRARY=ON -DGGML_ACCELERATE=ON \
  '-DCMAKE_INSTALL_RPATH=@loader_path/../lib'
cmake --build build/audio8-macos --parallel 2 --target llama-tts llama-server
cmake --install build/audio8-macos --prefix "$PWD/stage/audio8-macos" --component Audio8Runtime
```

<blockquote>
<sub><strong>Note：</strong>建议使用 CPU；Metal（<code>--gpu-layers 99</code>）暂为实验选项。Mac server 和 Intel Mac 构建尚未经实机测试。</sub>
</blockquote>

### Windows x64

使用 x64 Visual Studio Developer PowerShell，安装 C++17 工具、CMake、Ninja、
Git 与 Python。

<blockquote>
<sub><strong>Note：</strong>以下 Windows/MSVC 构建说明尚未经 Windows 实机测试。</sub>
</blockquote>

```powershell
cmake -S vendor/llama.cpp -B build/audio8-windows -G Ninja `
  -C llama_cpp/cmake/common.cmake
cmake --build build/audio8-windows --parallel 4 --target llama-tts llama-server
cmake --install build/audio8-windows --prefix "$PWD/stage/audio8-windows" --component Audio8Runtime
```

保留安装后的 `bin/`、`lib/`、`share/` 结构，不要只复制 `.exe` 丢掉 DLL。
如果 Windows 解释器命名为 `python`，准备和校验命令相应替换 `python3`。

## 生成语音

下面用 Linux CPU 举例，其他平台替换可执行文件；Windows 使用
`stage/audio8-windows/bin/llama-tts.exe`。

```bash
stage/audio8-cpu/bin/llama-tts \
  --audio8-model-dir model/Audio8-TTS-Realistic-Air/llama-cpp \
  --text "你好，欢迎使用 Audio8。" --output hello.wav \
  --gpu-layers 0 --threads 4 --seed 0 --max-frames 512 --report hello.json
```

Linux CUDA 使用 `stage/audio8-cuda/bin/llama-tts`，把 `--gpu-layers 0` 换为
`--gpu-layers 99 --codec-gpu`。Mac CPU 使用 Mac 二进制和 `--gpu-layers 0`，
不加 `--codec-gpu`。

音色克隆在上述完整命令中增加两项：

```bash
  --reference-audio reference.wav \
  --reference-text "参考录音中实际说出的完整文字。"
```

输出为单声道 44.1 kHz float32 WAV。默认 top-k 50、top-p 0.9、temperature 0.7，
`--greedy` 关闭采样。native 的固定 seed 用于同运行时/配置复现，不等于 Torch
随机数算法；两框架填相同数字，不保证生成相同语音。
已有 WAV/report 不覆盖。达到帧预算却未 EOS 时默认报错；只有明确接受不完整
音频时才加 `--allow-partial`，并查看 `stop_reason`。

## HTTP 与流式输出

启动本地服务；参考音频目录按需开放：

```bash
stage/audio8-cpu/bin/llama-server \
  --audio8-model-dir model/Audio8-TTS-Realistic-Air/llama-cpp \
  --host 127.0.0.1 --port 8080 --threads 4 --gpu-layers 0

curl --fail http://127.0.0.1:8080/health
curl --fail http://127.0.0.1:8080/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"model":"audio8","input":"Hello, Audio8.","response_format":"wav","seed":0}' \
  --output hello-http.wav
```

克隆时启动参数增加 `--reference-dir /path/to/references`，请求增加
`"reference_audio":"speaker.wav","reference_text":"录音原文。"`。
音频名相对于服务端参考目录，不是远程 URL 或上传字段。
这里只提供有限的 speech API：仅 `voice=default`、WAV 响应和本文 Audio8 参数；
不宣称兼容完整 OpenAI API 或普通 llama-server 的全部接口。
同一时刻只执行一个生成任务，并发生成返回 HTTP 429，没有 SGLang 动态 batching。

流式表示整句结束前就交付音频。CLI 同时保存最终 WAV，并把原始单声道
44.1 kHz **F32 little-endian PCM** 写到 stdout：

```bash
stage/audio8-cpu/bin/llama-tts \
  --audio8-model-dir model/Audio8-TTS-Realistic-Air/llama-cpp \
  --text "这是一条分块生成的语音。" --output stream.wav \
  --stream --chunk-frames 12 --gpu-layers 0 --threads 4 > stream.f32

curl --no-buffer --fail http://127.0.0.1:8080/audio8/stream \
  -H 'Content-Type: application/json' \
  -d '{"model":"audio8","input":"Hello, Audio8.","request_id":"example-1","chunk_frames":12}'
```

HTTP 返回 SSE：`start` 描述格式，`audio` 带 `offset_samples`、`samples`、
`pcm_base64`，最后为 `done` 或 `error`。客户端按序解码和播放 PCM，
它不是一串独立 WAV。取消入口为 `POST /audio8/cancel/example-1`。
Windows 不要用 PowerShell 的文本重定向处理 CLI 二进制 stdout，
应使用支持二进制的客户端或 `cmd.exe` 重定向。

构建已开启增量 codec，实际以报告的 `streaming_decode_policy` 为准；
关闭 `AUDIO8_CODEC_STREAM` 会退回完整前缀重算。
chunk 大小影响等待时间与计算开销。

## 精度与性能

模型包使用 F32 权重并自带预计算 RoPE 表，运行时保留默认精度设置即可。
主要性能调节项为 CPU 线程、SIMD/Accelerate、GPU offload 和 chunk 大小。

H20 / F32 参考测量中，约 26 秒长句的非流式暖 RTF 中位数为 **0.535**；
12 帧分块缓存流式 RTF 为 **0.621**、首 PCM **363 ms**。中位数来自每配置四次
暖运行，不含加载、网络、声卡。M4 CPU 两线程参考音色克隆生成约 5.5–7.9 秒
音频，耗时约 21–32 秒，不含模型加载。性能随硬件、构建选项和输入长度变化。

## 重新导出权重

普通使用直接下载 GGUF 即可。自行导出时，下载固定源版本并排除 GGUF 子目录，
在独立环境安装 converter 依赖。CPU 转换需要数 GiB 内存及至少 7 GiB 空闲磁盘：

```bash
hf download Edge0/Audio8-TTS-Realistic-Air \
  --revision 655a4cd17916bfbec9189f4f46bad2fc2f70a2cf \
  --exclude "llama-cpp/**" --local-dir model/realistic-source-pinned
python3 -m venv .venv-conversion
. .venv-conversion/bin/activate
pip install -r llama_cpp/converter/requirements-conversion.txt
mkdir -p converted
python llama_cpp/converter/convert_audio8_realistic.py \
  --model-dir model/realistic-source-pinned --llama-cpp vendor/llama.cpp \
  --output-dir converted/realistic-f32 --threads 4
python -S llama_cpp/converter/convert_audio8_realistic.py \
  --verify-only --output-dir converted/realistic-f32
```

不要额外安装 `gguf` wheel；转换器使用并校验传入 llama.cpp 的固定 `gguf-py`
源码，导出前验证原模型 SHA。输出父目录须存在，最终目录及同名 `.partial`
须不存在；失败现场保留，不自动覆盖。元数据和生成环境会记录在 manifest，
细节见 converter README。

## 排错

| 现象 | 检查 |
|---|---|
| 普通 llama.cpp 无法加载 | 必须用固定补丁运行时，且同时保留 slow/fast、codec 与 embedding sidecar |
| 找不到 runtime JSON 或权重 | 参数指向完整 `llama-cpp/`；先跑标准库校验器 |
| 缺少 `.dylib` / `.so` / DLL | 安装 `Audio8Runtime` 并保留目录结构；补丁已纳入 Mac 可选 BLAS |
| CPU 很慢 | 初始配置关闭了可选 SIMD/OpenMP；优化配置另测 |
| 多次生成结果不同 | 固定运行时、模型文件、后端、seed 和采样设置 |
| 流式乱码 | CLI 是二进制 F32 PCM，HTTP 是携带 base64 PCM 的 SSE |
| 达到帧预算 | 缩短文本或增加有界预算；只有明确接受不完整输出才启用 partial |

## 许可

Realistic Air 模型和 Audio8 代码使用 [Apache-2.0](../LICENSE)，归属见
[NOTICE](../NOTICE)。llama.cpp 及所含第三方保留各自许可；运行时安装将相关
声明放在 `share/audio8/licenses/`，分发时一并保留。
