"""Public atlas routes must load the exact bytes bound by their source receipt."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

import frontier_runtime
import scripts.materialize_second_brain as materializer
import test_second_brain_runtime as fixtures


class FrontierSnapshotDigestTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = fixtures.PublicSecondBrainTest()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.output = self.fixture.snapshot / "receipted-atlas"
        with patch.object(materializer, "resolve_revision", return_value="a" * 40), patch.object(
            materializer,
            "request_bytes",
            side_effect=lambda url, **kwargs: (self.fixture.snapshot / url.rsplit("/", 1)[1]).read_bytes(),
        ):
            materializer.materialize(self.output)
        self.enterContext(patch.multiple(
            frontier_runtime,
            STATE_PATH=self.output / "frontier-state.v1.json",
            CANDIDATES_PATH=self.output / "frontier-candidates.public.jsonl",
            SOURCE_PATH=self.output / "source.json",
            ATLAS=frontier_runtime.FrontierAtlas(),
        ))
        self.client = self.enterContext(TestClient(frontier_runtime.app))
        self.assertEqual(200, self.client.get("/api/anatomy/v1/frontier/status").status_code)

    def _assert_public_routes_unavailable(self) -> None:
        with patch.object(frontier_runtime, "ATLAS", frontier_runtime.FrontierAtlas()):
            for route in (
                "/api/anatomy/v1/frontier/status",
                "/api/anatomy/v1/frontier/handles",
                "/api/anatomy/v1/frontier/formulas",
                "/api/anatomy/v1/frontier/ouroboros",
                "/api/anatomy/v1/holographic-v7",
            ):
                with self.subTest(route=route):
                    response = self.client.get(route)
                    self.assertEqual(503, response.status_code)
                    self.assertFalse(response.json()["ready"])
                    self.assertEqual("UNAVAILABLE", response.json()["state"])

    def test_source_manifest_digest_drift_rejects_public_readiness(self) -> None:
        path = self.output / "frontier-state.v1.json"
        state = json.loads(path.read_text(encoding="utf-8"))
        state["sources"][0]["content_sha256"] = "f" * 64
        path.write_text(json.dumps(state), encoding="utf-8")
        self._assert_public_routes_unavailable()

    def test_candidate_file_bytes_must_match_receipt_even_if_rows_do(self) -> None:
        path = self.output / "frontier-candidates.public.jsonl"
        path.write_bytes(path.read_bytes() + b"\n")
        self._assert_public_routes_unavailable()

    def test_missing_state_digest_rejects_public_readiness(self) -> None:
        path = self.output / "source.json"
        source = json.loads(path.read_text(encoding="utf-8"))
        del source["frontier_state_sha256"]
        path.write_text(json.dumps(source), encoding="utf-8")
        self._assert_public_routes_unavailable()

    def test_nested_receipt_requires_matching_raw_digests(self) -> None:
        path = self.output / "source.json"
        source = json.loads(path.read_text(encoding="utf-8"))
        source["schema"] = "szl.second-brain.snapshot/v2"
        source["frontier"] = {
            "candidate_count": source["frontier_candidate_count"],
            "source_count": source["frontier_source_count"],
            "candidate_set_sha256": source["frontier_candidate_set_sha256"],
            "state_sha256": source.pop("frontier_state_sha256"),
            "candidates_sha256": source.pop("frontier_candidates_sha256"),
        }
        path.write_text(json.dumps(source), encoding="utf-8")
        with patch.object(frontier_runtime, "ATLAS", frontier_runtime.FrontierAtlas()):
            self.assertEqual(200, self.client.get("/api/anatomy/v1/frontier/status").status_code)
        source["frontier"]["state_sha256"] = "0" * 64
        path.write_text(json.dumps(source), encoding="utf-8")
        self._assert_public_routes_unavailable()


if __name__ == "__main__":
    unittest.main()
