# SPDX-License-Identifier: Apache-2.0
"""Source identity and evidence boundaries for the read-only pipeline inspector."""
from __future__ import annotations

import unittest

import test_second_brain_runtime as fixtures
from second_brain_runtime import PublicSecondBrain


class PipelineObservationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = fixtures.PublicSecondBrainTest()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)

    def _maintained_snapshot(self) -> PublicSecondBrain:
        state, rows = self.fixture._frontier_fixture()
        for source in state["sources"]:
            if source["source_id"] == "ouroboros_runtime":
                source["repository"] = "szl-holdings/szl-ouroboros"
        for row in rows:
            if row["source_repository"] == "szl-holdings/ouroboros":
                row["source_repository"] = "szl-holdings/szl-ouroboros"
        self.fixture._rewrite_frontier(state, rows)
        return PublicSecondBrain(self.fixture.snapshot)

    def test_maintained_ouroboros_identity_returns_its_actual_handles(self) -> None:
        brain = self._maintained_snapshot()
        self.assertTrue(brain.ready)
        observed = brain.ouroboros_view()
        self.assertTrue(observed["ready"])
        self.assertTrue(observed["handles"])
        self.assertEqual("szl-holdings/szl-ouroboros", observed["source"]["repository"])
        self.assertTrue(all(handle["sourceRepository"] == "szl-holdings/szl-ouroboros"
                            for handle in observed["handles"]))

    def test_metadata_cannot_assert_runtime_termination_or_receipt_closure(self) -> None:
        observed = self._maintained_snapshot().ouroboros_view()
        self.assertEqual("SOURCE_METADATA_ONLY", observed["observation_state"])
        for name in ("bounded", "terminating", "receipt_closed"):
            with self.subTest(measurement=name):
                self.assertIsNone(observed["loop_contract"][name])
                self.assertIs(observed["contract_requirements"][name], True)
        self.assertEqual("UNAVAILABLE", observed["runtime_evidence"]["state"])
        self.assertIsNone(observed["runtime_evidence"]["receipt_sha256"])
        self.assertFalse(observed["loop_contract"]["recommendations_executed"])

    def test_missing_ouroboros_source_does_not_borrow_unrelated_handles(self) -> None:
        state, rows = self.fixture._frontier_fixture()
        for source in state["sources"]:
            if source["source_id"] == "ouroboros_runtime":
                source["source_id"] = "unrelated_source"
        self.fixture._rewrite_frontier(state, rows)
        brain = PublicSecondBrain(self.fixture.snapshot)
        self.assertTrue(brain.ready)
        observed = brain.ouroboros_view()
        self.assertFalse(observed["ready"])
        self.assertEqual("UNAVAILABLE", observed["observation_state"])
        self.assertEqual([], observed["handles"])
        self.assertIsNone(observed["loop_contract"]["receipt_closed"])

    def test_unavailable_snapshot_never_claims_runtime_success(self) -> None:
        (self.fixture.snapshot / "brain-corpus.public.jsonl").write_text("corrupt")
        observed = PublicSecondBrain(self.fixture.snapshot).ouroboros_view()
        self.assertFalse(observed["ready"])
        self.assertIsNone(observed["loop_contract"]["bounded"])
        self.assertIsNone(observed["loop_contract"]["terminating"])
        self.assertIsNone(observed["loop_contract"]["receipt_closed"])


if __name__ == "__main__":
    unittest.main()
