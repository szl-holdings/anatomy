# SPDX-License-Identifier: Apache-2.0
"""Run modal-focus JavaScript regressions in the existing unittest CI lane."""
from pathlib import Path
import shutil
import subprocess
import unittest


class ModalFocusContract(unittest.TestCase):
    def test_source_focus_behaviors(self):
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node is required by the existing frontend CI contract")
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [node, "--test", str(root / "tests" / "test_modal_focus.cjs")],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
