from pathlib import Path
import unittest


WORKFLOW = Path(".github/workflows/hf-sync.yml")
README = Path("README.md")


class HfSyncContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.readme = README.read_text(encoding="utf-8")

    def test_runtime_files_are_in_upload_contract(self) -> None:
        for path in ("Dockerfile", ".dockerignore", "server.py"):
            self.assertIn(f'"{path}"', self.workflow, path)
        self.assertIn('"*.html"', self.workflow)
        self.assertNotIn('"index.html", "live-body.html"', self.workflow)

    def test_every_main_push_schedules_a_replacement_deploy(self) -> None:
        push_trigger = self.workflow.split("workflow_dispatch:", 1)[0]
        self.assertNotIn("paths:", push_trigger)
        self.assertIn("group: anatomy-hf-sync", self.workflow)
        self.assertIn("cancel-in-progress: false", self.workflow)

    def test_release_tooling_is_exactly_pinned(self) -> None:
        self.assertIn("huggingface_hub==1.23.0", self.workflow)
        self.assertNotIn("huggingface_hub>=", self.workflow)

    def test_release_waits_for_exact_live_revision(self) -> None:
        self.assertIn("info.sha == target_sha", self.workflow)
        self.assertIn('stage == "RUNNING"', self.workflow)
        self.assertIn('"BUILD_ERROR"', self.workflow)
        self.assertIn('/.well-known/szl-source.json?refresh=1', self.workflow)
        self.assertIn('source["deployment"]["hf_revision"] == target_sha', self.workflow)
        self.assertIn('source["source"]["commit"] == source_revision', self.workflow)
        self.assertIn(
            'source["alignment_state"] == "SOURCE_BOUND_DEPLOYMENT"',
            self.workflow,
        )
        self.assertIn(
            'source["deployment"]["workflow_run_id"] == workflow_run_id',
            self.workflow,
        )

    def test_release_generates_exact_source_manifest(self) -> None:
        self.assertIn('"schema": "szl.hf-deploy-manifest/v1"', self.workflow)
        self.assertIn('"source_repository": "szl-holdings/anatomy"', self.workflow)
        self.assertIn('"source_revision": source_revision', self.workflow)
        self.assertIn('"workflow_run_id": workflow_run_id', self.workflow)
        self.assertIn('path_in_repo="hf-deploy-manifest.json"', self.workflow)
        self.assertIn(
            'commit_message=f"hf-sync: source {source_revision} run {workflow_run_id}"',
            self.workflow,
        )
        self.assertNotIn("os.environ.get('GITHUB_SHA','')[:8]", self.workflow)

    def test_release_binds_manifest_to_hf_commit_metadata(self) -> None:
        self.assertIn('workflow_run_id = os.environ.get("GITHUB_RUN_ID", "")', self.workflow)
        self.assertIn('if not workflow_run_id.isdigit():', self.workflow)
        self.assertIn(
            'f"hf-sync: source {source_revision} run {workflow_run_id}"',
            self.workflow,
        )

    def test_release_rechecks_exact_current_main_at_mutation_boundary(self) -> None:
        for contract in (
            "GITHUB_TOKEN: ${{ github.token }}",
            'source_ref != "refs/heads/main"',
            'github_repo != "szl-holdings/anatomy"',
            'f"/repos/{github_repo}/commits/main"',
            "current_main != source_revision",
        ):
            self.assertIn(contract, self.workflow)
        self.assertLess(
            self.workflow.index("current_main != source_revision"),
            self.workflow.index("api.create_commit("),
        )

    def test_release_verifies_public_health(self) -> None:
        self.assertIn('base + "/healthz"', self.workflow)
        self.assertIn('health["transport_state"] == "REACHABLE"', self.workflow)
        self.assertIn('health["verification_state"] == "STRUCTURAL_ONLY"', self.workflow)

    def test_release_verifies_public_version_and_evidence(self) -> None:
        for contract in (
            'base + "/version"',
            'base + "/evidence?refresh=1"',
            'version["gitSha"] == source_revision',
            'version["deploymentRevision"] == target_sha',
            'version["evidenceState"] == "MEASURED"',
            'evidence["gitSha"] == source_revision',
            'evidence["evidenceState"] == "PARTIAL"',
            'evidence["source"]["deployment"]["hf_revision"] == target_sha',
            'evidence["receipts"][0]["status"] == "STRUCTURAL_ONLY"',
            'evidence["outputProvenance"]["authenticityEstablished"] is False',
        ):
            self.assertIn(contract, self.workflow)

    def test_stale_space_only_docker_claim_is_absent(self) -> None:
        self.assertNotIn("does not exist in this repo", self.workflow)
        self.assertNotIn("Space-only Dockerfile", self.workflow)

    def test_archived_uds_source_is_not_advertised(self) -> None:
        self.assertNotIn(
            "https://github.com/szl-holdings/szl-uds-deployment",
            self.readme,
        )
        for active_source in ("a11oy", "killinchu", "szl-mesh"):
            self.assertIn(
                f"https://github.com/szl-holdings/{active_source}",
                self.readme,
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
