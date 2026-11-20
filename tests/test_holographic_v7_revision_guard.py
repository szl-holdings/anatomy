# SPDX-License-Identifier: Apache-2.0
"""Offline negative controls for the exact Holographic v7 revision witness.

The test runs no provider calls and grants no deployment or training authority.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.holo_revision_identity import is_sha40, is_sha256


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
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
    ],
)
def test_hf_and_second_brain_revision_strict(candidate: object, expected: bool) -> None:
    assert is_sha40(candidate) is expected


@pytest.mark.parametrize(
    ("candidate", "expected"),
    [
        ("f" * 64, True),
        ("g" * 64, False),
        ("F" * 64, False),
        (" " * 64, False),
        ("f" * 63, False),
        ("f" * 64 + "\n", False),
        (["f"] * 64, False),
        (None, False),
    ],
)
def test_candidate_set_digest_strict(candidate: object, expected: bool) -> None:
    assert is_sha256(candidate) is expected


def test_live_witness_uses_rejecting_predicates_for_all_three_bindings() -> None:
    root = Path(__file__).resolve().parents[1]
    workflow = (root / ".github/workflows/holographic-v7-live-witness.yml").read_text(
        encoding="utf-8"
    )
    assert workflow.count(
        "from scripts.holo_revision_identity import is_sha40, is_sha256"
    ) == 1
    assert workflow.count("assert is_sha40(hf_revision)") == 1
    assert workflow.count('assert is_sha40(status["second_brain_source_revision"])') == 1
    assert workflow.count('assert is_sha256(status["candidate_set_sha256"])') == 1
    assert 'assert isinstance(hf_revision, str) and len(hf_revision) == 40' not in workflow
    assert 'assert len(status["second_brain_source_revision"]) == 40' not in workflow
    assert 'assert len(status["candidate_set_sha256"]) == 64' not in workflow
    # The PR event runs the zero-authority contract; it cannot run the
    # read-only network witness or any deployment/action authorization.
    assert "pull_request:" in workflow
    assert "if: github.event_name != 'pull_request'" in workflow
    assert "tests/test_holographic_v7_revision_guard.py" in workflow
