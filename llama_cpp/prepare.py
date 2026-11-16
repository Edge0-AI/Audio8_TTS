#!/usr/bin/env python3
"""Apply the Audio8 patch to a clean, pinned llama.cpp checkout (no downloads)."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent


def git(source, *arguments):
    result = subprocess.run(['git', '-C', str(source), *arguments],
                            capture_output=True, text=True, check=True)
    return result.stdout.strip()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(source, lock):
    for name, expected in lock['files'].items():
        path = source / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size != expected['bytes'] or sha256(path) != expected['sha256']:
            raise ValueError('Patched source differs: ' + name)
    return {'status': 'verified_patched_files', 'files': len(lock['files']),
            'upstream_commit': lock['upstream_commit'],
            'scope': 'Source integrity only; no build, inference or platform acceptance.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='A separately cloned llama.cpp checkout')
    parser.add_argument('--verify-only', action='store_true', help='Check an already patched checkout')
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    lock = json.loads((HERE / 'source-lock.json').read_text())
    patch = HERE / lock['patch']
    if sha256(patch) != lock['patch_sha256']:
        raise ValueError('Patch checksum differs from source-lock.json')
    if Path(git(source, 'rev-parse', '--show-toplevel')).resolve() != source:
        raise ValueError('--source must be the llama.cpp repository root')
    if git(source, 'rev-parse', 'HEAD') != lock['upstream_commit']:
        raise ValueError('Check out the exact upstream_commit in source-lock.json first')
    if not args.verify_only:
        if git(source, 'status', '--porcelain', '--untracked-files=all'):
            raise ValueError('Use a clean, separate checkout; existing changes are never overwritten')
        git(source, 'apply', '--check', str(patch))
        git(source, 'apply', str(patch))
    print(json.dumps(verify(source, lock), indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error))
