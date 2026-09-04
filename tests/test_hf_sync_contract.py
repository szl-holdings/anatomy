from pathlib import Path
import unittest


WORKFLOW = Path(".github/workflows/hf-sync.yml")
PUBLISHER = Path("scripts/sync_hf_creator_profile.py")
README = Path("README.md")


class HfSyncContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.publisher = PUBLISHER.read_text(encoding="utf-8")
        cls.release = cls.workflow + "\n" + cls.publisher
        cls.readme = README.read_text(encoding="utf-8")

    def test_runtime_files_are_in_upload_contract(self) -> None:
        for path in (
            "README.md",
            "Dockerfile",
            ".dockerignore",
            "server.py",
            "organ_integrity.py",
            "living_runtime.py",
            "second_brain_runtime.py",
        ):
            self.assertIn(f'"{path}"', self.publisher, path)
        self.assertIn('"*.html"', self.publisher)
        self.assertIn('"*.js"', self.publisher)
        self.assertIn('"*.css"', self.publisher)
        self.assertNotIn('"index.html", "live-body.html"', self.publisher)

    def test_every_main_push_schedules_a_replacement_deploy(self) -> None:
        push_trigger = self.workflow.split("workflow_dispatch:", 1)[0]
        self.assertNotIn("paths:", push_trigger)
        self.assertIn("group: anatomy-hf-creator-sync", self.workflow)
        self.assertIn("cancel-in-progress: false", self.workflow)
        self.assertIn("python scripts/sync_hf_creator_profile.py", self.workflow)

    def test_creator_profile_is_the_only_public_destination(self) -> None:
        self.assertIn('SPACE_ID = "betterwithage/anatomy"', self.publisher)
        self.assertIn('EXPECTED_IDENTITY = "betterwithage"', self.publisher)
        self.assertIn(
            'LIVE_BASE = "https://betterwithage-anatomy.hf.space"',
            self.publisher,
        )
        self.assertIn('"destination": "betterwithage/anatomy"', self.workflow)

    def test_release_tooling_is_exactly_pinned(self) -> None:
        self.assertIn("huggingface_hub==1.23.0", self.workflow)
        self.assertNotIn("huggingface_hub>=", self.workflow)

    def test_release_waits_for_exact_live_revision(self) -> None:
        self.assertIn('current_sha == target_sha and stage == "RUNNING"', self.publisher)
        self.assertIn('"BUILD_ERROR"', self.publisher)
        self.assertIn('/version?refresh=1', self.publisher)
        self.assertIn('/.well-known/szl-source.json?refresh=1', self.publisher)
        self.assertIn('source["deployment"]["hf_revision"] == target_sha', self.publisher)
        self.assertIn('source["source"]["commit"] == source_revision', self.publisher)
        self.assertIn(
            'source["deployment"]["workflow_run_id"] == workflow_run_id',
            self.publisher,
        )

    def test_release_generates_exact_source_manifest(self) -> None:
        self.assertIn('"schema": "szl.hf-deploy-manifest/v1"', self.publisher)
        self.assertIn('EXPECTED_REPOSITORY = "szl-holdings/anatomy"', self.publisher)
        self.assertIn('"source_revision": source_revision', self.publisher)
        self.assertIn('"workflow_run_id": workflow_run_id', self.publisher)
        self.assertIn('path_in_repo="hf-deploy-manifest.json"', self.publisher)
        self.assertIn(
            'f"hf-sync: creator profile source {source_revision} "',
            self.publisher,
        )
        self.assertNotIn("os.environ.get('GITHUB_SHA','')[:8]", self.release)

    def test_release_binds_manifest_to_hf_commit_metadata(self) -> None:
        self.assertIn('workflow_run_id = os.environ.get("GITHUB_RUN_ID", "")', self.publisher)
        self.assertIn('if not workflow_run_id.isdigit():', self.publisher)
        self.assertIn(
            'f"hf-sync: creator profile source {source_revision} "',
            self.publisher,
        )
        self.assertIn('f"run {workflow_run_id}"', self.publisher)

    def test_release_rechecks_exact_current_main_at_mutation_boundary(self) -> None:
        for contract in (
            "GITHUB_TOKEN: ${{ github.token }}",
            'source_ref != "refs/heads/main"',
            'repository != EXPECTED_REPOSITORY',
            'f"/repos/{repository}/commits/main"',
            "current_protected_main(repository, github_token) != source_revision",
        ):
            self.assertIn(contract, self.release)
        self.assertLess(
            self.publisher.index(
                "current_protected_main(repository, github_token) != source_revision"
            ),
            self.publisher.index("api.create_commit("),
        )

    def test_release_verifies_public_health_and_brain_boundary(self) -> None:
        for contract in (
            'LIVE_BASE + "/healthz"',
            'health["transport_state"] == "REACHABLE"',
            'living["ready"] is True',
            'living["organs"]["brain"]["chunk_count"] == 575',
            'brain["private_graph_nodes_loaded"] == 0',
            'brain["content_access"] == "HANDLES_ONLY"',
            'all("text" not in handle for handle in search["handles"])',
        ):
            self.assertIn(contract, self.publisher)

    def test_release_verifies_public_version_and_evidence(self) -> None:
        for contract in (
            'LIVE_BASE + "/version?refresh=1"',
            'LIVE_BASE + "/evidence?refresh=1"',
            'version["gitSha"] == source_revision',
            'version["deploymentRevision"] == target_sha',
            'version["secondBrainSourceRevision"] == brain_revision',
            'evidence["gitSha"] == source_revision',
            'evidence["source"]["deployment"]["hf_revision"] == target_sha',
        ):
            self.assertIn(contract, self.publisher)

    def test_release_is_bounded_to_public_read_only_second_brain(self) -> None:
        for contract in (
            '"authority_state": "READ_ONLY"',
            '"content_access": "HANDLES_ONLY"',
            'brain_source.get("private_graph_nodes_materialized") != 0',
            'int(brain_source.get("public_chunk_count") or 0) != 575',
        ):
            self.assertIn(contract, self.publisher)

    def test_stale_space_only_docker_claim_is_absent(self) -> None:
        self.assertNotIn("does not exist in this repo", self.release)
        self.assertNotIn("Space-only Dockerfile", self.release)

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
