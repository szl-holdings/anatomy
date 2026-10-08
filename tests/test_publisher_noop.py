from pathlib import Path
import ast
import copy
from typing import Any
import unittest


PUBLISHER = Path("scripts/sync_hf_creator_profile.py")


class PublisherNoopContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.source = PUBLISHER.read_text(encoding="utf-8")

    def test_noop_comparison_is_exact_and_source_owned(self) -> None:
        for contract in (
            "def live_deploy_manifest()",
            "def deployment_inputs_match(",
            'observed.get("source_revision") != desired.get("source_revision")',
            'observed_destination.get(key) != desired_destination.get(key)',
            'observed_brain.get(key) == desired_brain.get(key)',
            '"frontier_candidate_set_sha256"',
            '"formula_counts"',
            '"quant_domain_count"',
            '"training_authority"',
            '"execution_authority"',
        ):
            self.assertIn(contract, self.source)

    def test_noop_preserves_revision_and_reverifies_live(self) -> None:
        for contract in (
            "if deployment_inputs_match(observed_manifest, deploy_manifest):",
            'current_sha = str(getattr(info, "sha", "") or "")',
            "wait_running(api, current_sha)",
            "verify_live(",
            "observed_run_id",
            "return",
        ):
            self.assertIn(contract, self.source)
        noop_index = self.source.index(
            "if deployment_inputs_match(observed_manifest, deploy_manifest):"
        )
        commit_index = self.source.index("api.create_commit(")
        self.assertLess(noop_index, commit_index)

    def test_workflow_run_id_is_not_an_immutable_input(self) -> None:
        function = self.source.split(
            "def deployment_inputs_match(",
            1,
        )[1].split("def wait_running", 1)[0]
        self.assertNotIn('observed.get("workflow_run_id")', function)
        self.assertNotIn('desired.get("workflow_run_id")', function)

    def test_new_admitted_pipeline_inputs_invalidate_publication_noop(self) -> None:
        tree = ast.parse(self.source)
        function = next(node for node in tree.body
                        if isinstance(node, ast.FunctionDef) and node.name == "deployment_inputs_match")
        namespace = {"Any": Any}
        exec(compile(ast.Module(body=[function], type_ignores=[]), "<no-op predicate>", "exec"), namespace)
        match = namespace["deployment_inputs_match"]
        manifest = {"schema": "szl.hf-deploy-manifest/v1", "source_repository": "szl-holdings/anatomy",
                    "source_revision": "a" * 40, "destination": {"repo_id": "betterwithage/anatomy"},
                    "dependencies": {"second_brain": {"source_revision": "b" * 40,
                        "pipeline_dependency": {"source_repository": "szl-holdings/a11oy",
                            "source_revision": "c" * 40, "source_snapshot_sha256": "d" * 64}}}}
        self.assertTrue(match(manifest, copy.deepcopy(manifest)))
        changed = copy.deepcopy(manifest)
        changed["dependencies"]["second_brain"]["pipeline_dependency"]["source_snapshot_sha256"] = "e" * 64
        self.assertFalse(match(manifest, changed))
        changed = copy.deepcopy(manifest)
        changed["dependencies"]["second_brain"]["capture_time"] = "new observation time"
        self.assertTrue(match(manifest, changed), "capture time alone must not force a rebuild")


if __name__ == "__main__":
    unittest.main(verbosity=2)
