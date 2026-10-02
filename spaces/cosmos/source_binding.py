"""Validate the generated source binding against the mounted Cosmos payload."""
import hashlib
import json
import os
import re
from pathlib import Path, PurePosixPath


def mounted_files(root, declared):
    """Inventory payload; allow only CPython caches for declared Python modules."""
    result = set()
    def fail(error):
        raise error
    for directory, directories, filenames in os.walk(root, followlinks=False, onerror=fail):
        for name in directories + filenames:
            target = Path(directory) / name
            if target.is_symlink() or getattr(target, 'is_junction', lambda: False)():
                raise ValueError('mounted link')
        for name in filenames:
            target = Path(directory) / name
            if not target.is_file():
                raise ValueError('nonregular mounted entry')
            relative = target.relative_to(root)
            if relative.as_posix() == 'COSMOS_SOURCE_BINDING.json':
                continue
            if relative.parent.name == '__pycache__':
                match = re.fullmatch(r'(.+)\.cpython-[0-9]+(?:\.opt-[012])?\.pyc', name)
                source = relative.parent.parent / ((match[1] if match else '') + '.py')
                if match and source.as_posix() in declared:
                    continue
            result.add(relative.as_posix())
    return result


def bound_source(directory):
    root = Path(directory).resolve()
    try:
        binding = json.loads((root / 'COSMOS_SOURCE_BINDING.json').read_text(encoding='utf-8'))
        if not isinstance(binding, dict):
            raise ValueError('binding object required')
        if binding['schema'] != 'szl.cosmos-source/v1' or binding['repository'] != 'szl-holdings/anatomy' or binding['source_path'] != 'spaces/cosmos' or binding['destination'] != 'betterwithage/cosmos':
            raise ValueError('binding identity')
        if not re.fullmatch('[0-9a-f]{40}', binding['commit']):
            raise ValueError('source commit')
        files = binding['files']
        if not isinstance(files, dict) or not {'server.py', 'catalog.py', 'source_binding.py', 'index.html', 'vendor/three.module.min.js'}.issubset(files):
            raise ValueError('incomplete binding')
        if mounted_files(root, files) != set(files):
            raise ValueError('mounted file set mismatch')
        for name, digest in files.items():
            path = PurePosixPath(name)
            if not name or path.as_posix() != name or path.is_absolute() or '..' in path.parts or ':' in name or '\\' in name or not re.fullmatch('[0-9a-f]{64}', digest):
                raise ValueError('invalid file entry')
            target = root.joinpath(*path.parts)
            if target.is_symlink() or not target.resolve().is_relative_to(root) or hashlib.sha256(target.read_bytes()).hexdigest() != digest:
                raise ValueError('payload mismatch')
        return {'repository': binding['repository'], 'commit': binding['commit'], 'path': binding['source_path'], 'relation': 'mounted-files-match-publisher-binding', 'state': 'SOURCE_BOUND', 'evidence_url': 'https://github.com/' + binding['repository'] + '/tree/' + binding['commit'] + '/' + binding['source_path']}, 'SOURCE_BOUND_LOCAL_BYTES'
    except (OSError, ValueError, TypeError, KeyError):
        return None, 'UNKNOWN_SOURCE_RELATION'
