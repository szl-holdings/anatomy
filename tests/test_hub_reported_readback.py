# SPDX-License-Identifier: Apache-2.0
"""Live readback follows the exact hf.space host the Hub reports for the declared Space.

The declared creator-profile id stays ``betterwithage/anatomy`` (the owner kept it
in szl-holdings/a11oy#3239). When the Hub serves that id from another hf.space
label, the publisher, the refinement readback and the Holographic v7 witness read
back on the Hub-reported host, keep the declared origin beside it, and fail closed
before any readback when the Hub reports no exact ``https://<label>.hf.space``.
This module covers the shared resolver, the publisher and the refinement readback.

Standard library only (container-contract.yml installs no huggingface_hub): the
publisher's functions are extracted with ``ast`` like tests/test_publisher_noop.py,
and the network is faked. The witness step is exercised in
tests/test_live_witness_origin.py.

Not covered: the real Hub and hf.space answers. Those are observed by the
hf-sync.yml and holographic-v7-live-witness.yml runs on main.
"""
from __future__ import annotations

import ast
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
import unittest.mock as mock
import urllib.error

ROOT = Path(__file__).resolve().parents[1]
PUBLISHER = ROOT / "scripts/sync_hf_creator_profile.py"
SPACE = "betterwithage/anatomy"
DECLARED = "https://betterwithage-anatomy.hf.space"
CANONICAL = "https://fixture-canonical-anatomy.hf.space"
REFUSED = "exact https hf.space origin"


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


origin = load("hf_space_origin", "scripts/hf_space_origin.py")
with mock.patch.dict(sys.modules, {"hf_space_origin": origin}):
    refinement = load("verify_refinement_observatory", "scripts/verify_refinement_observatory.py")


class FakeResponse:
    def __init__(self, final_url: str, body: bytes) -> None:
        self.final_url = final_url
        self.body = body

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def geturl(self) -> str:
        return self.final_url

    def read(self, size: int = -1) -> bytes:
        return self.body if size < 0 else self.body[:size]


def not_found(url: str) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(url, 404, "Not Found", {}, io.BytesIO(b"missing"))


class ExactSpaceHostTest(unittest.TestCase):
    def test_accepts_exact_hf_space_origins(self) -> None:
        for value, expected in (
            (DECLARED, DECLARED),
            (CANONICAL, CANONICAL),
            (CANONICAL + "/", CANONICAL),
            ("  " + CANONICAL + "\n", CANONICAL),
            ("https://a.hf.space", "https://a.hf.space"),
            ("https://" + "a" * 63 + ".hf.space", "https://" + "a" * 63 + ".hf.space"),
        ):
            with self.subTest(value=value):
                self.assertEqual(expected, origin.exact_space_host(value))

    def test_refuses_everything_that_is_not_an_exact_hf_space_origin(self) -> None:
        for value in (
            None, "", 42, b"https://a.hf.space",
            "http://a.hf.space", "HTTPS://a.hf.space", "https://hf.space", "https://.hf.space",
            "https://a.hf.space.evil.example", "https://evil.example/a.hf.space",
            "https://evil.example#.hf.space", "https://evil.example?.hf.space",
            "https://user@a.hf.space", "https://a.hf.space/path", "https://a.hf.space?x=1",
            "https://a.hf.space#frag", "https://a.hf.space:443", "https://a\\b.hf.space",
            "https://a.b.hf.space", "https://-a.hf.space", "https://a-.hf.space",
            "https://a--b.hf.space", "https://A.hf.space", "https://a b.hf.space",
            "https://a\n.hf.space", "https://é.hf.space", "https://" + "a" * 64 + ".hf.space",
        ):
            with self.subTest(value=value):
                with self.assertRaisesRegex(RuntimeError, REFUSED):
                    origin.exact_space_host(value)


class HubReportedOriginTest(unittest.TestCase):
    def test_follows_the_hub_redirect_for_a_transferred_space_id(self) -> None:
        requested: list[str] = []

        def urlopen(request, timeout):
            requested.append(request.full_url)
            return FakeResponse(
                "https://huggingface.co/api/spaces/fixture-canonical/anatomy",
                json.dumps({"id": "fixture-canonical/anatomy", "host": CANONICAL}).encode(),
            )

        with mock.patch.object(origin.urllib.request, "urlopen", urlopen):
            self.assertEqual(CANONICAL, origin.hub_reported_origin(SPACE))
        self.assertEqual(["https://huggingface.co/api/spaces/betterwithage/anatomy"], requested)

    def test_refuses_a_lookup_redirected_off_the_hub_api(self) -> None:
        for final in (
            "https://evil.example/api/spaces/fixture/anatomy",
            "http://huggingface.co/api/spaces/fixture/anatomy",
            "https://huggingface.co/spaces/fixture/anatomy",
            "https://huggingface.co.evil.example/api/spaces/fixture/anatomy",
        ):
            with self.subTest(final=final):
                with mock.patch.object(
                    origin.urllib.request, "urlopen",
                    lambda request, timeout, final=final: FakeResponse(
                        final, json.dumps({"host": CANONICAL}).encode()),
                ):
                    with self.assertRaisesRegex(RuntimeError, "redirected off"):
                        origin.hub_reported_origin(SPACE)

    def test_refuses_a_reported_host_that_is_not_an_exact_hf_space_origin(self) -> None:
        api = "https://huggingface.co/api/spaces/betterwithage/anatomy"
        for payload, error in (
            ({"host": "https://evil.example/anatomy"}, REFUSED),
            ({"host": None}, REFUSED),
            ({}, REFUSED),
            ([{"host": CANONICAL}], "JSON object"),
        ):
            with self.subTest(payload=payload):
                with mock.patch.object(
                    origin.urllib.request, "urlopen",
                    lambda request, timeout, payload=payload: FakeResponse(
                        api, json.dumps(payload).encode()),
                ):
                    with self.assertRaisesRegex(RuntimeError, error):
                        origin.hub_reported_origin(SPACE)

    def test_refuses_an_oversized_lookup_response(self) -> None:
        body = b" " * origin.MAX_RESPONSE_BYTES + json.dumps({"host": CANONICAL}).encode()
        with mock.patch.object(
            origin.urllib.request, "urlopen",
            lambda request, timeout: FakeResponse(
                "https://huggingface.co/api/spaces/betterwithage/anatomy", body),
        ):
            with self.assertRaisesRegex(RuntimeError, "byte budget"):
                origin.hub_reported_origin(SPACE)

    def test_refuses_a_malformed_space_id_before_any_request(self) -> None:
        urlopen = mock.Mock(side_effect=AssertionError("no request may be made"))
        with mock.patch.object(origin.urllib.request, "urlopen", urlopen):
            for space_id in ("", "anatomy", "a/b/c", "../etc", "a/..", "a/b?x=1", "a/b#f", "a /b"):
                with self.subTest(space_id=space_id):
                    with self.assertRaisesRegex(RuntimeError, "not a Hub Space id"):
                        origin.hub_reported_origin(space_id)
        urlopen.assert_not_called()

    def test_cli_prints_the_origin_or_one_line_reason(self) -> None:
        with mock.patch.object(origin, "hub_reported_origin", return_value=CANONICAL) as lookup:
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                self.assertEqual(0, origin.main([SPACE]))
        lookup.assert_called_once_with(SPACE)
        self.assertEqual(CANONICAL + "\n", out.getvalue())
        self.assertEqual("", err.getvalue())

        for failure in (RuntimeError("Space host is not an exact https hf.space origin"),
                        not_found("https://huggingface.co/api/spaces/betterwithage/anatomy"),
                        ValueError("Expecting value")):
            with self.subTest(failure=type(failure).__name__):
                with mock.patch.object(origin, "hub_reported_origin", side_effect=failure):
                    out, err = io.StringIO(), io.StringIO()
                    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                        self.assertEqual(1, origin.main([SPACE]))
                self.assertEqual("", out.getvalue())
                self.assertEqual(1, err.getvalue().count("\n"))
                self.assertTrue(err.getvalue().startswith("hf_space_origin: " + type(failure).__name__))

        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(2, origin.main([]))
        self.assertIn("usage:", err.getvalue())


class PublisherBindingTest(unittest.TestCase):
    """The publisher's own resolve_live_base(), run without importing huggingface_hub."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tree = ast.parse(PUBLISHER.read_text(encoding="utf-8"))
        cls.functions = {node.name: node for node in cls.tree.body if isinstance(node, ast.FunctionDef)}

    def namespace(self) -> dict:
        constants = [
            node for node in self.tree.body
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name)
                and target.id in {"SPACE_ID", "LIVE_BASE", "DECLARED_LIVE_BASE"}
                for target in node.targets)
        ]
        self.assertEqual(3, len(constants))
        namespace = {"HfApi": object, "exact_space_host": origin.exact_space_host}
        module = ast.Module(body=constants + [self.functions["resolve_live_base"]], type_ignores=[])
        exec(compile(module, str(PUBLISHER), "exec"), namespace)
        self.assertEqual(SPACE, namespace["SPACE_ID"])
        self.assertEqual(DECLARED, namespace["DECLARED_LIVE_BASE"])
        self.assertEqual(DECLARED, namespace["LIVE_BASE"])
        return namespace

    def test_transferred_space_id_rebinds_readback_to_the_hub_reported_host(self) -> None:
        namespace = self.namespace()
        api = mock.Mock()
        api.space_info.return_value = SimpleNamespace(host=CANONICAL)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(CANONICAL, namespace["resolve_live_base"](api))
        api.space_info.assert_called_once_with(repo_id=SPACE)
        self.assertEqual(CANONICAL, namespace["LIVE_BASE"])
        self.assertEqual(DECLARED, namespace["DECLARED_LIVE_BASE"])
        self.assertIn(f"Hub reports {SPACE} on {CANONICAL}; declared origin is {DECLARED}", out.getvalue())

    def test_declared_host_stays_bound_when_the_hub_reports_it(self) -> None:
        namespace = self.namespace()
        api = mock.Mock()
        api.space_info.return_value = SimpleNamespace(host=DECLARED + "/")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(DECLARED, namespace["resolve_live_base"](api))
        self.assertEqual(DECLARED, namespace["LIVE_BASE"])
        self.assertEqual("", out.getvalue())

    def test_non_hf_space_host_fails_closed_and_leaves_the_binding_alone(self) -> None:
        for info in (SimpleNamespace(host="https://evil.example/anatomy"),
                     SimpleNamespace(host=None), SimpleNamespace()):
            with self.subTest(info=info):
                namespace = self.namespace()
                api = mock.Mock()
                api.space_info.return_value = info
                with self.assertRaisesRegex(RuntimeError, REFUSED):
                    namespace["resolve_live_base"](api)
                self.assertEqual(DECLARED, namespace["LIVE_BASE"])

    def test_main_binds_after_destination_and_before_publication_and_readback(self) -> None:
        main = self.functions["main"]
        lines: dict[str, list[int]] = {}
        for node in ast.walk(main):
            if isinstance(node, ast.Call):
                func = node.func
                name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
                lines.setdefault(name, []).append(node.lineno)
        self.assertEqual(1, len(lines["resolve_live_base"]))
        bound = lines["resolve_live_base"][0]
        self.assertLess(max(lines["ensure_destination"]), bound)
        for later in ("live_deploy_manifest", "create_commit", "wait_running", "verify_live"):
            with self.subTest(call=later):
                self.assertLess(bound, min(lines[later]))

    def test_every_readback_url_reads_the_rebound_module_global(self) -> None:
        verify_live = self.functions["verify_live"]
        parameters = {arg.arg for arg in verify_live.args.args}
        self.assertNotIn("LIVE_BASE", parameters)
        stores = [node for node in ast.walk(verify_live)
                  if isinstance(node, ast.Name) and node.id == "LIVE_BASE" and isinstance(node.ctx, ast.Store)]
        self.assertEqual([], stores)
        readers = [node for node in ast.walk(verify_live) if isinstance(node, ast.Call)
                   and getattr(node.func, "id", "") in {"get_json", "get_text", "get_status"}]
        self.assertTrue(readers)
        for call in readers:
            url = call.args[0]
            while isinstance(url, ast.BinOp):
                url = url.left
            with self.subTest(line=call.lineno):
                self.assertIsInstance(url, ast.Name)
                self.assertEqual("LIVE_BASE", url.id)
        literal_hosts = [node.value for node in ast.walk(verify_live)
                         if isinstance(node, ast.Constant) and isinstance(node.value, str) and "hf.space" in node.value]
        self.assertEqual([], literal_hosts)


class RefinementReadbackTest(unittest.TestCase):
    def setUp(self) -> None:
        self.local = json.loads((ROOT / "lib/refinement_source.json").read_text(encoding="utf-8"))
        cwd = os.getcwd()
        os.chdir(ROOT)  # main() reads lib/refinement_source.json from the checkout root
        self.addCleanup(os.chdir, cwd)

    def serve(self, requested: list[str]):
        routes = {
            CANONICAL + "/api/anatomy/v1/refinement/status": json.dumps({
                "content_access": "HANDLES_ONLY", "authority": "READ_ONLY",
                "state_sha256": self.local["state_sha256"],
                "source_revision": self.local["source_revision"], "pattern_count": 2,
            }).encode(),
            CANONICAL + "/api/anatomy/v1/refinement/patterns?limit=20": json.dumps({
                "content_access": "HANDLES_ONLY", "patterns": [{"id": "p1"}, {"id": "p2"}],
            }).encode(),
            CANONICAL + "/refinement-lab": b"<title>Alloy Refinement Observatory</title>",
        }

        def urlopen(request, timeout):
            url = getattr(request, "full_url", request)
            requested.append(url)
            if url in routes:
                return FakeResponse(url, routes[url])
            raise not_found(url)

        return urlopen

    def test_unrouted_declared_alias_still_proves_the_hub_reported_host(self) -> None:
        requested: list[str] = []
        out = io.StringIO()
        with mock.patch.object(refinement, "hub_reported_origin", return_value=CANONICAL) as lookup, \
                mock.patch.object(refinement.urllib.request, "urlopen", self.serve(requested)), \
                mock.patch.object(refinement.time, "sleep", side_effect=AssertionError("unexpected retry")), \
                contextlib.redirect_stdout(out):
            self.assertEqual(0, refinement.main())
        lookup.assert_called_once_with(SPACE)
        self.assertTrue(requested)
        self.assertTrue(all(url.startswith(CANONICAL + "/") for url in requested), requested)
        result = json.loads(out.getvalue().strip().splitlines()[-1])
        self.assertEqual(CANONICAL, result["origin"])
        self.assertEqual(DECLARED, result["declared_origin"])
        self.assertIs(True, result["live"])
        self.assertEqual(self.local["state_sha256"], result["state_sha256"])

    def test_non_hf_space_host_fails_closed_before_any_readback(self) -> None:
        urlopen = mock.Mock(side_effect=AssertionError("no readback may be attempted"))
        with mock.patch.object(refinement, "hub_reported_origin",
                               side_effect=RuntimeError("Space host is not an exact https hf.space origin")), \
                mock.patch.object(refinement.urllib.request, "urlopen", urlopen):
            with self.assertRaisesRegex(RuntimeError, REFUSED):
                refinement.main()
        urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
