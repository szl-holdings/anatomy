from pathlib import Path
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
