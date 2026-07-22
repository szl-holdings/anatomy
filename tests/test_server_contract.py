from __future__ import annotations

import copy
import json
import os
import sys
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server  # noqa: E402


class AnatomyContractTest(unittest.TestCase):
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
            with urllib.request.urlopen(req, timeout=5) as response:
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

    def test_manifest_separates_state_dimensions(self):
        status, headers, body = self.request("/api/anatomy/v1/manifest")
        self.assertEqual(200, status)
        self.assertEqual("szl.anatomy-manifest/v1", body["schema"])
        self.assertEqual(
            {"transport_state", "evidence_state", "verification_state", "authority_state"},
            set(body["state_dimensions"]),
        )
        self.assertEqual("CONJECTURE_1", body["doctrine"]["lambda"])
        self.assertEqual(
            ["F1", "F11", "F12", "F18", "F19"],
            body["doctrine"]["locked_proven_declared"],
        )
        self.assertEqual(
            ["F4", "F7", "F22"],
            body["doctrine"]["experimental_not_locked_declared"],
        )
        self.assertTrue(
            set(body["doctrine"]["locked_proven_declared"]).isdisjoint(
                body["doctrine"]["experimental_not_locked_declared"]
            )
        )
        self.assertEqual("*", headers["Access-Control-Allow-Origin"])

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
        self.assertEqual(
            ["F1", "F11", "F12", "F18", "F19"],
            formula["evidence"]["locked_declared"],
        )
        self.assertEqual(
            ["F4", "F7", "F22"],
            formula["evidence"]["experimental_not_locked"],
        )
        self.assertTrue(all(url.startswith("https://github.com/") for url in formula["provenance"]))

    def test_receipt_replays_as_structural_only(self):
        status, receipt_headers, receipt = self.request("/api/anatomy/v1/receipt")
        self.assertEqual(200, status)
        self.assertEqual("STRUCTURAL_ONLY", receipt["verification_state"])
        self.assertEqual(64, len(receipt["receipt_id"]))
        self.assertEqual("STRUCTURAL_ONLY", receipt_headers["X-SZL-Verification-State"])

        verify_status, verify_headers, verified = self.request(
            "/api/anatomy/v1/verify/receipt", method="POST", body=receipt
        )
        self.assertEqual(200, verify_status)
        self.assertEqual("STRUCTURAL-ONLY", verified["verdict"])
        self.assertEqual("STRUCTURAL_ONLY", verify_headers["X-SZL-Verification-State"])
        checks = {item["name"]: item["status"] for item in verified["checks"]}
        self.assertEqual("PASS", checks["artifact_set"])
        self.assertEqual("UNAVAILABLE", checks["signature"])

    def test_tampered_receipt_fails(self):
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
