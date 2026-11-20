# SPDX-License-Identifier: Apache-2.0
"""Offline negative controls for the exact Holographic v7 revision witness.

Standard-library unittest: both global container CI and focused pytest can
execute these checks without a new Python dependency, provider call, or model.
"""
from __future__ import annotations

from pathlib import Path
import unittest

from scripts.holo_revision_identity import is_sha40, is_sha256


class HolographicV7RevisionIdentityTests(unittest.TestCase):
    def test_hf_and_second_brain_revision_strict(self) -> None:
        samples = (
            ("a" * 40, True),
            ("0123456789abcdef" * 2 + "01234567", True),
            ("g" * 40, False),
            ("A" * 40, False),
            ("!" * 40, False),
            ("０" * 40, False),
            ("a" * 39, False),
            ("a" * 40 + "\n", False),
            (["a"] * 40, False),
            (40, False),
            (None, False),
        )
        for candidate, expected in samples:
            with self.subTest(value_type=type(candidate).__name__, expected=expected):
                self.assertIs(is_sha40(candidate), expected)

    def test_candidate_set_digest_strict(self) -> None:
        samples = (
            ("f" * 64, True),
            ("g" * 64, False),
            ("F" * 64, False),
            (" " * 64, False),
            ("f" * 63, False),
            ("f" * 64 + "\n", False),
            (["f"] * 64, False),
            (None, False),
        )
        for candidate, expected in samples:
            with self.subTest(value_type=type(candidate).__name__, expected=expected):
                self.assertIs(is_sha256(candidate), expected)

    def test_live_witness_wires_all_three_strict_checks(self) -> None:
        root = Path(__file__).resolve().parents[1]
        workflow = (
            root / ".github/workflows/holographic-v7-live-witness.yml"
        ).read_text(encoding="utf-8")
        self.assertEqual(
            1,
            workflow.count(
                "from scripts.holo_revision_identity import is_sha40, is_sha256"
            ),
        )
        self.assertEqual(1, workflow.count("assert is_sha40(hf_revision)"))
        self.assertEqual(
            1,
            workflow.count('assert is_sha40(status["second_brain_source_revision"])'),
        )
        self.assertEqual(
            1,
            workflow.count('assert is_sha256(status["candidate_set_sha256"])'),
        )
        self.assertNotIn(
            'assert isinstance(hf_revision, str) and len(hf_revision) == 40',
            workflow,
        )
        self.assertNotIn(
            'assert len(status["second_brain_source_revision"]) == 40',
            workflow,
        )
        self.assertNotIn('assert len(status["candidate_set_sha256"]) == 64', workflow)
        # On PR events only the zero-authority contract job may execute.
        self.assertIn("pull_request:", workflow)
        self.assertIn("if: github.event_name != 'pull_request'", workflow)
        self.assertIn("tests/test_holographic_v7_revision_guard.py", workflow)


if __name__ == "__main__":
    unittest.main()
