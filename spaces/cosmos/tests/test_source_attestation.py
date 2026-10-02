import functools
import json
import os
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server  # noqa: E402


class SourceAttestationTests(unittest.TestCase):
    def test_unknown_source_does_not_claim_parity(self):
        with patch.dict(os.environ, {"SPACE_REPOSITORY_COMMIT": "a" * 40}):
            payload = server.build_attestation(
                server.SPACE_ID,
                server.SOURCE_OBSERVATION,
                "UNKNOWN_SOURCE_RELATION",
            )
        self.assertEqual("szl.deployment-source/v1", payload["schema"])
        self.assertEqual("a" * 40, payload["deployment"]["hf_revision"])
        self.assertEqual("MEASURED", payload["deployment"]["revision_state"])
        self.assertEqual("UNKNOWN", payload["source"]["state"])
        self.assertIsNone(payload["source"]["repository"])
        self.assertEqual("NOT_CLAIMED", payload["claims"]["github_parity"])
        self.assertEqual("NOT_CLAIMED", payload["claims"]["reproducible_build"])

    def test_well_known_route_returns_uncacheable_json(self):
        handler = functools.partial(server.HardenedHandler, directory=str(ROOT))
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            with patch.dict(os.environ, {"SPACE_REPOSITORY_COMMIT": "b" * 40}):
                with urlopen(
                    f"http://127.0.0.1:{httpd.server_port}/.well-known/szl-source.json",
                    timeout=3,
                ) as response:
                    payload = json.load(response)
                    self.assertEqual(200, response.status)
                    self.assertEqual("no-store", response.headers["Cache-Control"])
                    self.assertEqual("COMPUTED", response.headers["X-SZL-Evidence-State"])
                    self.assertEqual("READ_ONLY", response.headers["X-SZL-Authority-State"])
                    self.assertEqual("b" * 40, payload["deployment"]["hf_revision"])
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
