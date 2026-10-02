import functools
import json
import os
import sys
import threading
import tempfile
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.request import urlopen, Request
from urllib.error import HTTPError


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import server  # noqa: E402


class SourceAttestationTests(unittest.TestCase):
    def test_private_paths_are_not_served_for_get_or_head(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ('.git/config', '__pycache__/server.cpython-311.pyc', 'assets/.secret', 'loose.pyc', 'index.html'):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text('fixture')
            httpd = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(server.HardenedHandler, directory=tmp))
            thread = threading.Thread(target=httpd.serve_forever, daemon=True)
            thread.start()
            base = f'http://127.0.0.1:{httpd.server_port}'
            try:
                for method in ('GET', 'HEAD'):
                    for route in ('/.git/', '/.git/config', '/%2egit/config', '/__pycache__/', '/__pycache__/server.cpython-311.pyc', '/assets/.secret', '/assets/%2esecret', '/loose.pyc'):
                        with self.subTest(method=method, route=route):
                            with self.assertRaises(HTTPError) as error:
                                urlopen(Request(base + route, method=method), timeout=3)
                            self.assertEqual(error.exception.code, 404)
                    with urlopen(Request(base + '/index.html', method=method), timeout=3) as response:
                        self.assertEqual(response.status, 200)
                    with patch.dict(os.environ, {'SPACE_REPOSITORY_COMMIT': 'b' * 40}):
                        with urlopen(Request(base + '/.well-known/szl-source.json', method=method), timeout=3) as response:
                            self.assertEqual(response.status, 200)
                            self.assertEqual(response.headers['Cache-Control'], 'no-store')
            finally:
                httpd.shutdown(); httpd.server_close(); thread.join(timeout=3)

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
