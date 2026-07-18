from pathlib import Path
import unittest


WORKFLOW = Path(".github/workflows/hf-sync.yml")


class HfSyncContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_runtime_files_are_in_trigger_and_upload_contract(self) -> None:
        for path in ("Dockerfile", ".dockerignore", "server.py"):
            self.assertGreaterEqual(self.workflow.count(f'"{path}"'), 2, path)

    def test_release_tooling_is_exactly_pinned(self) -> None:
        self.assertIn("huggingface_hub==1.23.0", self.workflow)
        self.assertNotIn("huggingface_hub>=", self.workflow)

    def test_release_waits_for_exact_live_revision(self) -> None:
        self.assertIn("info.sha == target_sha", self.workflow)
        self.assertIn('stage == "RUNNING"', self.workflow)
        self.assertIn('"BUILD_ERROR"', self.workflow)
        self.assertIn('/.well-known/szl-source.json?refresh=1', self.workflow)
        self.assertIn('source["deployment"]["hf_revision"] == target_sha', self.workflow)

    def test_release_verifies_public_health(self) -> None:
        self.assertIn('base + "/healthz"', self.workflow)
        self.assertIn('health["transport_state"] == "REACHABLE"', self.workflow)
        self.assertIn('health["verification_state"] == "STRUCTURAL_ONLY"', self.workflow)

    def test_stale_space_only_docker_claim_is_absent(self) -> None:
        self.assertNotIn("does not exist in this repo", self.workflow)
        self.assertNotIn("Space-only Dockerfile", self.workflow)


if __name__ == "__main__":
    unittest.main(verbosity=2)
