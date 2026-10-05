"""Verify the shared validator is shipped, receipted, and usable by the CLI."""
import ast
import glob
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import chdir
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


class FrontierSourcePackagingTest(unittest.TestCase):
    def test_publisher_requires_and_uploads_the_validator(self):
        # Exercise the publisher's actual pure file-selection function without
        # importing a Hub client or invoking a publication boundary.
        tree = ast.parse((ROOT / "scripts/sync_hf_creator_profile.py").read_text())
        function = next(node for node in tree.body
                        if isinstance(node, ast.FunctionDef) and node.name == "runtime_files")
        namespace = {"glob": glob, "os": os}
        exec(compile(ast.Module(body=[function], type_ignores=[]), "<publisher files>", "exec"), namespace)
        required = (
            "README.md", "Dockerfile", "requirements.txt", "server.py", "living_runtime.py",
            "organ_integrity.py", "style.css", "favicon.svg", "frontier_runtime.py",
            "frontier_source_contract.py", "second_brain_runtime.py", "neural-quant-v7.js",
            "neural-quant-v7.css", "holographic-v7.js", "holographic-v7.css",
            "refinement-lab.html", "refinement-lab.js", "refinement-lab.css",
            "lib/refinement_contract.py", "lib/refinement_living_runtime.py",
            "lib/refinement_patterns.public.json", "lib/refinement_source.json",
            "scripts/materialize_refinement_memory.py",
            ".runtime/second-brain/manifest.json", ".runtime/second-brain/brain-corpus.public.jsonl",
            ".runtime/second-brain/frontier-state.v1.json",
            ".runtime/second-brain/frontier-candidates.public.jsonl", ".runtime/second-brain/source.json",
        )
        with tempfile.TemporaryDirectory() as directory, chdir(directory):
            for name in required:
                path = Path(name)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("fixture")
            self.assertIn("frontier_source_contract.py", namespace["runtime_files"]())
            Path("frontier_source_contract.py").unlink()
            with self.assertRaisesRegex(RuntimeError, "frontier_source_contract.py"):
                namespace["runtime_files"]()

    def test_validator_is_in_the_live_artifact_receipt(self):
        import living_runtime

        server = living_runtime.anatomy_server
        self.assertIn("frontier_source_contract.py", server.ARTIFACT_PATHS)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in server.ARTIFACT_PATHS:
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("original")
            with patch.object(server, "DIRECTORY", root):
                receipt = server._artifact_manifest()
                (root / "frontier_source_contract.py").write_text("changed validator")
                self.assertNotEqual(receipt, server._artifact_manifest())

    def test_materializer_cli_imports_validator_outside_repository_cwd(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, "-I", str(ROOT / "scripts/materialize_second_brain.py"), "--help"],
                cwd=directory, capture_output=True, text=True, timeout=10, check=False,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("--output", result.stdout)
