from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCKED = ["F1", "F11", "F12", "F18", "F19"]
EXPERIMENTAL_NOT_LOCKED = ["F4", "F7", "F22"]
ACTIVE_SURFACES = (
    "README.md",
    "index.html",
    "data.js",
    "app.js",
    "v5_organs.js",
    "v6_alive.js",
    "server.py",
)


def _javascript_array(source: str, key: str) -> list[str]:
    match = re.search(rf"\b{re.escape(key)}\s*:\s*(\[[^\]]*\])", source)
    if match is None:
        raise AssertionError(f"missing JavaScript array: {key}")
    return list(ast.literal_eval(match.group(1)))


class FormulaTaxonomyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = (ROOT / "data.js").read_text(encoding="utf-8")
        cls.server = (ROOT / "server.py").read_text(encoding="utf-8")

    def test_browser_source_of_truth_has_exact_disjoint_sets(self) -> None:
        locked = _javascript_array(self.data, "locked_proven")
        experimental = _javascript_array(self.data, "experimental_not_locked")
        self.assertEqual(LOCKED, locked)
        self.assertEqual(EXPERIMENTAL_NOT_LOCKED, experimental)
        self.assertTrue(set(locked).isdisjoint(experimental))

    def test_experimental_formulas_cannot_be_promoted_by_copy(self) -> None:
        for formula_id in EXPERIMENTAL_NOT_LOCKED:
            pattern = rf"\b{formula_id}\s*:\s*\{{[^}}]*maturity:'EXPERIMENTAL'"
            self.assertRegex(self.data, pattern)
            self.assertNotRegex(
                self.data,
                rf"\b{formula_id}\s*:\s*\{{[^}}]*maturity:'LOCKED'",
            )

    def test_machine_contract_uses_the_same_sets(self) -> None:
        self.assertIn(f"LOCKED_FORMULAS = {LOCKED!r}".replace("'", '"'), self.server)
        self.assertIn(
            f"EXPERIMENTAL_NOT_LOCKED_FORMULAS = {EXPERIMENTAL_NOT_LOCKED!r}".replace("'", '"'),
            self.server,
        )

    def test_active_surfaces_reject_retired_locked_eight_claim(self) -> None:
        retired = re.compile(
            r"locked[- ]?8|8[ \t]+locked|exactly[ \t]+8|locked_count_eight|"
            r"F1[ \t]*,?[ \t]*F4[ \t]*,?[ \t]*F7[ \t]*,?[ \t]*F11",
            re.IGNORECASE,
        )
        for relative in ACTIVE_SURFACES:
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIsNone(retired.search(source), relative)

    def test_public_surfaces_name_the_boundary(self) -> None:
        for relative in ("README.md", "index.html", "data.js", "app.js"):
            source = (ROOT / relative).read_text(encoding="utf-8")
            self.assertIn("EXPERIMENTAL / NOT LOCKED", source, relative)
        self.assertIn("{F1,F11,F12,F18,F19}", self.data)


if __name__ == "__main__":
    unittest.main(verbosity=2)
