"""Guard: every pytest-style test module must run in PR CI and the deploy gate.

``python -m unittest discover`` only collects ``unittest.TestCase`` methods.
Module-level ``def test_*`` functions are silently skipped by it, which is how
a stale assertion once reached main without any pull-request check failing.
This test fails if such a module exists but is not named in the explicit
pytest step of the PR gate (container-contract.yml) and the deploy gate
(hf-sync.yml).
"""

from __future__ import annotations

import ast
from pathlib import Path
import unittest


TESTS = Path("tests")
GATES = (
    Path(".github/workflows/container-contract.yml"),
    Path(".github/workflows/hf-sync.yml"),
)


def pytest_style_modules() -> list[Path]:
    modules = []
    for path in sorted(TESTS.glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        if any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test")
            for node in tree.body
        ):
            modules.append(path)
    return modules


class CiCollectsPytestModulesTest(unittest.TestCase):
    def test_scan_finds_known_pytest_modules(self) -> None:
        names = {path.name for path in pytest_style_modules()}
        # Sanity check that the scan itself works; not an exhaustive list.
        self.assertIn("test_frontier_runtime.py", names)
        self.assertIn("test_holographic_v7_contract.py", names)

    def test_every_pytest_style_module_runs_in_each_gate(self) -> None:
        modules = pytest_style_modules()
        for gate in GATES:
            workflow = gate.read_text(encoding="utf-8")
            self.assertIn("python -m pytest", workflow, gate)
            for module in modules:
                self.assertTrue(
                    module.as_posix() in workflow,
                    f"{module.as_posix()} has module-level test functions that "
                    f"unittest discover never runs; add it to the pytest step "
                    f"in {gate.as_posix()}",
                )


if __name__ == "__main__":
    unittest.main()
