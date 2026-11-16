# Realistic Air F32 converter

[Runbook](../../guides/llama-cpp.md#reproduce-the-model-files) · [中文](../../guides/llama-cpp_zh.md#重新导出权重)

Use Python 3.10+ and the direct dependency constraints in
`requirements-conversion.txt`. The converter uses
the pinned llama.cpp tree's `gguf-py` directly; do not install a separate `gguf`
package. No downloads are performed by the converter.

The current download repository is `Edge0/Audio8-TTS-Realistic-Air`. The fixed
source revision `655a4cd17916bfbec9189f4f46bad2fc2f70a2cf` and internal compatibility
identifier `Edge0/Audio8-TTS-Realistic-0.6b` remain unchanged; this is the same
released checkpoint, not another platform's model.

```sh
python llama_cpp/converter/convert_audio8_realistic.py \
  --model-dir /path/to/pinned-transformers-snapshot \
  --llama-cpp /path/to/patched-llama.cpp \
  --output-dir /path/to/NEW-bundle --threads 4

python -S llama_cpp/converter/convert_audio8_realistic.py \
  --verify-only --output-dir /path/to/bundle
```

The output parent must exist; the final directory and its sibling `.partial`
must not exist. Reserve at least 7 GiB of free space and several GiB of RAM.
Conversion runs on CPU, defaults to four threads, preserves failed staging
directories, and does not replace an existing bundle. Complete official RoPE
tables, tensor payloads, tokenizer and licenses are checked. It does not require
Transformers or ONNX Runtime.

`--verify-only` needs only Python's standard library and reads every bundle file
to verify checksums and the exact inventory. The conversion manifest records the
source revision, tensor hashes and export environment for reproducibility.
