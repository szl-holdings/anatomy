import json
import tempfile
import unittest
from pathlib import Path

from lib.refinement_contract import (
    RefinementProjectionError,
    canonical_bytes,
    filter_handles,
    load_projection,
    sha256_hex,
    validate_projection,
)

ROOT = Path(__file__).resolve().parents[1]


def projection_fixture(*, available: bool) -> tuple[dict, dict]:
    """Build synthetic metadata without depending on a materialized source."""
    handles = []
    if available:
        handles.append(
            {
                "schema": "szl.second-brain.refinement-pattern-handle/v1",
                "id": "refinement:synthetic-fixture",
                "sha256": "1" * 64,
                "model_pair_sha256": "2" * 64,
                "error_code": "FIXTURE_ERROR",
                "verified_repair_rate": 0.5,
                "regression_rate": 0.0,
                "mean_audit_confidence": 0.75,
            }
        )
    state = {
        "schema": "szl.second-brain.refinement-memory/v1",
        "ready": True,
        "content_access": "HANDLES_ONLY",
        "private_graph_present": False,
        "raw_reasoning_present": False,
        "training_authority": "NONE",
        "promotion_authority": "NONE",
        "execution_authority": "NONE",
        "merge_authority": "NONE",
        "pattern_count": len(handles),
        "handles": handles,
    }
    state["state_sha256"] = sha256_hex(canonical_bytes(state))
    source = {
        "schema": "szl.anatomy.refinement-source/v1",
        "source_repository": "szl-holdings/szl-second-brain",
        "source_path": "data/refinement-patterns.public.json",
        "source_revision": "a" * 40 if available else None,
        "available": available,
        "state_sha256": state["state_sha256"],
        "source_content_sha256": sha256_hex(canonical_bytes(state)),
        "content_access": "HANDLES_ONLY",
        "training_authority": "NONE",
        "promotion_authority": "NONE",
        "execution_authority": "NONE",
    }
    source["receipt_sha256"] = sha256_hex(canonical_bytes(source))
    return state, source


class RefinementObservatoryContractTests(unittest.TestCase):
    def test_local_projection_is_bound_and_handles_only(self) -> None:
        # The publisher materializes these paths before running this suite.
        # Both available and unavailable source receipts are valid contracts.
        state, source = load_projection(
            ROOT / "lib/refinement_patterns.public.json",
            ROOT / "lib/refinement_source.json",
        )
        self.assertEqual(state["content_access"], "HANDLES_ONLY")
        self.assertIsInstance(source["available"], bool)
        self.assertEqual(source["state_sha256"], state["state_sha256"])
        self.assertEqual(filter_handles(state), state["handles"][:50])

    def test_available_and_unavailable_projections_load(self) -> None:
        for available in (False, True):
            with self.subTest(available=available), tempfile.TemporaryDirectory() as tmp:
                state, source = projection_fixture(available=available)
                state_path = Path(tmp) / "state.json"
                source_path = Path(tmp) / "source.json"
                state_path.write_text(json.dumps(state), encoding="utf-8")
                source_path.write_text(json.dumps(source), encoding="utf-8")
                loaded_state, loaded_source = load_projection(state_path, source_path)
                self.assertEqual((loaded_state, loaded_source), (state, source))
                self.assertIs(loaded_source["available"], available)
                self.assertEqual(len(filter_handles(loaded_state)), int(available))

    def test_available_source_requires_exact_revision(self) -> None:
        for revision in (None, "", "main", "a" * 39):
            with self.subTest(revision=revision):
                state, source = projection_fixture(available=True)
                source["source_revision"] = revision
                source.pop("receipt_sha256")
                source["receipt_sha256"] = sha256_hex(canonical_bytes(source))
                with self.assertRaisesRegex(RefinementProjectionError, "revision is not exact"):
                    validate_projection(state, source)

    def test_digest_tamper_is_rejected(self) -> None:
        state, source = projection_fixture(available=True)
        state["pattern_count"] = 9
        with self.assertRaisesRegex(RefinementProjectionError, "digest mismatch"):
            validate_projection(state, source)

    def test_private_content_key_is_rejected_recursively(self) -> None:
        state, source = projection_fixture(available=True)
        state["hidden_reasoning"] = "forbidden"
        with self.assertRaisesRegex(RefinementProjectionError, "forbidden"):
            validate_projection(state, source)

    def test_frontend_is_local_responsive_and_no_external_runtime(self) -> None:
        html = (ROOT / "refinement-lab.html").read_text(encoding="utf-8")
        js = (ROOT / "refinement-lab.js").read_text(encoding="utf-8")
        css = (ROOT / "refinement-lab.css").read_text(encoding="utf-8")
        self.assertIn("Alloy Refinement Observatory", html)
        self.assertIn("/api/anatomy/v1/refinement/status", js)
        self.assertIn("textContent", js)
        self.assertNotIn("innerHTML", js)
        self.assertIn("@media(max-width:480px)", css)
        self.assertNotIn("https://", html + js + css)


if __name__ == "__main__":
    unittest.main()
