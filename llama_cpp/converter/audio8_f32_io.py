"""Bounded F32 bytes for the hash-locked GGUF writer, without NumPy fallocate.

This adapter is deliberately limited to little-endian, contiguous F32 tensors.
No NumPy/Torch imports are needed; --verify-only remains standard-library-only.
"""
import sys
import tempfile

BLOCK_BYTES = 1024 * 1024


def _bytes(array):
    if sys.byteorder != 'little' or array.dtype.str != '<f4' or not array.flags.c_contiguous:
        raise ValueError('Expected contiguous little-endian F32 tensor')
    view = memoryview(array).cast('B')
    if len(view) != array.nbytes or not len(view):
        raise ValueError('Expected a nonempty F32 tensor')
    return view


def write_f32(stream, array):
    view = _bytes(array)
    start = stream.tell()
    position = 0
    while position < len(view):
        block = view[position:position + BLOCK_BYTES]
        written = stream.write(block)
        if not isinstance(written, int) or not 0 < written <= len(block):
            raise OSError('F32 write made zero or invalid progress')
        position += written
    if stream.tell() - start != len(view):
        raise OSError('F32 write cursor differs from payload length')


def add_f32_tensor(writer, name, array):
    _bytes(array)  # Reject unsupported tensors before registering metadata.
    if not writer.use_temp_file:
        raise ValueError('F32 adapter requires the pinned temporary-file writer')
    writer.add_tensor_info(name, array.shape, array.dtype, array.nbytes)
    if writer.temp_file is None:
        writer.temp_file = tempfile.TemporaryFile(mode='w+b')
    write_f32(writer.temp_file, array)
    writer.write_padding(writer.temp_file, array.nbytes)


def close_writer(writer):
    try:
        writer.close()
    finally:
        if writer.temp_file is not None and not writer.temp_file.closed:
            writer.temp_file.close()
