from __future__ import annotations

import copy
import io
import json
import os
import re
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server  # noqa: E402


class AnatomyContractTest(unittest.TestCase):
    @staticmethod
    def complete_manifest():
        artifacts = [
            {"path": path, "bytes": 1, "sha256": "d" * 64}
            for path in server.ARTIFACT_PATHS
        ]
        return {
            "algorithm": "sha256",
            "artifact_count": len(artifacts),
            "artifact_set_sha256": server._sha256(server._canonical(artifacts)),
            "artifacts": artifacts,
        }

    @classmethod
    def setUpClass(cls) -> None:
        cls.httpd = server.make_server("127.0.0.1", 0)
        cls.port = cls.httpd.server_address[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=3)

    def request(self, path: str, *, method: str = "GET", body=None):
        data = None
        headers = {}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(self.base + path, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                return response.status, dict(response.headers), json.load(response)
        except urllib.error.HTTPError as exc:
            return exc.code, dict(exc.headers), json.load(exc)

    def test_health_is_transport_only(self):
        status, headers, body = self.request("/healthz")
        self.assertEqual(200, status)
        self.assertEqual("REACHABLE", body["transport_state"])
        self.assertEqual("SNAPSHOT", body["evidence_state"])
        self.assertEqual("STRUCTURAL_ONLY", body["verification_state"])
        self.assertEqual("READ_ONLY", body["authority_state"])
        self.assertIn("quality", body["note"])
        self.assertEqual("REACHABLE", headers["X-SZL-Transport-State"])
        self.assertEqual("nosniff", headers["X-Content-Type-Options"])

    def test_static_bundle_is_served_from_the_anatomy_root(self):
        for path, marker in (("/", "SZL Living Anatomy"), ("/frontier_anatomy.js", "Evidence Bay")):
            with urllib.request.urlopen(self.base + path, timeout=5) as response:
                body = response.read().decode("utf-8")
                self.assertEqual(200, response.status)
                self.assertIn(marker, body)

    def test_runtime_manifest_covers_frontend_script_dependencies(self):
        declared = set(server.ARTIFACT_PATHS)
        required: set[str] = set()
        for relative_path in ("index.html", "live-body.html"):
            document = (ROOT / relative_path).read_text(encoding="utf-8")
            required.update(
                re.findall(r'<script[^>]+src="\./([^"?#]+)', document)
            )
        self.assertTrue(required)
        self.assertEqual(set(), required - declared)

    def test_manifest_separates_state_dimensions(self):
        status, headers, body = self.request("/api/anatomy/v1/manifest")
        self.assertEqual(200, status)
        self.assertEqual("szl.anatomy-manifest/v1", body["schema"])
        self.assertEqual(
            {"transport_state", "evidence_state", "verification_state", "authority_state"},
            set(body["state_dimensions"]),
        )
        self.assertEqual("CONJECTURE_1", body["doctrine"]["lambda"])
        self.assertEqual(8, len(body["doctrine"]["locked_proven_declared"]))
        self.assertEqual("/version", body["endpoints"]["version"])
        self.assertEqual("/evidence", body["endpoints"]["evidence_index"])
        self.assertEqual("*", headers["Access-Control-Allow-Origin"])

    def test_version_and_evidence_are_real_json_contracts(self):
        source = {
            "schema": "szl.deployment-source/v1",
            "source": {
                "repository": "szl-holdings/anatomy",
                "commit": "b" * 40,
                "path": "",
                "relation": "github-actions-source-bound-deployment",
            },
            "deployment": {
                "hf_space": "SZLHOLDINGS/anatomy",
                "hf_revision": "c" * 40,
                "artifact_set_sha256": "d" * 64,
            },
            "built_at": None,
            "observed_at": "2026-08-01T00:00:00Z",
            "alignment_state": "SOURCE_BOUND_DEPLOYMENT",
            "limits": [],
        }
        dependencies = {
            "evidence_state": "MIXED",
            "observed_at": "2026-08-01T00:00:00Z",
            "summary": {"live": 3, "total": 4},
        }
        with (
            mock.patch.object(server, "_source_attestation", return_value=source),
            mock.patch.object(server, "_dependency_evidence", return_value=dependencies),
            mock.patch.object(server, "_artifact_manifest", return_value=self.complete_manifest()),
        ):
            version_status, _, version = self.request("/version")
            evidence_status, evidence_headers, evidence = self.request("/evidence")

        self.assertEqual(200, version_status)
        self.assertEqual("szl.vertical-conformance.version.v1", version["schemaVersion"])
        self.assertEqual("b" * 40, version["gitSha"])
        self.assertEqual("c" * 40, version["deploymentRevision"])
        self.assertEqual("MEASURED", version["evidenceState"])

        self.assertEqual(200, evidence_status)
        self.assertEqual("szl.vertical-conformance.evidence.v1", evidence["schemaVersion"])
        self.assertEqual("PARTIAL", evidence["evidenceState"])
        self.assertEqual("b" * 40, evidence["gitSha"])
        self.assertEqual("STRUCTURAL_ONLY", evidence["receipts"][0]["status"])
        self.assertEqual(False, evidence["outputProvenance"]["authenticityEstablished"])
        self.assertEqual("STRUCTURAL_ONLY", evidence_headers["X-SZL-Verification-State"])

    def test_unbound_version_refuses_to_publish_declared_base_as_runtime_identity(self):
        source = {
            "source": {"commit": "a" * 40},
            "deployment": {"hf_revision": "b" * 40},
            "alignment_state": "PENDING_GITHUB_SYNC",
        }
        with mock.patch.object(server, "_source_attestation", return_value=source):
            status, _, version = self.request("/version")
        self.assertEqual(503, status)
        self.assertEqual("UNAVAILABLE", version["evidenceState"])
        self.assertIsNone(version["gitSha"])

    def test_unbound_evidence_fails_closed_at_transport_and_claim_layers(self):
        source = {
            "source": {"commit": "a" * 40},
            "deployment": {"hf_revision": "b" * 40},
            "alignment_state": "PENDING_GITHUB_SYNC",
        }
        dependencies = {
            "evidence_state": "UNAVAILABLE",
            "observed_at": "2026-08-01T00:00:00Z",
            "summary": {"live": 0, "total": 4},
        }
        with (
            mock.patch.object(server, "_source_attestation", return_value=source),
            mock.patch.object(server, "_dependency_evidence", return_value=dependencies),
            mock.patch.object(server, "_artifact_manifest", return_value=self.complete_manifest()),
        ):
            status, headers, evidence = self.request("/evidence")
        self.assertEqual(503, status)
        self.assertEqual("UNAVAILABLE", evidence["evidenceState"])
        self.assertIsNone(evidence["gitSha"])
        self.assertEqual("STRUCTURAL_ONLY", evidence["receipts"][0]["status"])
        self.assertEqual("STRUCTURAL_ONLY", headers["X-SZL-Verification-State"])

    def test_malformed_source_revisions_cannot_satisfy_binding(self):
        source = {
            "source": {"commit": "not-a-revision"},
            "deployment": {"hf_revision": "z" * 40},
            "alignment_state": "SOURCE_BOUND_DEPLOYMENT",
        }
        dependencies = {
            "evidence_state": "UNAVAILABLE",
            "observed_at": "2026-08-01T00:00:00Z",
            "summary": {"live": 0, "total": 4},
        }
        with (
            mock.patch.object(server, "_source_attestation", return_value=source),
            mock.patch.object(server, "_dependency_evidence", return_value=dependencies),
        ):
            version_status, _, version = self.request("/version")
            evidence_status, _, evidence = self.request("/evidence")
        self.assertEqual(503, version_status)
        self.assertEqual(503, evidence_status)
        self.assertEqual("UNAVAILABLE", version["evidenceState"])
        self.assertEqual("UNAVAILABLE", evidence["evidenceState"])
        self.assertIsNone(version["gitSha"])
        self.assertIsNone(evidence["gitSha"])

    def test_missing_runtime_artifact_fails_readiness_and_evidence(self):
        source = {
            "source": {"commit": "a" * 40},
            "deployment": {"hf_revision": "b" * 40},
            "alignment_state": "SOURCE_BOUND_DEPLOYMENT",
        }
        dependencies = {
            "evidence_state": "UNAVAILABLE",
            "observed_at": "2026-08-01T00:00:00Z",
            "summary": {"live": 0, "total": 4},
        }
        receipt = {
            "receipt": {
                "evidence": {
                    "artifact_set_sha256": "d" * 64,
                    "artifacts": [{"path": path, "state": "MISSING"} for path in server.ARTIFACT_PATHS],
                }
            },
            "receipt_id": "e" * 64,
        }
        with (
            mock.patch.object(server, "_source_attestation", return_value=source),
            mock.patch.object(server, "_dependency_evidence", return_value=dependencies),
            mock.patch.object(server, "_local_receipt", return_value=receipt),
        ):
            status, headers, evidence = self.request("/evidence")
        self.assertEqual(503, status)
        self.assertEqual("UNAVAILABLE", evidence["evidenceState"])
        self.assertIsNone(evidence["gitSha"])
        self.assertEqual("DEGRADED", evidence["runtime"]["status"])
        self.assertFalse(evidence["runtime"]["ready"])
        self.assertEqual("FAILED", evidence["receipts"][0]["status"])
        self.assertEqual("FAILED", headers["X-SZL-Verification-State"])

    def test_every_capability_has_five_part_shell(self):
        status, _, body = self.request("/api/anatomy/v1/capabilities")
        self.assertEqual(200, status)
        self.assertGreaterEqual(body["count"], 5)
        for capability in body["capabilities"]:
            for key in ("purpose", "try", "evidence", "limits", "reproduce"):
                self.assertIn(key, capability, f"{capability['id']} lacks {key}")
            self.assertEqual("READ_ONLY", capability["authority_state"])
        formula = next(item for item in body["capabilities"] if item["id"] == "anatomy.formula-spine")
        self.assertEqual("SNAPSHOT", formula["evidence"]["state"])
        self.assertTrue(all(url.startswith("https://github.com/") for url in formula["provenance"]))

    def test_receipt_replays_as_structural_only(self):
        with mock.patch.object(
            server, "_artifact_manifest", return_value=self.complete_manifest()
        ):
            status, receipt_headers, receipt = self.request("/api/anatomy/v1/receipt")
            verify_status, verify_headers, verified = self.request(
                "/api/anatomy/v1/verify/receipt", method="POST", body=receipt
            )
        self.assertEqual(200, status)
        self.assertEqual("STRUCTURAL_ONLY", receipt["verification_state"])
        self.assertEqual(64, len(receipt["receipt_id"]))
        self.assertEqual("STRUCTURAL_ONLY", receipt_headers["X-SZL-Verification-State"])
        self.assertEqual(200, verify_status)
        self.assertEqual("STRUCTURAL-ONLY", verified["verdict"])
        self.assertEqual("STRUCTURAL_ONLY", verify_headers["X-SZL-Verification-State"])
        checks = {item["name"]: item["status"] for item in verified["checks"]}
        self.assertEqual("PASS", checks["artifact_set"])
        self.assertEqual("UNAVAILABLE", checks["signature"])

    def test_tampered_receipt_fails(self):
        with mock.patch.object(
            server, "_artifact_manifest", return_value=self.complete_manifest()
        ):
            _, _, receipt = self.request("/api/anatomy/v1/receipt")
            tampered = copy.deepcopy(receipt)
            tampered["receipt"]["claim"]["purpose"] = "changed"
            status, _, result = self.request(
                "/api/anatomy/v1/verify/receipt", method="POST", body=tampered
            )
        self.assertEqual(400, status)
        self.assertEqual("FAIL", result["verdict"])
        checks = {item["name"]: item["status"] for item in result["checks"]}
        self.assertEqual("FAIL", checks["receipt_digest"])

    def test_rehashed_receipt_with_missing_artifact_fails(self):
        current = self.complete_manifest()
        with mock.patch.object(server, "_artifact_manifest", return_value=current):
            _, _, receipt = self.request("/api/anatomy/v1/receipt")
            tampered = copy.deepcopy(receipt)
            tampered["receipt"]["evidence"]["artifacts"].pop()
            tampered["receipt_id"] = server._sha256(
                server._canonical(tampered["receipt"])
            )
            status, _, result = self.request(
                "/api/anatomy/v1/verify/receipt", method="POST", body=tampered
            )
        self.assertEqual(400, status)
        self.assertEqual("FAIL", result["verdict"])
        checks = {item["name"]: item["status"] for item in result["checks"]}
        self.assertEqual("PASS", checks["receipt_digest"])
        self.assertEqual("FAIL", checks["artifact_set"])
        self.assertEqual("FAIL", checks["artifact_completeness"])

    def test_incomplete_receipt_cannot_receive_structural_pass(self):
        incomplete = {
            "algorithm": "sha256",
            "artifact_count": len(server.ARTIFACT_PATHS),
            "artifact_set_sha256": "f" * 64,
            "artifacts": [
                {"path": path, "state": "MISSING"} for path in server.ARTIFACT_PATHS
            ],
        }
        with mock.patch.object(server, "_artifact_manifest", return_value=incomplete):
            _, _, receipt = self.request("/api/anatomy/v1/receipt")
            status, _, result = self.request(
                "/api/anatomy/v1/verify/receipt", method="POST", body=receipt
            )
        self.assertEqual(400, status)
        self.assertEqual("FAIL", result["verdict"])
        checks = {item["name"]: item["status"] for item in result["checks"]}
        self.assertEqual("FAIL", checks["artifact_completeness"])

    def test_forged_incomplete_candidate_cannot_reuse_live_artifact_digest(self):
        manifest = self.complete_manifest()
        with mock.patch.object(server, "_artifact_manifest", return_value=manifest):
            _, _, receipt = self.request("/api/anatomy/v1/receipt")
            receipt["receipt"]["evidence"]["artifacts"] = [
                {"path": path, "state": "MISSING"} for path in server.ARTIFACT_PATHS
            ]
            receipt["receipt_id"] = server._sha256(server._canonical(receipt["receipt"]))
            status, _, result = self.request(
                "/api/anatomy/v1/verify/receipt", method="POST", body=receipt
            )
        self.assertEqual(400, status)
        self.assertEqual("FAIL", result["verdict"])
        checks = {item["name"]: item["status"] for item in result["checks"]}
        self.assertEqual("PASS", checks["receipt_digest"])
        self.assertEqual("FAIL", checks["artifact_set"])
        self.assertEqual("FAIL", checks["artifact_completeness"])

    def test_zero_byte_runtime_artifact_is_incomplete(self):
        manifest = self.complete_manifest()
        manifest["artifacts"][0]["bytes"] = 0
        manifest["artifact_set_sha256"] = server._sha256(
            server._canonical(manifest["artifacts"])
        )
        with mock.patch.object(server, "_artifact_manifest", return_value=manifest):
            status, headers, receipt = self.request("/api/anatomy/v1/receipt")
        self.assertEqual(503, status)
        self.assertEqual("FAILED", receipt["verification_state"])
        self.assertEqual("FAILED", headers["X-SZL-Verification-State"])

    def test_source_attestation_matches_estate_schema(self):
        previous = os.environ.get("SPACE_REPOSITORY_COMMIT")
        os.environ["SPACE_REPOSITORY_COMMIT"] = "a" * 40
        try:
            status, _, body = self.request("/.well-known/szl-source.json")
        finally:
            if previous is None:
                os.environ.pop("SPACE_REPOSITORY_COMMIT", None)
            else:
                os.environ["SPACE_REPOSITORY_COMMIT"] = previous
        self.assertEqual(200, status)
        self.assertEqual("szl.deployment-source/v1", body["schema"])
        self.assertEqual("szl-holdings/anatomy", body["source"]["repository"])
        self.assertEqual("SZLHOLDINGS/anatomy", body["deployment"]["hf_space"])
        self.assertEqual("a" * 40, body["deployment"]["hf_revision"])
        self.assertEqual("PENDING_GITHUB_SYNC", body["alignment_state"])

    def test_source_attestation_prefers_valid_deploy_manifest(self):
        previous_manifest = server.DEPLOY_MANIFEST_PATH
        previous_revision = os.environ.get("SPACE_REPOSITORY_COMMIT")
        with tempfile.TemporaryDirectory() as temporary:
            manifest = Path(temporary) / "hf-deploy-manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema": "szl.hf-deploy-manifest/v1",
                        "source_repository": "szl-holdings/anatomy",
                        "source_revision": "b" * 40,
                        "source_path": "",
                        "workflow_run_id": "123456789",
                    }
                ),
                encoding="utf-8",
            )
            server.DEPLOY_MANIFEST_PATH = manifest
            os.environ["SPACE_REPOSITORY_COMMIT"] = "c" * 40
            try:
                with mock.patch.object(server, "_hf_commit_matches_source", return_value=True):
                    status, _, body = self.request("/.well-known/szl-source.json")
            finally:
                server.DEPLOY_MANIFEST_PATH = previous_manifest
                if previous_revision is None:
                    os.environ.pop("SPACE_REPOSITORY_COMMIT", None)
                else:
                    os.environ["SPACE_REPOSITORY_COMMIT"] = previous_revision
        self.assertEqual(200, status)
        self.assertEqual("b" * 40, body["source"]["commit"])
        self.assertEqual(
            "github-actions-source-bound-deployment",
            body["source"]["relation"],
        )
        self.assertEqual("SOURCE_BOUND_DEPLOYMENT", body["alignment_state"])
        self.assertEqual("c" * 40, body["deployment"]["hf_revision"])
        self.assertEqual("MEASURED", body["deployment"]["commit_binding"])
        self.assertEqual("123456789", body["deployment"]["workflow_run_id"])

    def test_source_attestation_rejects_stale_manifest_on_new_hf_revision(self):
        previous_manifest = server.DEPLOY_MANIFEST_PATH
        previous_revision = os.environ.get("SPACE_REPOSITORY_COMMIT")
        with tempfile.TemporaryDirectory() as temporary:
            manifest = Path(temporary) / "hf-deploy-manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema": "szl.hf-deploy-manifest/v1",
                        "source_repository": "szl-holdings/anatomy",
                        "source_revision": "b" * 40,
                        "source_path": "",
                        "workflow_run_id": "123456789",
                    }
                ),
                encoding="utf-8",
            )
            server.DEPLOY_MANIFEST_PATH = manifest
            os.environ["SPACE_REPOSITORY_COMMIT"] = "c" * 40
            try:
                with mock.patch.object(server, "_hf_commit_matches_source", return_value=False):
                    status, _, body = self.request("/.well-known/szl-source.json")
            finally:
                server.DEPLOY_MANIFEST_PATH = previous_manifest
                if previous_revision is None:
                    os.environ.pop("SPACE_REPOSITORY_COMMIT", None)
                else:
                    os.environ["SPACE_REPOSITORY_COMMIT"] = previous_revision
        self.assertEqual(200, status)
        self.assertEqual("DEPLOYMENT_REVISION_UNBOUND", body["alignment_state"])
        self.assertEqual("UNAVAILABLE", body["deployment"]["commit_binding"])
        self.assertIsNone(body["deployment"]["workflow_run_id"])
        self.assertIn("do not bind", body["limits"][-1])

    def test_hf_commit_binding_requires_exact_head_title_and_manifest_diff(self):
        source_revision = "b" * 40
        hf_revision = "c" * 40
        workflow_run_id = "123456789"
        commits = json.dumps(
            [
                {
                    "id": hf_revision,
                    "title": f"hf-sync: source {source_revision} run {workflow_run_id}",
                }
            ]
        ).encode("utf-8")
        commit_diff = (
            "diff --git a/hf-deploy-manifest.json b/hf-deploy-manifest.json\n"
            f'+  "source_revision": "{source_revision}"\n'
            f'+  "workflow_run_id": "{workflow_run_id}"\n'
        ).encode("utf-8")
        with mock.patch.object(
            urllib.request,
            "urlopen",
            side_effect=[io.BytesIO(commits), io.BytesIO(commit_diff)],
        ):
            self.assertTrue(
                server._hf_commit_matches_source(
                    hf_revision, source_revision, workflow_run_id, force=True
                )
            )

        stale_diff = b"diff --git a/index.html b/index.html\n"
        with mock.patch.object(
            urllib.request,
            "urlopen",
            side_effect=[io.BytesIO(commits), io.BytesIO(stale_diff)],
        ):
            self.assertFalse(
                server._hf_commit_matches_source(
                    hf_revision, source_revision, workflow_run_id, force=True
                )
            )

    def test_frontend_and_public_verifier_use_current_contract(self):
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        bay = (ROOT / "frontier_anatomy.js").read_text(encoding="utf-8")
        widget = (ROOT / "lib" / "szl_verify_widget.js").read_text(encoding="utf-8")
        self.assertIn('src="./frontier_anatomy.js"', index)
        self.assertIn("Evidence Bay", bay)
        self.assertIn("/api/anatomy/v1", bay)
        self.assertIn("/api/a11oy/v1/verify/receipt", widget)
        self.assertNotIn("base+'/api/a11oy/v1/verify'", widget)


if __name__ == "__main__":
    unittest.main(verbosity=2)
