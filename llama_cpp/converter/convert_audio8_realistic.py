#!/usr/bin/env python3
"""Convert the pinned public Realistic release directly into a native F32 bundle."""
from __future__ import annotations

import argparse
import ast
import ctypes
import datetime
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import tempfile

# This must precede Torch (including imports performed by the official codec).
os.environ['CUDA_VISIBLE_DEVICES'] = ''
sys.dont_write_bytecode = True

from audio8_ar_helpers import file_sha256, tensor_map, validate_config, LLAMA_CPP_REVISION
from audio8_codec_helpers import load_official
from audio8_f32_io import add_f32_tensor, close_writer, write_f32

HERE = Path(__file__).resolve().parent
MODEL_LOCK = json.loads((HERE / 'model-source-lock.json').read_text())
GGUF_LOCK = json.loads((HERE / 'gguf-source-lock.json').read_text())
REVISION = MODEL_LOCK['revision']
MODEL = MODEL_LOCK['model']
MODE = 'official_bf16_table_v1'
TABLE = 'audio8.rope_coeffs.weight'
ASSETS = {'slow': 'models/slow-f32.gguf', 'fast': 'models/fast-f32.gguf',
          'codebook_embeddings': 'models/codebook_embeddings.f32',
          'codec': 'models/audio8-realistic-codec-f32.gguf'}


def write_json(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def stable_sha(path):
    before = path.stat()
    result = file_sha256(path)
    after = path.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
        raise ValueError(f'Input changed during hashing: {path.name}')
    return result


def validate_sources(model, llama):
    source = {}
    for name, expected in MODEL_LOCK['files'].items():
        path = model / name
        if not path.is_file() or path.stat().st_size != expected['bytes'] or stable_sha(path) != expected['sha256']:
            raise ValueError(f'Pinned public Realistic input differs: {name}')
        source[name] = dict(expected)
    actual_package = {path.relative_to(llama).as_posix() for path in (llama / 'gguf-py/gguf').rglob('*.py')}
    expected_package = {name for name in GGUF_LOCK['files'] if name.endswith('.py')}
    if actual_package != expected_package:
        raise ValueError('Vendored gguf Python file inventory differs from the pinned source')
    for name, expected in GGUF_LOCK['files'].items():
        path = llama / name
        if not path.is_file() or stable_sha(path) != expected:
            raise ValueError(f'Pinned llama.cpp conversion source differs: {name}')
    return source


def load_dependencies(llama, threads):
    os.environ['OMP_NUM_THREADS'] = str(threads)
    os.environ['OPENBLAS_NUM_THREADS'] = str(threads)
    os.environ['MKL_NUM_THREADS'] = str(threads)
    import numpy as np
    import torch
    import safetensors
    import yaml
    if torch.__version__.split('+')[0] != '2.8.0' or np.__version__ != '1.26.4' or safetensors.__version__ != '0.5.3':
        raise RuntimeError('This converter requires Torch 2.8.0, NumPy 1.26.4 and safetensors 0.5.3; see README')
    if yaml.__version__ != '6.0.3':
        raise RuntimeError('Pinned vendored gguf import requires PyYAML 6.0.3; see README')
    if 'gguf' in sys.modules:
        raise RuntimeError('Start a fresh Python process; gguf must come only from --llama-cpp/gguf-py')
    sys.path.insert(0, str(llama / 'gguf-py'))
    gguf = importlib.import_module('gguf')
    if Path(gguf.__file__).resolve() != (llama / 'gguf-py/gguf/__init__.py').resolve():
        raise RuntimeError('Unexpected gguf module origin')
    torch.set_num_threads(threads)
    torch.set_num_interop_threads(1)
    torch.set_default_dtype(torch.float32)
    torch.set_default_device('cpu')
    versions = {'python': platform.python_version(), 'torch': torch.__version__, 'numpy': np.__version__,
                'safetensors': safetensors.__version__, 'PyYAML': yaml.__version__,
                'gguf_source_revision': LLAMA_CPP_REVISION, 'CUDA_VISIBLE_DEVICES': '',
                'torch_threads': torch.get_num_threads(), 'torch_interop_threads': torch.get_num_interop_threads()}
    return gguf, np, torch, versions


def official_ar_tables(model, np, torch):
    source_path = model / 'modeling_arktts.py'
    source = source_path.read_text(encoding='utf-8')
    nodes = [node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == '_precompute_rope']
    if len(nodes) != 1:
        raise ValueError('Expected exactly one pinned official RoPE function')
    scope = {'torch': torch, 'Tensor': torch.Tensor}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), str(source_path), 'exec'), scope)
    arrays, records = {}, {}
    with torch.inference_mode():
        for branch, positions in [('slow', 2048), ('fast', 10)]:
            original = scope['_precompute_rope'](positions, 64, 1000000.0)
            if original.device.type != 'cpu' or original.dtype != torch.bfloat16 or tuple(original.shape) != (positions, 32, 2):
                raise ValueError('Unexpected official RoPE shape/device/dtype')
            table = np.asarray(original.float().contiguous().numpy().reshape(positions, 64), dtype='<f4')
            digest = hashlib.sha256(memoryview(table)).hexdigest()
            if not np.isfinite(table).all() or np.any(table.view('<u4') & 0xffff) or digest != MODEL_LOCK['rope_payload_sha256'][branch]:
                raise ValueError(f'Official full {branch} RoPE table differs from the accepted CPU table')
            arrays[branch] = table
            records[branch] = {'shape': list(table.shape), 'dtype': 'F32', 'payload_sha256': digest}
    return arrays, {'policy': 'Unmodified pinned official function on CPU; exact BF16-to-F32 expansion',
                    'layout': 'numpy[position,64], adjacent cos/sin pairs; GGML[64,position]',
                    'function_source_sha256': hashlib.sha256(ast.get_source_segment(source, nodes[0]).encode()).hexdigest(),
                    'tables': records}


def tokenizer_contract(model, config, gguf):
    tokenizer = json.loads((model / 'tokenizer.json').read_text(encoding='utf-8'))
    if tokenizer['normalizer'] != {'type': 'NFC'} or tokenizer['model']['type'] != 'BPE':
        raise ValueError('Unsupported tokenizer algorithm')
    vocab, additions = tokenizer['model']['vocab'], tokenizer['added_tokens']
    if (len(vocab), len(tokenizer['model']['merges']), len(additions)) != (151643, 151387, 4131):
        raise ValueError('Unexpected tokenizer inventory')
    tokens = [None] * config['vocab_size']
    types = [gguf.TokenType.UNUSED] * len(tokens)
    for token, index in vocab.items():
        if not isinstance(index, int) or not 0 <= index < len(tokens) or tokens[index] is not None:
            raise ValueError('Duplicate or invalid tokenizer ID')
        tokens[index], types[index] = token, gguf.TokenType.NORMAL
    for token in additions:
        if any(token[key] for key in ['single_word', 'lstrip', 'rstrip', 'normalized']):
            raise ValueError('Unsupported added-token matching flags')
        index = token['id']
        if not isinstance(index, int) or not 0 <= index < len(tokens) or tokens[index] is not None:
            raise ValueError('Duplicate or invalid added-token ID')
        tokens[index] = token['content']
        types[index] = gguf.TokenType.CONTROL if token['special'] else gguf.TokenType.USER_DEFINED
    unused = [index for index, token in enumerate(tokens) if token is None]
    if unused != [155774, 155775]:
        raise ValueError('Unexpected embedding-only rows')
    for index in unused:
        tokens[index] = f'[AUDIO8_UNUSED_{index}]'
    merges = [' '.join(pair) if isinstance(pair, list) else pair for pair in tokenizer['model']['merges']]
    if len(set(tokens)) != len(tokens):
        raise ValueError('Tokenizer strings must be unique')
    return {'tokens': tokens, 'types': [int(x) for x in types], 'merges': merges, 'unused': unused}


def add_tokenizer(writer, text):
    writer.add_tokenizer_model('gpt2')
    writer.add_tokenizer_pre('qwen2')
    writer.add_token_list(text['tokens'])
    writer.add_token_types(text['types'])
    writer.add_token_merges(text['merges'])
    writer.add_add_bos_token(False)
    writer.add_add_eos_token(False)
    writer.add_eos_token_id(151643)
    writer.add_pad_token_id(151643)
    writer.add_eot_token_id(151645)
    writer.add_string('audio8.text.contract', 'arktts_processor_v1')
    writer.add_string('audio8.text.normalizer', 'NFC_in_native_processor')
    writer.add_string('audio8.text.python_unicode_version', '13.0.0')
    writer.add_string('audio8.text.processor_sha256', MODEL_LOCK['files']['processing_arktts.py']['sha256'])
    writer.add_string('audio8.text.tokenizer_sha256', MODEL_LOCK['files']['tokenizer.json']['sha256'])
    writer.add_array('audio8.text.unused_embedding_rows', text['unused'])


def ar_writer(gguf, path, config, branch, table_record, text):
    fast = branch == 'fast'
    writer = gguf.GGUFWriter(path, 'llama', use_temp_file=True)
    writer.add_name(f'Audio8 Realistic 0.6B {branch} AR with official RoPE')
    writer.add_description('Pinned private native Audio8 integration; requires matching runtime and text processor')
    writer.add_file_type(gguf.LlamaFileType.ALL_F32)
    writer.add_vocab_size(config['codebook_size' if fast else 'vocab_size'])
    if fast:
        writer.add_tokenizer_model('none')
    else:
        add_tokenizer(writer, text)
    writer.add_context_length(config['num_codebooks' if fast else 'max_seq_len'])
    writer.add_embedding_length(config['fast_dim' if fast else 'dim'])
    writer.add_feed_forward_length(config['fast_intermediate_size' if fast else 'intermediate_size'])
    writer.add_block_count(config['n_fast_layer' if fast else 'n_layer'])
    writer.add_head_count(config['fast_n_head' if fast else 'n_head'])
    writer.add_head_count_kv(config['fast_n_local_heads' if fast else 'n_local_heads'])
    writer.add_key_length(config['fast_head_dim' if fast else 'head_dim'])
    writer.add_value_length(config['fast_head_dim' if fast else 'head_dim'])
    writer.add_layer_norm_rms_eps(config['norm_eps'])
    writer.add_rope_dimension_count(config['fast_head_dim' if fast else 'head_dim'])
    writer.add_rope_freq_base(config['rope_base'])
    writer.add_string('llama.rope.scaling.type', 'none')
    writer.add_causal_attention(True)
    writer.add_bool('audio8.prototype', True)
    writer.add_string('audio8.graph', 'llama_fused_qkv_official_rope_table_v1')
    writer.add_string('audio8.branch', branch)
    writer.add_string('audio8.source_model', 'Audio8-TTS-Realistic-0.6b')
    writer.add_string('audio8.source_revision', REVISION)
    writer.add_string('audio8.source_weights_sha256', MODEL_LOCK['files']['model.safetensors']['sha256'])
    writer.add_string('audio8.llama_cpp_revision', LLAMA_CPP_REVISION)
    writer.add_string('audio8.rope.mode', MODE)
    writer.add_uint32('audio8.rope.n_positions', table_record['shape'][0])
    writer.add_string('audio8.rope.coefficients_sha256', table_record['payload_sha256'])
    writer.add_string('audio8.rope_note', 'Official BF16-rounded coefficients stored as exact F32 rows; shared CPU/CUDA graph rotation')
    writer.add_bool('audio8.tied_output', not fast)
    for key in ['num_codebooks', 'codebook_size', 'semantic_begin_id', 'semantic_end_id', 'eos_token_id']:
        writer.add_uint32('audio8.' + key, config[key])
    return writer


def tensor_record(name, array, **extra):
    return dict(name=name, shape=list(array.shape), dtype='F32',
                sha256=hashlib.sha256(memoryview(array)).hexdigest(), **extra)


def verify_gguf(path, records, gguf, text=None, metadata=None):
    reader = gguf.GGUFReader(path)
    tensors = {tensor.name: tensor for tensor in reader.tensors}
    if len(tensors) != len(records) or set(tensors) != {row['name'] for row in records}:
        raise ValueError('Serialized tensor inventory differs')
    for row in records:
        tensor = tensors[row['name']]
        if tensor.tensor_type != gguf.GGMLQuantizationType.F32 or list(tensor.shape) != row['shape'][::-1]:
            raise ValueError('Serialized shape/type differs: ' + row['name'])
        if hashlib.sha256(memoryview(tensor.data)).hexdigest() != row['sha256']:
            raise ValueError('Serialized payload differs: ' + row['name'])
    if text:
        for key, value in [('tokenizer.ggml.tokens', text['tokens']), ('tokenizer.ggml.token_type', text['types']),
                           ('tokenizer.ggml.merges', text['merges'])]:
            if reader.fields[key].contents() != value:
                raise ValueError('Serialized tokenizer differs: ' + key)
    for key, value in (metadata or {}).items():
        if key not in reader.fields or reader.fields[key].contents() != value:
            raise ValueError('Serialized metadata differs: ' + key)
    # Drop every view before the enclosing directory is renamed (Windows mmap).
    del tensors, reader


def export_ar(source, config, folder, tables, rope_report, text, gguf, np, torch):
    outputs = {}
    expected = {item[0] for branch in ['slow', 'fast'] for item in tensor_map(config, branch)} | {'codebook_embeddings.weight'}
    if set(source.keys()) != expected or len(expected) != 226:
        raise ValueError('Realistic source tensor coverage differs')
    for branch in ['slow', 'fast']:
        path = folder / ASSETS[branch]
        writer = ar_writer(gguf, path, config, branch, rope_report['tables'][branch], text)
        records = []
        try:
            for original, target, shape in tensor_map(config, branch):
                value = source.get_tensor(original)
                if tuple(value.shape) != shape or value.dtype != torch.bfloat16:
                    raise ValueError('Source tensor shape/type differs: ' + original)
                array = np.asarray(value.float().contiguous().numpy(), dtype='<f4')
                if not np.isfinite(array).all():
                    raise ValueError('Nonfinite source tensor: ' + original)
                add_f32_tensor(writer, target, array)
                records.append(tensor_record(target, array, source=original, transform='BF16_to_F32_no_permutation'))
            add_f32_tensor(writer, TABLE, tables[branch])
            records.append(tensor_record(TABLE, tables[branch], source='official_CPU_RoPE'))
            writer.write_header_to_file(); writer.write_kv_data_to_file(); writer.write_tensors_to_file(progress=False)
        finally:
            close_writer(writer)
        verify_gguf(path, records, gguf, text if branch == 'slow' else None,
                    {'audio8.rope.mode': MODE, 'audio8.branch': branch,
                     'audio8.rope.n_positions': tables[branch].shape[0], 'llama.rope.scaling.type': 'none'})
        outputs[branch] = dict(path=ASSETS[branch], bytes=path.stat().st_size, sha256=file_sha256(path), tensors=records)
        print(json.dumps({'exported': branch, 'tensors': len(records)}), flush=True)
    value = source.get_tensor('codebook_embeddings.weight')
    if value.dtype != torch.bfloat16 or tuple(value.shape) != (40960, 896):
        raise ValueError('Invalid source codebook embeddings')
    array = np.asarray(value.float().contiguous().numpy(), dtype='<f4')
    path = folder / ASSETS['codebook_embeddings']
    with path.open('xb') as stream:
        write_f32(stream, array)
    digest = file_sha256(path)
    if not np.isfinite(array).all() or digest != MODEL_LOCK['sidecar_payload_sha256']:
        raise ValueError('Codebook sidecar differs from pinned F32 expansion')
    outputs['codebook_embeddings'] = dict(path=ASSETS['codebook_embeddings'], bytes=path.stat().st_size,
        sha256=digest, shape=[40960, 896], dtype='float32_le', layout='row-major: book*4096+code, channel')
    return outputs


def export_codec(model, folder, gguf, np, torch):
    module, codec, folded = load_official(model, fold_weight_norm=True)
    if len(folded) != 80:
        raise ValueError('Unexpected weight-normalization folding inventory')
    path = folder / ASSETS['codec']
    writer = gguf.GGUFWriter(path, 'audio8_codec', use_temp_file=True)
    writer.add_name('Audio8 Realistic native codec F32 baseline')
    writer.add_file_type(gguf.LlamaFileType.ALL_F32)
    writer.add_string('audio8.codec.format', 'native_f32_v1')
    writer.add_string('audio8.codec.source_sha256', MODEL_LOCK['files']['codec.pth']['sha256'])
    writer.add_string('audio8.codec.python_sha256', MODEL_LOCK['files']['modeling_arktts_codec.py']['sha256'])
    for key, value in [('sample_rate', 44100), ('frame_length', 2048), ('num_codebooks', 10),
                       ('semantic_size', 4096), ('acoustic_size', 1024), ('rope_positions', 8192)]:
        writer.add_uint32('audio8.codec.' + key, value)
    writer.add_string('audio8.codec.rope_policy', 'official_cpu_bf16_promoted_f32')
    records = []
    try:
        with torch.inference_mode():
            for name, value in codec.state_dict().items():
                array = np.asarray(value.detach().float().cpu().contiguous().numpy(), dtype='<f4')
                if not np.isfinite(array).all():
                    raise ValueError('Nonfinite folded codec tensor: ' + name)
                add_f32_tensor(writer, name, array)
                records.append(tensor_record(name, array))
            rope = module._rope(8192, 64, 10000.0, device='cpu').float().reshape(8192, 64).contiguous().numpy()
            rope = np.asarray(rope, dtype='<f4')
            row = tensor_record('audio8.codec.rope_coeffs.weight', rope)
            if not np.isfinite(rope).all() or np.any(rope.view('<u4') & 0xffff) or row['sha256'] != MODEL_LOCK['rope_payload_sha256']['codec']:
                raise ValueError('Official CPU codec RoPE table differs')
            add_f32_tensor(writer, row['name'], rope); records.append(row)
        if len(records) != 456:
            raise ValueError('Unexpected codec tensor inventory')
        writer.write_header_to_file(); writer.write_kv_data_to_file(); writer.write_tensors_to_file(progress=False)
    finally:
        close_writer(writer)
    verify_gguf(path, records, gguf, metadata={'audio8.codec.format': 'native_f32_v1', 'audio8.codec.rope_positions': 8192})
    print(json.dumps({'exported': 'codec', 'tensors': len(records), 'folded_modules': len(folded)}), flush=True)
    return dict(path=ASSETS['codec'], bytes=path.stat().st_size, sha256=file_sha256(path), tensors=records,
                folded_modules=folded, weight_norm_policy='Official CPU FP32 evaluation then remove; source untouched')


def contained_regular(root, relative):
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError('Invalid relative output path')
    current = root
    for part in path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('Output symlinks are not permitted')
    if not current.is_file() or not current.resolve().is_relative_to(root.resolve()):
        raise ValueError('Output must be a contained regular file')
    return current


def verify_bundle(folder):
    folder = folder.resolve(strict=True)
    runtime = json.loads(contained_regular(folder, 'audio8-runtime.json').read_text())
    conversion = json.loads(contained_regular(folder, 'conversion-manifest.json').read_text())
    if runtime['schema'] != 'audio8.runtime_bundle.v1' or runtime['model'] != MODEL or runtime['development_links'] is not False:
        raise ValueError('Unsupported runtime manifest')
    if conversion['status'] != 'converted_serialization_verified_runtime_pending' or conversion['source_revision'] != REVISION:
        raise ValueError('Unfinished or unexpected conversion manifest')
    if set(runtime['assets']) != set(ASSETS) or set(conversion['outputs']) != set(ASSETS):
        raise ValueError('Unexpected four-asset inventory')
    for key, asset in runtime['assets'].items():
        if asset['path'] != ASSETS[key]:
            raise ValueError('Unexpected asset location')
        path = contained_regular(folder, asset['path'])
        if path.stat().st_size != asset['bytes'] or file_sha256(path) != asset['sha256']:
            raise ValueError('Complete asset checksum mismatch: ' + key)
        if any(conversion['outputs'][key][field] != asset[field] for field in ['path', 'bytes', 'sha256']):
            raise ValueError('Runtime/conversion manifests disagree')
    sums = contained_regular(folder, 'SHA256SUMS').read_text().splitlines()
    listed = {}
    for line in sums:
        digest, relative = line.split('  ', 1)
        if relative in listed or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('Invalid or duplicate checksum entry')
        path = contained_regular(folder, relative)
        if file_sha256(path) != digest:
            raise ValueError('Bundle checksum mismatch: ' + relative)
        listed[relative] = digest
    actual = set()
    for path in folder.rglob('*'):
        if path.is_symlink():
            raise ValueError('Unexpected symlink in output bundle')
        if path.is_file() and path != folder / 'SHA256SUMS':
            actual.add(path.relative_to(folder).as_posix())
    if actual != set(listed):
        raise ValueError('Checksum inventory is incomplete or contains extra files')
    for name in ['LICENSE', 'NOTICE']:
        if listed.get(name) != MODEL_LOCK['files'][name]['sha256']:
            raise ValueError('Original model license/notice changed')
    return {'status': 'verified_complete_file_hashes', 'assets': 4,
            'files': len(listed), 'output_dir': str(folder),
            'scope': 'Full-file integrity includes serialized tensor payloads; no model execution or product acceptance.'}


def commit_no_replace(source, target):
    """Atomic same-filesystem directory publication, refusing even a racing target."""
    if os.name == 'nt':
        os.rename(source, target)  # Windows fails if target already exists.
        return
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform.startswith('linux'):
        function = libc.renameat2
        function.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        function.restype = ctypes.c_int
        result = function(-100, os.fsencode(source), -100, os.fsencode(target), 1)  # RENAME_NOREPLACE
    elif sys.platform == 'darwin':
        function = libc.renamex_np
        function.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        function.restype = ctypes.c_int
        result = function(os.fsencode(source), os.fsencode(target), 0x4)  # SDK sys/stdio.h RENAME_EXCL
    else:
        raise RuntimeError('No verified atomic no-replace directory publication for this OS')
    if result:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), str(target))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model-dir', type=Path)
    parser.add_argument('--llama-cpp', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if args.verify_only:
        print(json.dumps(verify_bundle(args.output_dir), ensure_ascii=False), flush=True)
        return
    if args.model_dir is None or args.llama_cpp is None:
        parser.error('--model-dir and --llama-cpp are required for conversion')
    if not 1 <= args.threads <= 16:
        parser.error('--threads must be in 1..16')
    if sys.byteorder != 'little':
        raise RuntimeError('This release supports little-endian hosts only')
    output = args.output_dir.absolute()
    partial = output.with_name(output.name + '.partial')
    if output.exists() or output.is_symlink() or partial.exists() or partial.is_symlink():
        raise FileExistsError('Output or .partial directory exists; choose a new directory')
    if not output.parent.is_dir():
        raise ValueError('Output parent must already exist')
    if shutil.disk_usage(output.parent).free < 7 * 1024**3:
        raise RuntimeError('Need at least 7 GiB free for final assets and colocated temporary tensors')
    model, llama = args.model_dir.resolve(strict=True), args.llama_cpp.resolve(strict=True)
    source_files = validate_sources(model, llama)
    config = json.loads((model / 'config.json').read_text())
    validate_config(config)
    if (config['max_seq_len'], config['norm_eps'], config['eos_token_id']) != (2048, 1e-6, 151645):
        raise ValueError('Unexpected Realistic context/norm/EOS contract')
    gguf, np, torch, versions = load_dependencies(llama, args.threads)
    from safetensors import safe_open
    partial.mkdir(exist_ok=False)
    (partial / 'models').mkdir()
    work = partial / '.work'
    work.mkdir()
    old_tempdir = tempfile.tempdir
    tempfile.tempdir = str(work)
    try:
        tables, rope_report = official_ar_tables(model, np, torch)
        text = tokenizer_contract(model, config, gguf)
        with safe_open(model / 'model.safetensors', framework='pt', device='cpu') as source:
            outputs = export_ar(source, config, partial, tables, rope_report, text, gguf, np, torch)
        outputs['codec'] = export_codec(model, partial, gguf, np, torch)
        # Re-hash the source after conversion so a concurrent source change cannot
        # publish a successful provenance record.
        validate_sources(model, llama)
        for name in ['LICENSE', 'NOTICE']:
            shutil.copyfile(model / name, partial / name)
        producer_files = {path.name: file_sha256(path) for path in sorted(HERE.iterdir())
                          if path.is_file() and path.suffix in ('.py', '.json', '.txt', '.md')}
        manifest = {'schema': 'audio8.portable_realistic_conversion.v1',
                    'status': 'converted_serialization_verified_runtime_pending',
                    'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    'source_model': MODEL, 'source_revision': REVISION, 'source_files': source_files,
                    'llama_cpp_revision': LLAMA_CPP_REVISION, 'gguf_source_files_sha256': GGUF_LOCK['files'],
                    'llama_cpp_identity_scope': 'Pinned vendored conversion package; no Git required, runtime core is separately locked',
                    'producer_files_sha256': producer_files, 'environment': versions,
                    'platform': platform.platform(), 'cpu_only': True, 'converter_revision': 2,
                    'tensor_io': 'bounded_memoryview_write_v1_no_numpy_fallocate', 'outputs': outputs, 'ar_rope': rope_report,
                    'tokenizer': {'base_vocab': 151643, 'added_tokens': 4131, 'gguf_vocab': len(text['tokens']),
                                  'merges': len(text['merges']), 'unused_embedding_rows': text['unused'],
                                  'contract': 'arktts_processor_v1', 'normalizer': 'NFC_in_native_processor'},
                    'limitations': ['Private native runtime required, not arbitrary upstream llama-server',
                                    'This conversion verifies serialization; runtime and product acceptance are separate',
                                    'No Preview, quantization, historical golden or prior converted artifact input']}
        write_json(partial / 'conversion-manifest.json', manifest)
        runtime = {'schema': 'audio8.runtime_bundle.v1', 'model': MODEL, 'development_links': False,
                   'assets': {key: {field: item[field] for field in ['path', 'bytes', 'sha256']} for key, item in outputs.items()},
                   'source_model_revision': REVISION, 'llama_cpp_revision': LLAMA_CPP_REVISION,
                   'core_patch_sha256': '0bb9c43c90109c13a973c505f1fbe9fc439a609ca4cc23194f88014d6a629ded',
                   'distribution_status': 'unpublished_candidate',
                   'scope': 'Self-contained native F32 assets; matching runtime and platform acceptance are separate.'}
        write_json(partial / 'audio8-runtime.json', runtime)
        (partial / 'README.md').write_text('# Audio8 Realistic native F32 model bundle\n\n'
            'Generated directly from the pinned public release. Runtime binaries are separate.\n'
            'Requires the matching private Audio8 llama.cpp implementation; arbitrary upstream binaries are insufficient.\n'
            'No Python, PyTorch or ORT is required by native inference. The converter itself uses CPU Python.\n'
            'Verify with convert_audio8_realistic.py --verify-only --output-dir THIS_DIRECTORY.\n'
            'Conversion/serialization verified; runtime, listening, platform and product acceptance remain separate.\n', encoding='utf-8')
        work.rmdir()
        checksums = ''.join(f'{file_sha256(path)}  {path.relative_to(partial).as_posix()}\n'
                            for path in sorted(partial.rglob('*')) if path.is_file())
        (partial / 'SHA256SUMS').write_text(checksums, encoding='utf-8')
        verify_bundle(partial)
        commit_no_replace(partial, output)
        print(json.dumps({'status': manifest['status'], 'output_dir': str(output), 'assets': 4}), flush=True)
    finally:
        tempfile.tempdir = old_tempdir
        # On failure the isolated .partial is intentionally retained for diagnosis;
        # no valid final output is published and no input/previous asset is changed.


if __name__ == '__main__':
    main()
