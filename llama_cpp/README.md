<div align="center">

<img src="../assets/readme-06b.svg" alt="Audio8-TTS-Realistic-Air" width="960">

**Native Audio8 inference with llama.cpp / GGML.**

[English runbook](../guides/llama-cpp.md) · [中文运行手册](../guides/llama-cpp_zh.md) · [Model files](https://huggingface.co/Edge0/Audio8-TTS-Realistic-Air/tree/main/llama-cpp)

</div>

This Audio8-specific patch adds native inference to a fixed llama.cpp revision:
text processing, DualAR generation, reference-audio encoding, codec decoding,
WAV output and HTTP/streaming interfaces. Use it with the shared F32 model bundle
and the build commands in the runbook.

| Material | Purpose |
|---|---|
| [`source-lock.json`](source-lock.json) | Fixed upstream commit, patch checksum and patched source hashes |
| [`patches/audio8.patch`](patches/audio8.patch) | Native implementation, core changes, tool dispatch and installation rules |
| [`prepare.py`](prepare.py) | Apply to a clean pinned checkout; refuse unexpected changes; verify patched files |
| [`converter/`](converter/) | Reproduce the F32 assets from the hash-locked public Realistic checkpoint |

The runtime uses **one shared F32 model bundle** with platform-specific builds.
See the runbook for Linux CPU/CUDA, macOS and Windows commands.

<blockquote>
<sub><strong>Note:</strong> Use CPU on macOS; Metal is experimental. The Windows build instructions have not yet been tested on a Windows machine.</sub>
</blockquote>

The model and Audio8 contributions use the repository's Apache-2.0 license.
The patch retains upstream license headers; the resulting llama.cpp tree also
contains its MIT and bundled third-party licenses. `Audio8Runtime` installation
includes the collected notices under `share/audio8/licenses/`.
