import json
import tempfile
import unittest
from pathlib import Path

from lib.refinement_contract import (
    RefinementProjectionError,
    filter_handles,
    load_projection,
    validate_projection,
)

ROOT = Path(__file__).resolve().parents[1]


class RefinementObservatoryContractTests(unittest.TestCase):
    def test_checked_in_projection_is_bound_and_handles_only(self) -> None:
        state, source = load_projection(
            ROOT / "lib/refinement_patterns.public.json",
            ROOT / "lib/refinement_source.json",
        )
        self.assertEqual(state["content_access"], "HANDLES_ONLY")
        self.assertFalse(source["available"])
        self.assertEqual(filter_handles(state), [])

    def test_digest_tamper_is_rejected(self) -> None:
        state = json.loads(
            (ROOT / "lib/refinement_patterns.public.json").read_text(encoding="utf-8")
        )
        source = json.loads(
            (ROOT / "lib/refinement_source.json").read_text(encoding="utf-8")
        )
        state["pattern_count"] = 9
        with self.assertRaisesRegex(RefinementProjectionError, "digest mismatch"):
            validate_projection(state, source)

    def test_private_content_key_is_rejected_recursively(self) -> None:
        state = json.loads(
            (ROOT / "lib/refinement_patterns.public.json").read_text(encoding="utf-8")
        )
        source = json.loads(
            (ROOT / "lib/refinement_source.json").read_text(encoding="utf-8")
        )
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
