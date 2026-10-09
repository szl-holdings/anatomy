# SPDX-License-Identifier: Apache-2.0
"""Execute the v7 client and require every tab aria-controls target to exist."""

from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "tests" / "holographic_v7_tab_dom.mjs"


class HolographicV7TabDomTests(unittest.TestCase):
    def test_every_tab_controls_a_real_panel_and_keyboard_selection(self) -> None:
        node = shutil.which("node")
        self.assertIsNotNone(node, "node is required to execute the v7 DOM relationship")
        result = subprocess.run(
            [node, str(HARNESS)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertTrue(report["everyTargetExists"])
        self.assertTrue(report["orphanPanelAbsent"])
        self.assertEqual(
            [item["controls"] for item in report["controls"]],
            [
                "szl-v7-panel-brain",
                "szl-v7-panel-formulas",
                "szl-v7-panel-quant",
                "szl-v7-panel-loops",
            ],
        )
        self.assertTrue(all(item["targetExists"] for item in report["controls"]))
        selected = [item for item in report["afterRight"] if item["selected"] == "true"]
        self.assertEqual([item["id"] for item in selected], ["szl-v7-tab-formulas"])
        self.assertEqual(selected[0]["panelLabel"], "szl-v7-tab-formulas")
        self.assertFalse(selected[0]["panelHidden"])
        self.assertTrue(report["homeSelected"])


if __name__ == "__main__":
    unittest.main()
