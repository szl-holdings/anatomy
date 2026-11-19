# SPDX-License-Identifier: Apache-2.0
"""Offline qualification of the optional Ancient Mathematics reference plane.

A passing test proves only fixed synthetic arithmetic and source packaging.
It does not validate historical transcriptions or production publication.
"""
from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path
from unittest.mock import patch

import ancient_math_atlas as atlas


ROOT = Path(__file__).resolve().parents[1]


class AncientMathematicsCatalogTests(unittest.TestCase):
    def test_curated_catalog_is_deterministic_and_bounded(self):
        first = atlas.catalog_payload()
        second = atlas.catalog_payload()
        self.assertEqual(first, second)
        self.assertTrue(first["ready"])
        self.assertEqual(first["record_count"], 10)
        self.assertEqual(len(first["records"]), 10)
        self.assertRegex(first["catalog_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(first["schema"], "szl.anatomy.ancient-math-atlas/v1")
        self.assertEqual(first["state"], "CURATED_RESEARCH_EXACT_EXAMPLES")
        self.assertEqual(first["source_identity"], "PINNED_DECLARATIONS_NOT_LIVE_VERIFIED")

    def test_exact_witnesses_match_expected_math(self):
        witnesses = {
            row["id"]: row["witness"] for row in atlas.catalog_payload()["records"]
        }
        self.assertEqual(set(witnesses), {
            "rhind-unit-fractions", "rhind-doubling", "moscow-frustum",
            "euclid-i47", "euclid-vii2", "dresden-venus-cycle",
            "maya-long-count", "andean-khipu-positional",
            "andean-khipu-aggregate", "szl-kcrc-fingerprint",
        })
        expected = {
            "rhind-unit-fractions": "2/7",
            "rhind-doubling": "2419",
            "moscow-frustum": "56",
            "euclid-i47": "25",
            "euclid-vii2": "21",
            "dresden-venus-cycle": "2920",
            "maya-long-count": "159565",
            "andean-khipu-positional": "345",
            "andean-khipu-aggregate": "25",
            "szl-kcrc-fingerprint": "439",
        }
        for key, value in expected.items():
            with self.subTest(formula=key):
                self.assertEqual(witnesses[key]["status"], "PASS_EXACT_ARITHMETIC")
                self.assertEqual(witnesses[key]["observed"], value)
                self.assertEqual(witnesses[key]["expected"], value)
                self.assertEqual(
                    witnesses[key]["kind"], "FIXED_SYNTHETIC_OR_ILLUSTRATIVE"
                )

    def test_history_and_modern_math_are_distinct(self):
        payload = atlas.catalog_payload()
        traditions = {r["tradition"] for r in payload["records"]}
        self.assertEqual(traditions, {
            "Ancient Egypt", "Ancient Greece", "Maya Codices",
            "Andean Khipu", "SZL Modern Research",
        })
        for row in payload["records"]:
            self.assertTrue(row["limit"])
            self.assertTrue(row["artifact"])
            self.assertTrue(row["status"])
            self.assertTrue(row["analogy"])
            if row["tradition"] == "SZL Modern Research":
                self.assertEqual(
                    row["status"], "MODERN_SZL_CONSTRUCTION_NOT_HISTORICAL"
                )
        self.assertEqual(
            payload["authority"]["historical_decipherment"], "NONE"
        )
        self.assertEqual(payload["authority"]["historic_influence_claim"], "NONE")
        self.assertEqual(payload["authority"]["lean_proof"], "NOT_CLAIMED")
        self.assertEqual(payload["authority"]["training"], "NONE")
        self.assertEqual(payload["authority"]["provider_mutation"], "NONE")
        self.assertFalse(payload["authority"]["locked_proven_count_modified"])

    def test_pins_are_full_protected_source_revisions(self):
        payload = atlas.catalog_payload()
        self.assertEqual(payload["source_pins"], {
            "szl-papers": atlas.PAPERS_SHA,
            "szl-khipu": atlas.KHIPU_SHA,
            "lutar-lean": atlas.LEAN_SHA,
        })
        for ref in payload["source_pins"].values():
            self.assertRegex(ref, r"^[0-9a-f]{40}$")
        self.assertEqual(
            payload["research_context"]["locked_proven_ids"],
            ["F1", "F4", "F7", "F11", "F12", "F18", "F19", "F22"],
        )
        self.assertIn("CONJECTURE", payload["research_context"]["lambda"])
        self.assertIn("CONJECTURE_2", payload["research_context"]["khipu_bft"])

    def test_catalog_digest_is_recomputable_and_excludes_observation_time(self):
        payload = atlas.catalog_payload()
        basis = {"schema": atlas.SCHEMA, "source_pins": payload["source_pins"],
                 "records": atlas.RECORDS}
        digest = hashlib.sha256(
            json.dumps(basis, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        self.assertEqual(payload["catalog_sha256"], digest)
        self.assertNotIn("observed_at", payload)

    def test_tampering_with_a_witness_fails_closed(self):
        with patch.object(atlas, "_exact_example",
                          return_value=("WRONG", "EXPECTED")):
            result = atlas.catalog_payload()
        self.assertFalse(result["ready"])
        self.assertEqual(result["state"], "UNAVAILABLE")
        self.assertEqual(result["records"], [])
        self.assertNotIn("catalog_sha256", result)

    def test_missing_record_fails_closed(self):
        with patch.object(atlas, "RECORDS", atlas.RECORDS[:-1]):
            result = atlas.catalog_payload()
        self.assertFalse(result["ready"])
        self.assertEqual(result["record_count"], 0)

    def test_extra_field_or_missing_rights_context_fails_closed(self):
        records = [dict(item) for item in atlas.RECORDS]
        records[0].pop("limit")
        with patch.object(atlas, "RECORDS", tuple(records)):
            self.assertFalse(atlas.catalog_payload()["ready"])

    def test_invalid_url_or_modern_label_fails_closed(self):
        records = [dict(item) for item in atlas.RECORDS]
        records[0]["historical_url"] = "javascript:alert(1)"
        with patch.object(atlas, "RECORDS", tuple(records)):
            self.assertFalse(atlas.catalog_payload()["ready"])
        records = [dict(item) for item in atlas.RECORDS]
        records[-1]["status"] = "LOCKED_LEAN_PROOF"
        with patch.object(atlas, "RECORDS", tuple(records)):
            self.assertFalse(atlas.catalog_payload()["ready"])

    def test_retains_declared_unknown_cord_and_separate_tiers(self):
        rows = {row["id"]: row for row in atlas.catalog_payload()["records"]}
        self.assertIn("unknown", rows["andean-khipu-aggregate"]["limit"].lower())
        self.assertIn("not used by ancient", rows["szl-kcrc-fingerprint"]["limit"].lower())
        self.assertIn("approximation", rows["dresden-venus-cycle"]["limit"].lower())


class AnatomyPackagingTests(unittest.TestCase):
    def test_runtime_exposes_only_read_only_bounded_get(self):
        source = (ROOT / "living_runtime.py").read_text(encoding="utf-8")
        self.assertIn('if path == "/api/anatomy/v1/brain/ancient-math":', source)
        self.assertIn('ancient_math_catalog_payload()', source)
        self.assertIn('"X-SZL-Historical-Proof": "NOT_CLAIMED"', source)
        self.assertIn('"X-SZL-Authority": "READ_ONLY"', source)
        self.assertIn('"ancient_math_atlas.py"', source)
        self.assertIn('"ancient_math_atlas": "/api/anatomy/v1/brain/ancient-math"', source)

    def test_publisher_admits_file_and_independent_postdeploy_readback(self):
        source = (ROOT / "scripts/sync_hf_creator_profile.py").read_text(
            encoding="utf-8"
        )
        self.assertGreaterEqual(source.count('"ancient_math_atlas.py"'), 2)
        self.assertIn("expected_ancient = ancient_math_catalog_payload()", source)
        self.assertIn('ancient["catalog_sha256"] == expected_ancient["catalog_sha256"]', source)
        self.assertIn('ancient["source_pins"] == expected_ancient["source_pins"]', source)
        self.assertIn('ancient["authority"]["historical_decipherment"] == "NONE"', source)
        self.assertIn(
            'version["ancientMathCatalogSha256"] == expected_ancient["catalog_sha256"]',
            source,
        )

    def test_browser_has_lazy_same_origin_explicit_scholarly_tab(self):
        js = (ROOT / "neural-quant-v7.js").read_text(encoding="utf-8")
        self.assertIn('["ancient", "Ancient Math"]', js)
        self.assertIn('fetch("/api/anatomy/v1/brain/ancient-math"', js)
        self.assertIn('const safeResearchLink = (rawUrl, label)', js)
        self.assertIn('const renderAncient = (payload)', js)
        self.assertIn('link.rel = "noopener noreferrer"', js)
        self.assertNotIn("innerHTML", js[js.index('const renderAncient'):js.index('const renderQuant')])

    def test_same_origin_handler_serves_read_only_bounded_payload(self):
        import threading
        import urllib.request
        import living_runtime

        httpd = living_runtime.make_server("127.0.0.1", 0)
        worker = threading.Thread(target=httpd.serve_forever, daemon=True)
        worker.start()
        try:
            url = (
                f"http://127.0.0.1:{httpd.server_port}"
                "/api/anatomy/v1/brain/ancient-math"
            )
            with urllib.request.urlopen(url, timeout=5) as response:
                self.assertEqual(response.status, 200)
                self.assertEqual(response.headers.get("X-SZL-Authority"), "READ_ONLY")
                self.assertEqual(response.headers.get("X-SZL-Historical-Proof"), "NOT_CLAIMED")
                self.assertEqual(response.headers.get("X-SZL-Content-Access"), "CURATED_METADATA_ONLY")
                body = response.read(65536)
            payload = json.loads(body)
            self.assertTrue(payload["ready"])
            self.assertEqual(payload["record_count"], 10)
            self.assertEqual(
                payload["catalog_sha256"], atlas.catalog_payload()["catalog_sha256"]
            )
            self.assertNotIn("corpus_text", payload)
            self.assertNotIn("training_data", payload)
        finally:
            httpd.shutdown()
            httpd.server_close()
            worker.join(timeout=5)

    def test_handler_fails_closed_on_catalog_drift(self):
        import threading
        import urllib.error
        import urllib.request
        import living_runtime

        httpd = living_runtime.make_server("127.0.0.1", 0)
        worker = threading.Thread(target=httpd.serve_forever, daemon=True)
        worker.start()
        try:
            with patch.object(
                living_runtime, "ancient_math_catalog_payload",
                return_value={
                    "schema": atlas.SCHEMA, "state": "UNAVAILABLE",
                    "ready": False, "evidence_state": "UNAVAILABLE",
                    "record_count": 0, "records": [],
                },
            ):
                with self.assertRaises(urllib.error.HTTPError) as caught:
                    urllib.request.urlopen(
                        f"http://127.0.0.1:{httpd.server_port}"
                        "/api/anatomy/v1/brain/ancient-math",
                        timeout=5,
                    )
                self.assertEqual(caught.exception.code, 503)
                self.assertEqual(
                    json.loads(caught.exception.read())["state"], "UNAVAILABLE"
                )
        finally:
            httpd.shutdown()
            httpd.server_close()
            worker.join(timeout=5)

    def test_historical_catalog_does_not_modify_locked_registry(self):
        source = (ROOT / "ancient_math_atlas.py").read_text(encoding="utf-8")
        self.assertNotIn("import requests", source)
        self.assertNotIn("urllib.request", source)
        self.assertNotIn("eval(", source)
        self.assertNotIn("exec(", source)
        self.assertTrue((ROOT / "docs" / "ANCIENT_MATHEMATICS_ATLAS.md").is_file())


if __name__ == "__main__":
    unittest.main()
