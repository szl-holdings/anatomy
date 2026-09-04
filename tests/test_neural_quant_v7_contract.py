from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"
SCRIPT = ROOT / "neural-quant-v7.js"
STYLE = ROOT / "neural-quant-v7.css"
SERVER = ROOT / "server.py"
LIVING_RUNTIME = ROOT / "living_runtime.py"
BRAIN_RUNTIME = ROOT / "second_brain_runtime.py"
MATERIALIZER = ROOT / "scripts" / "materialize_second_brain.py"


class NeuralQuantV7ContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = INDEX.read_text(encoding="utf-8")
        cls.script = SCRIPT.read_text(encoding="utf-8")
        cls.style = STYLE.read_text(encoding="utf-8")
        cls.server = SERVER.read_text(encoding="utf-8")
        cls.living = LIVING_RUNTIME.read_text(encoding="utf-8")
        cls.brain = BRAIN_RUNTIME.read_text(encoding="utf-8")
        cls.materializer = MATERIALIZER.read_text(encoding="utf-8")

    def test_v7_assets_are_mounted_once(self) -> None:
        self.assertEqual(1, self.index.count('href="./neural-quant-v7.css"'))
        self.assertEqual(1, self.index.count('src="./neural-quant-v7.js"'))
        self.assertIn('"neural-quant-v7.js"', self.living)
        self.assertIn('"neural-quant-v7.css"', self.living)
        self.assertIn('"neural-quant-v7.js"', self.server)
        self.assertIn('"neural-quant-v7.css"', self.server)

    def test_frontend_uses_only_the_same_origin_v7_api(self) -> None:
        self.assertIn(
            'const ENDPOINT = "/api/anatomy/v1/brain/neural-quant-v7?k=24";',
            self.script,
        )
        self.assertIn("credentials: \"same-origin\"", self.script)
        self.assertIn("cache: \"no-store\"", self.script)
        self.assertNotIn("raw.githubusercontent.com", self.script)
        self.assertNotIn("huggingface.co/api", self.script)
        self.assertNotIn("eval(", self.script)
        self.assertNotIn("new Function", self.script)
        self.assertNotIn("innerHTML", self.script)
        self.assertIn("textContent", self.script)

    def test_frontend_enforces_handles_only_and_fail_closed_state(self) -> None:
        for contract in (
            'serialized.includes(\'"content"\')',
            'serialized.includes(\'"text"\')',
            'throw new Error("handles-only boundary failed")',
            '"The source-bound request failed."',
            '"No green synthesized"',
            '"Authority none"',
            '"Λ Conjecture 1"',
        ):
            self.assertIn(contract, self.script)

    def test_v7_has_accessible_desktop_and_mobile_controls(self) -> None:
        for contract in (
            'setAttribute("role", "dialog")',
            'setAttribute("aria-modal", "true")',
            'setAttribute("aria-labelledby", "nq7-title")',
            'event.key === "Escape"',
            'event.key !== "Tab"',
            "focusableNodes()",
            'setAttribute("role", "tablist")',
            'setAttribute("role", "tabpanel")',
        ):
            self.assertIn(contract, self.script)
        for contract in (
            "min-height: 44px",
            "env(safe-area-inset-bottom)",
            "@media (max-width: 720px)",
            "@media (prefers-reduced-motion: reduce)",
            "@media (prefers-contrast: more)",
            "@media (forced-colors: active)",
        ):
            self.assertIn(contract, self.style)
        self.assertNotRegex(self.style.lower(), r"purple|violet|magenta")

    def test_backend_exposes_all_v7_observation_routes(self) -> None:
        for route in (
            "/api/anatomy/v1/brain/frontier",
            "/api/anatomy/v1/brain/formulas",
            "/api/anatomy/v1/brain/quant",
            "/api/anatomy/v1/brain/ouroboros",
            "/api/anatomy/v1/brain/neural-quant-v7",
        ):
            self.assertIn(route, self.living)
            self.assertIn(route, self.brain)
        self.assertIn('path.startswith("/.runtime/")', self.living)
        self.assertIn('"BLOCKED_INTERNAL_RUNTIME_PATH"', self.living)

    def test_materializer_replays_formula_quant_and_authority_boundaries(self) -> None:
        for contract in (
            "EXPECTED_ATTRIBUTED_FORMULAS = 30",
            "EXPECTED_EXECUTABLE_FORMULAS = 21",
            "EXPECTED_QUANT_DOMAINS = 9",
            "EXPECTED_LOCKED_PROVEN = 8",
            '"UNKNOWN_NOT_INFERRED"',
            '"CONJECTURE_1_OPEN_ADVISORY_ONLY"',
            '"training_authority": "NONE"',
            '"promotion_authority": "NONE"',
            '"execution_authority": "NONE"',
            '"merge_authority": "NONE"',
            '"private_graph_nodes_materialized": 0',
        ):
            self.assertIn(contract, self.materializer)

    def test_script_has_no_unbounded_render_or_duplicate_mount(self) -> None:
        self.assertIn('if (document.getElementById(PANEL_ID)) return;', self.script)
        self.assertIn("domains.slice(0, 9)", self.script)
        self.assertIn("slice(0, 28)", self.script)
        self.assertIn("Math.max(1, domains.length)", self.script)
        self.assertTrue(
            re.search(r"window\.setTimeout\(\(\) => state\.abortController\.abort\(\), 12000\)", self.script)
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
