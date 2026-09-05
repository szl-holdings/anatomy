"""Exercise the production HTTP handler, including its route-specific limits."""
from __future__ import annotations

import json
import sys
import threading
import unittest
import urllib.request
from contextlib import ExitStack
from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
