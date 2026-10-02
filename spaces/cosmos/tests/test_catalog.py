import io
import json
import threading
import unittest
from unittest.mock import patch

from catalog import Catalog, TTL, public_stream


class Reply(io.BytesIO):
    headers = {}


class PublicCatalogTests(unittest.TestCase):
    def test_public_allowlist_and_no_authorization(self):
        rows = [{"id": "betterwithage/public", "private": False, "runtime": {"stage": "RUNNING", "sha": "abc"}},
                {"id": "betterwithage/secret", "private": True},
                {"id": "betterwithage/unknown"}, {"id": "other/public", "private": False},
                {"id": "betterwithage/x\" onclick=evil", "private": False}]
        def request(req, timeout):
            self.assertNotIn("Authorization", req.headers)
            self.assertEqual(timeout, 8)
            return Reply(json.dumps(rows).encode())
        with patch("catalog.urlopen", request):
            result = public_stream("betterwithage", "space")
        self.assertEqual(len(result["nodes"]), 1)
        self.assertEqual(result["nodes"][0]["runtime_stage"], "RUNNING")
        self.assertEqual(result["nodes"][0]["runtime_revision"], "abc")
        self.assertEqual(result["nodes"][0]["url"], "https://huggingface.co/spaces/betterwithage/public")

    def test_failure_retains_explicitly_stale_observation(self):
        now = [1.0]
        fail = [False]
        def fetch(owner, kind):
            if fail[0]:
                raise RuntimeError("do not leak token or body")
            return {"nodes": [{"id": owner+kind}], "observed_at": "then", "truncated": False}
        c = Catalog(fetch, lambda: now[0])
        c._refresh()
        c.attempt = now[0]
        self.assertEqual(c.snapshot()["state"], "FRESH")
        now[0] += TTL + 1
        fail[0] = True
        c._refresh()
        c.attempt = now[0]
        result = c.snapshot()
        self.assertEqual(result["state"], "PARTIAL")
        self.assertTrue(all(n["observation_state"] == "STALE" for n in result["nodes"]))
        self.assertNotIn("do not leak", json.dumps(result))

    def test_single_flight_and_empty_boot(self):
        entered = threading.Event()
        release = threading.Event()
        calls = []
        def fetch(owner, kind):
            calls.append((owner, kind))
            entered.set()
            release.wait(2)
            return {"nodes": [], "truncated": False}
        c = Catalog(fetch)
        first = c.snapshot()
        self.assertEqual(first["state"], "UNAVAILABLE")
        self.assertTrue(first["refreshing"])
        entered.wait(1)
        for _ in range(20):
            c.snapshot()
        release.set()
        self.assertLessEqual(len(calls), 6)

    def test_partial_catalog_never_claims_complete(self):
        c = Catalog(lambda o, k: {"nodes": [], "truncated": True})
        c._refresh()
        c.attempt = c.clock()
        self.assertEqual(c.snapshot()["state"], "PARTIAL")
        self.assertTrue(all(s["truncated"] for s in c.snapshot()["sources"]))

    def test_removals_replace_previous_public_list(self):
        c = Catalog(lambda o, k: {"nodes": [{"id": o+k}], "truncated": False})
        c._refresh()
        c.fetch = lambda o, k: {"nodes": [], "truncated": False}
        c._refresh()
        c.attempt = c.clock()
        self.assertEqual(c.snapshot()["nodes"], [])


if __name__ == "__main__":
    unittest.main()
