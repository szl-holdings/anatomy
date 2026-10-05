# SPDX-License-Identifier: Apache-2.0
"""Published runtime files must not link or probe retired Hugging Face Spaces."""

import glob
import os
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Absent from the Hub (checked 2026-09-29). Dated history elsewhere may keep them;
# the Space bundle this repository publishes may not.
RETIRED = (
    "SZLHOLDINGS/governed-receipt-verifier",
    "szlholdings-governed-receipt-verifier.static.hf.space",
    "szlholdings-hatun-mcp.hf.space",
    "SZLHOLDINGS/holographic)",
    'SZLHOLDINGS/holographic"',
    "szlholdings-holographic.hf.space",
    "SZLHOLDINGS/cosmos",
    "SZLHOLDINGS/sda)",
    "szlholdings-anatomy.hf.space",
)

# Same selection as scripts/sync_hf_creator_profile.py runtime_files(), minus the
# materialized .runtime tree, which is generated at publish time.
PATTERNS = (
    "README.md", "Dockerfile", "requirements.txt", "server.py", "organ_integrity.py",
    "living_runtime.py", "frontier_runtime.py", "frontier_source_contract.py", "second_brain_runtime.py",
    "scripts/materialize_second_brain.py", "*.html", "*.js", "*.css", "lib/**/*",
)


class RetiredSpaceReferenceTests(unittest.TestCase):
    def test_published_runtime_names_no_retired_space(self):
        cwd = os.getcwd()
        os.chdir(ROOT)
        try:
            files = sorted({path for pattern in PATTERNS
                            for path in glob.glob(pattern, recursive=True)
                            if os.path.isfile(path)})
        finally:
            os.chdir(cwd)
        self.assertIn("server.py", files)
        self.assertIn("frontier_anatomy.js", files)
        offenders = []
        for relative in files:
            text = (ROOT / relative).read_text(encoding="utf-8", errors="replace")
            offenders.extend(f"{relative}: {needle}" for needle in RETIRED if needle in text)
        self.assertEqual([], offenders)


if __name__ == "__main__":
    unittest.main()
