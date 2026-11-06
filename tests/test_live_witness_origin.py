# SPDX-License-Identifier: Apache-2.0
"""The Holographic v7 live witness reads back on the Hub-reported hf.space host.

Runs the workflow's real "Wait for exact source-bound Holographic v7" bash step
with stand-ins for the Hub lookup (judged by the real exact_space_host()), curl
and git. The declared alias answers 404, as it does on the Hub today; the step
must read back only on the exact origin the Hub reports for SPACE_ID, record
both origins in its receipt, and, when the Hub reports no exact hf.space origin,
probe nothing and still write an UNAVAILABLE receipt.

Not covered: the real Hub and hf.space answers (the scheduled live job observes
those) and the artifact-upload step.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
WITNESS = ROOT / ".github/workflows/holographic-v7-live-witness.yml"
SPACE = "betterwithage/anatomy"
DECLARED = "https://betterwithage-anatomy.hf.space"
CANONICAL = "https://fixture-canonical-anatomy.hf.space"
REFUSED = "exact https hf.space origin"


WITNESS_SHA = "1" * 40
WITNESS_ROUTES = {
    "/.well-known/szl-source.json": {
        "source": {"repository": "szl-holdings/anatomy", "commit": WITNESS_SHA},
        "alignment_state": "SOURCE_BOUND_DEPLOYMENT", "deployment": {"hf_revision": "2" * 40},
    },
    "/api/anatomy/v1/holographic-v7": {
        "state": "SOURCE_BOUND_READ_ONLY", "ready": True, "surface": "LIVING_ANATOMY_HOLOGRAPHIC_V7",
        "claims": {"content_exposed": False, "weights_trained": False, "claim_promoted": False,
                   "private_graph_used": False, "execution_performed": False, "human_review_required": True},
    },
    "/api/anatomy/v1/frontier/status": {
        "state": "SOURCE_BOUND_REVIEW_MEMORY", "second_brain_source_repository": "szl-holdings/szl-second-brain",
        "second_brain_source_revision": "3" * 40, "candidate_set_sha256": "4" * 64, "candidate_count": 144,
        "formula_atlas": {"attributed_formula_count": 30, "executable_formula_count": 21, "quant_domain_count": 9,
                          "locked_proven_formula_count": 8, "f_number_to_executable_mapping": "UNKNOWN_NOT_INFERRED"},
        "lambda": "CONJECTURE_1", "content_access": "HANDLES_ONLY", "training_authority": "NONE",
        "promotion_authority": "NONE", "execution_authority": "NONE", "private_graph_present": False,
        "raw_graph_nodes_admitted_to_gradients": 0,
    },
    "/api/anatomy/v1/frontier/formulas": {
        "content_access": "HANDLES_ONLY", "matched_count": 60, "returned_count": 48,
        "handles": [{"contentAccess": "HANDLES_ONLY", "authority": "NONE"}] * 48,
    },
    "/": ('<link data-szl-holographic-v7="style" href="/holographic-v7.css">'
          '<script data-szl-holographic-v7="script" src="/holographic-v7.js"></script>'),
}

# Stand-in for the Hub lookup: the real exact_space_host() judges what the "Hub" reported.
FAKE_LOOKUP = """\
import os, sys
sys.path.insert(0, os.environ["REAL_SCRIPTS"])
from hf_space_origin import exact_space_host
assert sys.argv[1:] == [os.environ["EXPECTED_SPACE_ID"]], sys.argv
try:
    print(exact_space_host(os.environ["FAKE_HUB_HOST"]))
except RuntimeError as error:
    print(f"hf_space_origin: RuntimeError: {error}", file=sys.stderr)
    raise SystemExit(1)
"""

FAKE_CURL = """\
import json, os, sys, urllib.parse
url = sys.argv[-1]
with open(os.environ["CURL_LOG"], "a", encoding="utf-8") as log:
    log.write(url + "\\n")
routes = json.loads(os.environ["FAKE_ROUTES"])
parts = urllib.parse.urlsplit(url)
if f"{parts.scheme}://{parts.netloc}" == os.environ["SERVED_ORIGIN"] and parts.path in routes:
    body = routes[parts.path]
    sys.stdout.write(body if isinstance(body, str) else json.dumps(body))
    raise SystemExit(0)
print(f"curl: (22) The requested URL returned error: 404", file=sys.stderr)
raise SystemExit(22)
"""


@unittest.skipUnless(shutil.which("bash"), "the witness step is a bash script; bash is not installed")
class WitnessStepTest(unittest.TestCase):
    """Runs the workflow's real 'Wait for exact source-bound Holographic v7' script."""

    @classmethod
    def setUpClass(cls) -> None:
        text = WITNESS.read_text(encoding="utf-8")
        cls.env = dict(re.findall(r"^  (SPACE_ID|LIVE_ORIGIN|RECEIPT): (\S+)$", text, re.MULTILINE))
        lines = text.splitlines()
        start = lines.index("      - name: Wait for exact source-bound Holographic v7")
        run = next(i for i in range(start, len(lines)) if lines[i] == "        run: |")
        body: list[str] = []
        for line in lines[run + 1:]:
            if line.strip() and not line.startswith("          "):
                break
            body.append(line[10:])
        cls.script = "\n".join(body).rstrip() + "\n"

    def setUp(self) -> None:
        self.assertEqual({"SPACE_ID": SPACE, "LIVE_ORIGIN": DECLARED,
                          "RECEIPT": "reports/holographic-v7-live-witness.json"}, self.env)
        self.assertTrue(self.script.startswith("set -euo pipefail\n"), self.script[:80])
        self.assertIn('python scripts/hf_space_origin.py "$SPACE_ID"', self.script)

    def run_step(self, hub_host: str, served_origin: str):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            bin_dir = work / "bin"
            bin_dir.mkdir()
            (work / "scripts").mkdir()
            (work / "scripts/hf_space_origin.py").write_text(FAKE_LOOKUP, encoding="utf-8")
            for name, content in (
                ("curl", f"#!{sys.executable}\n{FAKE_CURL}"),
                ("git", '#!/bin/sh\n[ "$1 $2" = "rev-parse HEAD" ] && { echo "%s"; exit 0; }\nexit 2\n'
                 % WITNESS_SHA),
                ("python", f'#!/bin/sh\nexec "{sys.executable}" "$@"\n'),
            ):
                tool = bin_dir / name
                tool.write_text(content, encoding="utf-8")
                tool.chmod(0o700)
            scratch = work / "live"
            script = work / "step.sh"
            script.write_text(self.script.replace("/tmp/anatomy-v7-live", str(scratch)), encoding="utf-8")
            curl_log = work / "curl.log"
            curl_log.touch()
            env = {
                "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}",
                "HOME": tmp, **self.env,
                "REAL_SCRIPTS": str(ROOT / "scripts"), "EXPECTED_SPACE_ID": SPACE,
                "FAKE_HUB_HOST": hub_host, "SERVED_ORIGIN": served_origin,
                "FAKE_ROUTES": json.dumps(WITNESS_ROUTES), "CURL_LOG": str(curl_log),
            }
            result = subprocess.run(
                ["bash", "--noprofile", "--norc", "-eo", "pipefail", str(script)],
                cwd=work, env=env, capture_output=True, text=True, timeout=120, check=False,
            )
            receipt_path = work / self.env["RECEIPT"]
            receipt = json.loads(receipt_path.read_text(encoding="utf-8")) if receipt_path.is_file() else None
            requested = curl_log.read_text(encoding="utf-8").splitlines()
        return result, receipt, requested

    def test_unrouted_declared_alias_still_proves_the_hub_reported_host(self) -> None:
        result, receipt, requested = self.run_step(CANONICAL, CANONICAL)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("LIVE", receipt["state"])
        self.assertEqual(SPACE, receipt["space"])
        self.assertEqual(CANONICAL, receipt["origin"])
        self.assertEqual(DECLARED, receipt["declared_origin"])
        self.assertEqual(WITNESS_SHA, receipt["observed_source_revision"])
        self.assertIsNone(receipt["failure_reason"])
        self.assertEqual(5, len(requested))
        self.assertTrue(all(url.startswith(CANONICAL + "/") for url in requested), requested)
        self.assertIn(f"::notice::Hub reports {SPACE} on {CANONICAL}", result.stdout)

    def test_declared_host_is_read_back_when_the_hub_reports_it(self) -> None:
        result, receipt, requested = self.run_step(DECLARED, DECLARED)
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        self.assertEqual("LIVE", receipt["state"])
        self.assertEqual(DECLARED, receipt["origin"])
        self.assertEqual(DECLARED, receipt["declared_origin"])
        self.assertTrue(all(url.startswith(DECLARED + "/") for url in requested), requested)
        self.assertNotIn("::notice::", result.stdout)

    def test_non_hf_space_host_fails_closed_unprobed_with_a_receipt(self) -> None:
        result, receipt, requested = self.run_step("https://evil.example/anatomy", "https://evil.example")
        self.assertEqual(1, result.returncode, result.stdout + result.stderr)
        self.assertEqual([], requested)
        self.assertEqual("UNAVAILABLE", receipt["state"])
        self.assertIsNone(receipt["origin"])
        self.assertEqual(DECLARED, receipt["declared_origin"])
        self.assertIn(REFUSED, receipt["failure_reason"])
        self.assertIn(f"::error::the Hub reported no {REFUSED} for {SPACE}", result.stdout)
        self.assertIn("hf_space_origin: RuntimeError", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
