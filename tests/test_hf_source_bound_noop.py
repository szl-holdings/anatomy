"""Fail-closed checks for reusing a published Hugging Face revision."""

import inspect
import unittest
from types import SimpleNamespace

from scripts.sync_hf_creator_profile import main, reusable_hf_head


REV = "a" * 40
SOURCE = "b" * 40
RUN = "44657609763"


class StubHub:
    def __init__(self, commit_id=REV, title=None, empty=False, error=None):
        self.commit_id = commit_id
        self.title = title if title is not None else f"hf-sync: source {SOURCE} run {RUN}"
        self.empty = empty
        self.error = error
        self.calls = []

    def list_repo_commits(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        if self.empty:
            return []
        return [SimpleNamespace(commit_id=self.commit_id, title=self.title)]


class SourceBoundNoopTests(unittest.TestCase):
    def test_exact_published_head_can_be_reused(self):
        hub = StubHub()
        self.assertTrue(reusable_hf_head(hub, REV, SOURCE, RUN))
        self.assertEqual(hub.calls, [
            {"repo_id": "SZLHOLDINGS/anatomy", "repo_type": "space", "revision": REV}
        ])

    def test_unrelated_commit_on_head_must_republish(self):
        hub = StubHub(title="SZL estate showcase card (weaver)")
        self.assertFalse(reusable_hf_head(hub, REV, SOURCE, RUN))

    def test_wrong_source_or_workflow_run_must_republish(self):
        hub = StubHub()
        self.assertFalse(reusable_hf_head(hub, REV, "c" * 40, RUN))
        self.assertFalse(reusable_hf_head(hub, REV, SOURCE, "999"))

    def test_commit_identity_mismatch_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "does not match"):
            reusable_hf_head(StubHub(commit_id="c" * 40), REV, SOURCE, RUN)

    def test_empty_commit_metadata_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, "no commit metadata"):
            reusable_hf_head(StubHub(empty=True), REV, SOURCE, RUN)

    def test_commit_metadata_transport_failure_fails_closed(self):
        with self.assertRaises(OSError):
            reusable_hf_head(StubHub(error=OSError("unavailable")), REV, SOURCE, RUN)

    def test_publisher_noop_path_rechecks_exact_head(self):
        source = inspect.getsource(main)
        self.assertIn("reuse_inputs = reusable_hf_head(", source)
        self.assertIn("if reuse_inputs:", source)


if __name__ == "__main__":
    unittest.main()
