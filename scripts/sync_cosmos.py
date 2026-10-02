#!/usr/bin/env python3
"""Publish the isolated Cosmos subtree from immutable, signed protected main."""
import hashlib
import io
import json
import os
import re
import subprocess
import time
import urllib.request
from pathlib import Path

REPOSITORY = 'szl-holdings/anatomy'
SPACE = 'betterwithage/cosmos'
PREFIX = 'spaces/cosmos/'
LIVE = 'https://betterwithage-cosmos.hf.space'


def git(*args):
    return subprocess.check_output(['git', *args])


def json_get(url, token=None):
    headers = {'User-Agent': 'szl-cosmos-publisher/1', 'Accept': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
        return json.load(response)


def main_head(token):
    info = json_get('https://api.github.com/repos/' + REPOSITORY, token)
    if info['archived'] or info['default_branch'] != 'main':
        raise RuntimeError('canonical source is not active main')
    branch = json_get('https://api.github.com/repos/' + REPOSITORY + '/branches/main', token)
    if branch.get('protected') is not True:
        raise RuntimeError('canonical main lacks branch protection')
    commit = json_get('https://api.github.com/repos/' + REPOSITORY + '/commits/main', token)
    if branch.get('commit', {}).get('sha') != commit.get('sha'):
        raise RuntimeError('canonical main moved during verification')
    if commit['commit']['verification']['verified'] is not True:
        raise RuntimeError('main commit lacks verified signature')
    return commit['sha']


def source_files(revision):
    if not re.fullmatch('[0-9a-f]{40}', revision):
        raise ValueError('exact source revision required')
    files = {}
    entries = git('ls-tree', '-rz', revision, '--', PREFIX).split(b'\0')
    for entry in entries:
        if not entry:
            continue
        metadata, raw_path = entry.split(b'\t', 1)
        mode, kind, blob = metadata.split()
        name = raw_path.decode('utf-8')[len(PREFIX):]
        if kind != b'blob' or mode not in (b'100644', b'100755'):
            raise ValueError('non-regular source entry: ' + name)
        if (name != '.gitattributes' and any(part.startswith('.') for part in name.split('/'))) or '__pycache__' in name.split('/') or name.endswith('.pyc'):
            raise ValueError('unintended source entry: ' + name)
        files[name] = git('cat-file', 'blob', blob.decode())
    if not {'server.py','source_binding.py','catalog.py','index.html','vendor/three.module.min.js'}.issubset(files):
        raise ValueError('incomplete Cosmos source')
    return files


def publication_files(revision):
    files = source_files(revision)
    if 'COSMOS_SOURCE_BINDING.json' in files:
        raise ValueError('source must not contain a generated binding')
    # Replace the old archived-repository declaration; all other legacy files stay.
    files['hf-deploy-manifest.json'] = json.dumps({'schema':'szl.hf-deploy-manifest/v1','source_repository':REPOSITORY,'source_revision':revision,'source_path':'spaces/cosmos','destination':{'repo_id':SPACE,'repo_type':'space','visibility':'public','lifecycle':'PUBLIC_CREATIVE','mode':'creator-profile'}},sort_keys=True).encode()
    binding = {'schema':'szl.cosmos-source/v1','repository':REPOSITORY,'commit':revision,'source_path':'spaces/cosmos','destination':SPACE,'files':{p:hashlib.sha256(b).hexdigest() for p,b in sorted(files.items())}}
    files['COSMOS_SOURCE_BINDING.json'] = json.dumps(binding,sort_keys=True).encode()
    return files


def verify_files(api, revision, expected, download):
    observed = set(api.list_repo_files(SPACE, repo_type='space', revision=revision))
    if observed != set(expected):
        raise RuntimeError('publication output set mismatch: ' + repr(sorted(observed ^ set(expected))))
    for name, data in expected.items():
        if download(SPACE, name, revision) != data:
            raise RuntimeError('publication bytes mismatch: ' + name)


def verify_runtime(api, hf_revision, source_revision):
    info = api.space_info(SPACE)
    runtime = getattr(info, 'runtime', None)
    raw = getattr(runtime, 'raw', runtime) or {}
    # The provider runtime revision must be witnessed independently of Hub head.
    runtime_sha = raw.get('sha') if isinstance(raw, dict) else None
    if runtime_sha != hf_revision or raw.get('stage') != 'RUNNING':
        raise RuntimeError('provider runtime revision not witnessed')
    payload = json_get(LIVE + '/.well-known/szl-source.json?refresh=1')
    if payload.get('alignment_state') != 'SOURCE_BOUND_LOCAL_BYTES' or payload.get('source', {}).get('commit') != source_revision or payload['source'].get('repository') != REPOSITORY:
        raise RuntimeError('mounted source binding not witnessed')
    health = json_get(LIVE + '/healthz')
    if health.get('ok') is not True:
        raise RuntimeError('runtime health failed')
    catalog = json_get(LIVE + '/api/catalog')
    streams = {(owner, kind) for owner in ('SZLHOLDINGS', 'betterwithage') for kind in ('space', 'model', 'dataset')}
    sources = catalog.get('sources', [])
    if catalog.get('state') != 'FRESH' or len(sources) != 6 or {(s.get('owner'), s.get('kind')) for s in sources} != streams or any(s.get('state') != 'FRESH' for s in sources):
        raise RuntimeError('public catalog streams are not all fresh')
    if any(n.get('owner') not in ('SZLHOLDINGS','betterwithage') for n in catalog.get('nodes', [])):
        raise RuntimeError('public catalog namespace violation')
    return {'runtime_revision':runtime_sha,'source':payload,'health':health,'catalog':catalog}


def changed_files(api, parent, expected, download):
    remote = set(api.list_repo_files(SPACE, repo_type='space', revision=parent))
    if remote - set(expected):
        raise RuntimeError('unowned destination files require reconciliation before publication')
    return {name: data for name, data in expected.items()
            if name not in remote or download(SPACE, name, parent) != data}


def main():
    from huggingface_hub import CommitOperationAdd, HfApi, hf_hub_download
    token = os.environ['GITHUB_TOKEN']
    revision = os.environ['GITHUB_SHA']
    if os.environ.get('GITHUB_REPOSITORY') != REPOSITORY or os.environ.get('GITHUB_REF') != 'refs/heads/main' or main_head(token) != revision:
        raise RuntimeError('only current canonical protected main may publish')
    api = HfApi(token=os.environ['HF_TOKEN'])
    expected = publication_files(revision)
    info = api.space_info(SPACE)
    if info.private is not False:
        raise RuntimeError('destination is not explicitly public')
    parent = info.sha
    if not re.fullmatch('[0-9a-f]{40}', parent or '') or main_head(token) != revision:
        raise RuntimeError('publication precondition changed')
    def download(repo, name, sha):
        return Path(hf_hub_download(repo_id=repo, repo_type='space', filename=name, revision=sha,token=os.environ['HF_TOKEN'])).read_bytes()
    changed = changed_files(api, parent, expected, download)
    refreshed = api.space_info(SPACE)
    if refreshed.private is not False or refreshed.sha != parent or main_head(token) != revision:
        raise RuntimeError('publication precondition changed during comparison')
    target = api.create_commit(repo_id=SPACE, repo_type='space', parent_commit=parent, operations=[CommitOperationAdd(path_in_repo=p,path_or_fileobj=io.BytesIO(b)) for p,b in changed.items()], commit_message='Cosmos canonical source ' + revision).oid if changed else parent
    receipt = {'source_repository':REPOSITORY,'source_revision':revision,'hf_parent':parent,'hf_revision':target,'file_count':len(expected),'changed_file_count':len(changed),'noop':not changed,'file_parity':False,'runtime_verified':False}
    try:
        verify_files(api,target,expected,download)
        receipt['file_parity'] = True
        deadline = time.monotonic() + 600
        for attempt in range(40):
            try:
                receipt['runtime'] = verify_runtime(api,target,revision)
                receipt['runtime_verified'] = True
                break
            except Exception as exc:
                receipt['runtime_last_error_type'] = type(exc).__name__
                if attempt == 39 or time.monotonic() >= deadline:
                    raise
                time.sleep(15)
    finally:
        Path('cosmos-publication-receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k != 'runtime'}))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        receipt_path = Path('cosmos-publication-receipt.json')
        if not receipt_path.exists():
            receipt_path.write_text(json.dumps({'source_repository': REPOSITORY, 'source_revision': os.environ.get('GITHUB_SHA'), 'complete': False, 'error_type': type(exc).__name__}), encoding='utf-8')
        raise
