"""Exercise the production HTTP handler, including its route-specific limits."""
from __future__ import annotations

import ast
import copy
import json
import http.client
import sys
import threading
import unittest
import urllib.request
from contextlib import ExitStack
from pathlib import Path
from typing import Any
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import frontier_runtime
import living_runtime
import scripts.materialize_second_brain as materializer
import test_second_brain_runtime as fixtures
from second_brain_runtime import PublicSecondBrain


class LivingFrontierContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = fixtures.PublicSecondBrainTest()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        output = self.fixture.snapshot / "http-materialized"
        with patch.object(materializer, "resolve_revision", return_value="a" * 40), patch.object(
            materializer,
            "request_bytes",
            side_effect=lambda url, **kwargs: (self.fixture.snapshot / url.rsplit("/", 1)[1]).read_bytes(),
        ):
            materializer.materialize(output)
        self.patches = self.enterContext(ExitStack())
        self.patches.enter_context(patch.multiple(
            frontier_runtime,
            STATE_PATH=output / "frontier-state.v1.json",
            CANDIDATES_PATH=output / "frontier-candidates.public.jsonl",
            SOURCE_PATH=output / "source.json",
        ))
        self.patches.enter_context(patch.multiple(
            living_runtime,
            FRONTIER_ATLAS=frontier_runtime.FrontierAtlas(),
            BRAIN=PublicSecondBrain(output),
        ))
        self.httpd = living_runtime.make_server("127.0.0.1", 0)
        self.worker = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.worker.start()
        self.addCleanup(self._stop_server)
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}"

    def _stop_server(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self.worker.join(timeout=5)

    def _get(self, route: str) -> dict:
        with urllib.request.urlopen(self.base + route, timeout=5) as response:
            self.assertEqual(200, response.status)
            return json.load(response)

    def test_formula_route_honors_48_and_bounds_invalid_limits(self) -> None:
        for suffix, expected in (("", 48), ("?k=48", 48), ("?k=1000", 48), ("?k=0", 1), ("?k=invalid", 6)):
            with self.subTest(query=suffix):
                payload = self._get("/api/anatomy/v1/frontier/formulas" + suffix)
                self.assertEqual(61, payload["matched_count"])
                self.assertEqual(expected, payload["returned_count"])
                self.assertEqual(expected, len(payload["handles"]))
                self.assertTrue(all(handle["authority"] == "NONE" for handle in payload["handles"]))
                self.assertTrue(all("content" not in handle and "text" not in handle for handle in payload["handles"]))

    def test_frontier_and_brain_keep_their_separate_limits(self) -> None:
        frontier = self._get("/api/anatomy/v1/frontier/handles?k=48")
        brain = self._get("/api/anatomy/v1/brain/search?q=public%20knowledge&k=48")
        self.assertEqual(48, frontier["returned_count"])
        self.assertEqual(24, len(brain["handles"]))

    def test_pipeline_get_is_local_and_preserves_unavailable_evidence(self) -> None:
        connection = http.client.HTTPConnection("127.0.0.1", self.httpd.server_address[1], timeout=5)
        self.addCleanup(connection.close)
        with patch("urllib.request.urlopen", side_effect=AssertionError("GET must not fetch or execute")):
            connection.request("GET", "/api/anatomy/v1/brain/pipeline?refresh=1")
            response = connection.getresponse()
            payload = json.loads(response.read())
        self.assertEqual(200, response.status)
        self.assertTrue(payload["ready"])
        self.assertEqual("PARTIAL", payload["state"])
        self.assertEqual(575, payload["rag"]["chunk_count"])
        self.assertEqual("UNAVAILABLE", payload["upstream"]["state"])
        self.assertFalse(payload["execution_authorized"])
        self.assertTrue(all(value == "NONE" for value in payload["authority"].values()))

    def _publisher_pipeline_check(self, payload: dict, neural: dict) -> None:
        """Run the publisher's actual verification block without importing its SDK."""
        source = Path("scripts/sync_hf_creator_profile.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
        body = next(node.body for node in ast.walk(functions["verify_live"])
                    if isinstance(node, ast.Try))
        start = next(i for i, node in enumerate(body) if isinstance(node, ast.Assign)
                     and any(isinstance(target, ast.Name) and target.id == "pipeline"
                             for target in node.targets))
        end = next(i for i in range(start, len(body))
                   if any(isinstance(node, ast.Name) and node.id == "neural" for node in ast.walk(body[i]))
                   and any(isinstance(node, ast.Constant) and node.value == "view_sha256"
                           for node in ast.walk(body[i])))
        helpers = [functions[name] for name in ("assert_handles_only", "assert_pipeline_metadata_only")
                   if name in functions]
        namespace = {
            "Any": Any, "json": json, "LIVE_BASE": self.base,
            "get_json": lambda _url: payload,
            "brain_revision": living_runtime.BRAIN.source_revision,
            "candidate_set_sha256": living_runtime.BRAIN.frontier_candidate_set_sha256,
            "pipeline_dependency": {}, "neural": neural,
        }
        executable = ast.Module(body=helpers + body[start:end + 1], type_ignores=[])
        exec(compile(executable, str(Path("scripts/sync_hf_creator_profile.py")), "exec"), namespace)

    def test_publisher_accepts_the_real_metadata_pipeline_response(self) -> None:
        payload = self._get("/api/anatomy/v1/brain/pipeline")
        neural = self._get("/api/anatomy/v1/brain/neural-quant-v7?k=12")
        self.assertNotIn("handles", payload, "The pipeline is a metadata envelope")
        self.assertEqual("UNAVAILABLE", payload["upstream"]["state"])
        self._publisher_pipeline_check(payload, neural)

    def test_publisher_rejects_corpus_fields_in_pipeline_metadata(self) -> None:
        payload = self._get("/api/anatomy/v1/brain/pipeline")
        neural = self._get("/api/anatomy/v1/brain/neural-quant-v7?k=12")
        for field in ("content", "text", "TEXT"):
            with self.subTest(field=field):
                changed = copy.deepcopy(payload)
                changed["upstream"]["unexpected"] = [{field: "synthetic prohibited field"}]
                with self.assertRaises(AssertionError):
                    self._publisher_pipeline_check(changed, neural)
        for access in (None, "FULL_CONTENT"):
            with self.subTest(content_access=access):
                changed = copy.deepcopy(payload)
                changed["content_access"] = access
                with self.assertRaises(AssertionError):
                    self._publisher_pipeline_check(changed, neural)


if __name__ == "__main__":
    unittest.main()
