"""Changes to executable, build and visible-style inputs must change the receipt."""
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import server


class RuntimeReceiptCoverageTest(unittest.TestCase):
    def test_runtime_and_build_inputs_are_hashed_and_tampering_changes_the_digest(self):
        critical = {"organ_integrity.py", "Dockerfile", "requirements.txt", "style.css", "favicon.svg"}
        self.assertTrue(critical.issubset(set(server.ARTIFACT_PATHS)))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in server.ARTIFACT_PATHS:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("original " + relative, encoding="utf-8")
            with mock.patch.object(server, "DIRECTORY", root):
                original = server._artifact_manifest()
                for relative in critical:
                    with self.subTest(path=relative):
                        target = root / relative
                        previous = target.read_bytes()
                        target.write_bytes(previous + b" changed")
                        self.assertNotEqual(original, server._artifact_manifest())
                        target.write_bytes(previous)
                self.assertEqual(original, server._artifact_manifest())


if __name__ == "__main__":
    unittest.main()
