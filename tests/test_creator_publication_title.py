# SPDX-License-Identifier: Apache-2.0
"""Offline publisher-to-runtime contract, with the actual committed expressions.

No Hub client import, application boot, credential, network or provider write.
Fixtures supply transport responses only; the actual runtime verifier executes.
"""
from __future__ import annotations
import ast
import io
import json
from pathlib import Path
import threading
import time
from types import SimpleNamespace
import unittest
from urllib.request import Request

ROOT = Path(__file__).resolve().parents[1]
SOURCE = '075a2484c1e520d4e5767c1a2780de9bd8827e6c'
REVISION = 'b10f867535d319c36570c69fa7314fd8387fcfca'
RUN = '33934719242'


def publisher_title(source_revision: str, workflow_run_id: str) -> str:
    tree = ast.parse((ROOT / 'scripts/sync_hf_creator_profile.py').read_text(encoding='utf-8'))
    main = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main']
    if len(main) != 1:
        raise AssertionError('Publisher main must be unambiguous')
    calls = [node for node in ast.walk(main[0]) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Attribute) and node.func.attr == 'create_commit']
    if len(calls) != 1:
        raise AssertionError('Exactly one publisher commit call is required')
    titles = [keyword.value for keyword in calls[0].keywords if keyword.arg == 'commit_message']
    if len(titles) != 1 or not isinstance(titles[0], ast.JoinedStr):
        raise AssertionError('Publisher title must be an explicit source/run f-string')
    for node in ast.walk(titles[0]):
        if isinstance(node, ast.Name) and node.id not in {'source_revision', 'workflow_run_id'}:
            raise AssertionError('Unexpected publisher title input')
        if not isinstance(node, (ast.JoinedStr, ast.FormattedValue, ast.Constant, ast.Name, ast.Load)):
            raise AssertionError('Unexpected executable expression in publisher title')
    return eval(compile(ast.Expression(titles[0]), '<actual publisher title>', 'eval'),
                {'__builtins__': {}}, {'source_revision': source_revision, 'workflow_run_id': workflow_run_id})


class CreatorPublicationTitleTest(unittest.TestCase):
    def setUp(self):
        self.commits = [{'id': REVISION, 'title': publisher_title(SOURCE, RUN)}]
        self.diff = 'diff --git a/hf-deploy-manifest.json b/hf-deploy-manifest.json\n'
        self.manifest = {'schema': 'szl.hf-deploy-manifest/v1',
                         'source_repository': 'szl-holdings/anatomy',
                         'source_revision': SOURCE, 'workflow_run_id': RUN}
        self.requests = []
        self.fail_transport = False
        source = (ROOT / 'server.py').read_text(encoding='utf-8')
        names = {'_is_full_revision', '_hf_commit_matches_source'}
        nodes = [node for node in ast.parse(source).body
                 if isinstance(node, ast.FunctionDef) and node.name in names]
        self.assertEqual({node.name for node in nodes}, names)
        self.namespace = {'json': json, 'time': time, 'SOURCE_REPOSITORY': 'szl-holdings/anatomy',
                          '_binding_lock': threading.Lock(),
                          '_binding_cache': {'key': None, 'at': 0, 'value': False},
                          'urllib': SimpleNamespace(request=SimpleNamespace(Request=Request, urlopen=self.urlopen))}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), '<actual runtime verifier>', 'exec'), self.namespace)

    def urlopen(self, request, timeout):
        self.requests.append(request.full_url)
        self.assertEqual(timeout, 4)
        if self.fail_transport:
            raise TimeoutError('offline unavailable fixture')
        url = request.full_url
        if url == 'https://huggingface.co/api/spaces/betterwithage/anatomy/commits/main?limit=1':
            value = json.dumps(self.commits).encode()
        elif url == f'https://huggingface.co/spaces/betterwithage/anatomy/commit/{REVISION}.diff':
            value = self.diff.encode()
        elif url == f'https://huggingface.co/spaces/betterwithage/anatomy/resolve/{REVISION}/hf-deploy-manifest.json':
            value = json.dumps(self.manifest).encode()
        else:
            raise AssertionError('Unexpected verifier URL: ' + url)
        return io.BytesIO(value)

    def matches(self, revision=REVISION, source=SOURCE, run=RUN):
        return self.namespace['_hf_commit_matches_source'](revision, source, run, force=True)

    def test_actual_publisher_commit_is_accepted_by_the_unmodified_runtime(self):
        self.assertTrue(self.matches(), 'The committed publisher emits a title rejected by the runtime')
        self.assertEqual(len(self.requests), 3)

    def test_observed_broken_creator_profile_prefix_stays_rejected(self):
        self.commits[0]['title'] = f'hf-sync: creator profile source {SOURCE} run {RUN}'
        self.assertFalse(self.matches())

    def test_title_cannot_substitute_a_different_source_or_workflow(self):
        for title in (publisher_title('a' * 40, RUN), publisher_title(SOURCE, '123'), 'arbitrary publisher title'):
            with self.subTest(title=title):
                self.commits[0]['title'] = title
                self.assertFalse(self.matches())

    def test_repository_head_must_match_the_measured_deployment(self):
        self.commits[0]['id'] = 'a' * 40
        self.assertFalse(self.matches())

    def test_commit_must_include_the_manifest_change(self):
        self.diff = 'diff --git a/README.md b/README.md\n'
        self.assertFalse(self.matches())

    def test_deployed_manifest_must_match_repository_source_run_and_schema(self):
        for key, value in (('schema', 'wrong'), ('source_repository', 'foreign/repo'),
                           ('source_revision', 'a' * 40), ('workflow_run_id', '123')):
            with self.subTest(key=key):
                original = self.manifest[key]
                self.manifest[key] = value
                self.assertFalse(self.matches())
                self.manifest[key] = original

    def test_absent_commit_metadata_is_not_a_source_binding(self):
        self.commits = []
        self.assertFalse(self.matches())

    def test_transport_failure_is_unavailable_not_a_false_pass(self):
        self.fail_transport = True
        self.assertFalse(self.matches())

    def test_invalid_identity_inputs_fail_without_transport(self):
        for revision, source, run in (('main', SOURCE, RUN), (REVISION, 'unknown', RUN),
                                      (REVISION, SOURCE, ''), (REVISION, SOURCE, 123)):
            with self.subTest(revision=revision, source=source, run=run):
                self.assertFalse(self.matches(revision, source, run))
        self.assertEqual(self.requests, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
