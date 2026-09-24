from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import sys
import threading
import unittest
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server


# Minimal selected fields from public responses observed 2026-09-24. Additional
# diagnostic fields must never flow into the returned measured projection.
HONESTY = {"organ": "a11oy", "git_sha": "fe46a6da0dd14a158f56a86a3e1b24cc319ac02b",
           "doctrine_lock": {"state": "LOCKED"}, "locked_formula_count": 8,
           "private_diagnostic": "must-not-appear"}
REJECTION = {"service": "public.verify.receipt", "ok": False, "error": "no_input", "verdict": "NO_INPUT"}
UNKNOWN_ORGANS = {"ok": True, "surface": "szl-organ-integrity", "body": {
    "state": "UNKNOWN", "live": False, "blocked": False, "live_count": None,
    "organs": [], "energy": "UNAVAILABLE"}}
# Source-derived fixture (not a witnessed runtime response):
# szl-holdings/killinchu@0fa0fdf5, killinchu_public_route_repair.py:705-734.
KILLINCHU_EVIDENCE = {
    "schemaVersion": "szl.vertical-conformance.evidence.v1", "service": "killinchu",
    "surface": "vessels", "evidenceState": "PARTIAL",
    "gitSha": "0fa0fdf5ff2c47283893152ef2b333385eab535c", "receipts": [],
    "releaseReceipt": {"state": "UNAVAILABLE", "reason": "NO_MATCHED_GITHUB_OIDC_ATTESTATION"},
    "limitations": ["No portable cross-repository root-to-target DSSE receipt pair is exposed by this deployment."],
}


class Response(io.BytesIO):
    def __init__(self, body: bytes, status=200, content_type="application/json"):
        super().__init__(body)
        self.status = status
        self.headers = {"Content-Type": content_type}


class DependencyObservationsTest(unittest.TestCase):
    def probe(self, identity="a11oy.honesty", payload=HONESTY, *, status=200,
              content_type="application/json", raw=None, error=None):
        dep = next(row for row in server.DEPENDENCIES if row["id"] == identity)
        body = raw if raw is not None else json.dumps(payload).encode()
        response = Response(body, status, content_type)
        effect = error
        if status >= 400 and error is None:
            effect = urllib.error.HTTPError(str(dep["url"]), status, "diagnostic", response.headers, response)
        with mock.patch.object(server.urllib.request, "urlopen", return_value=response, side_effect=effect):
            result = server._probe_dependency(dep)
        if error is None:
            self.assertTrue(response.closed)
        self.assertEqual(server.DEPENDENCY_OBSERVATION_CONTRACT, result["observation_contract"])
        self.assertIn("observed_at", result)
        self.assertGreaterEqual(result["latency_ms"], 0)
        self.assertEqual(result["contract_state"] == "AVAILABLE", result["contract_validated"])
        return result

    def test_html_200_is_reachable_but_not_a_live_json_contract(self):
        row = self.probe(raw=b"<html>SPA fallback</html>", content_type="text/html")
        self.assertEqual("REACHABLE", row["transport_state"])
        self.assertEqual("INVALID_RESPONSE", row["contract_state"])
        self.assertEqual("UNAVAILABLE", row["evidence_state"])
        self.assertFalse(row["contract_validated"])

    def test_public_honesty_fixture_returns_selected_fields_and_digest(self):
        row = self.probe()
        self.assertEqual("MEASURED", row["evidence_state"])
        self.assertEqual("REPORTED", row["posture_state"])
        self.assertEqual(8, row["measured"]["locked_formula_count"])
        self.assertEqual(HONESTY["git_sha"], row["measured"]["source_revision"])
        self.assertEqual(server._sha256(json.dumps(HONESTY).encode()), row["response_sha256"])
        self.assertNotIn("must-not-appear", json.dumps(row))

    def test_arbitrary_json_or_wrong_typed_fields_do_not_establish_contract(self):
        for payload in ({}, [], {"ok": True}, {**HONESTY, "git_sha": "main"},
                        {**HONESTY, "locked_formula_count": True}):
            with self.subTest(payload=payload):
                self.assertEqual("INVALID_RESPONSE", self.probe(payload=payload)["contract_state"])

    def test_expected_verifier_400_is_input_rejection_not_receipt_verification(self):
        row = self.probe("a11oy.public-verifier", REJECTION, status=400)
        self.assertEqual("AVAILABLE", row["contract_state"])
        self.assertEqual("MEASURED", row["evidence_state"])
        self.assertFalse(row["measured"]["receipt_verified"])
        self.assertEqual("REJECTED_INVALID_INPUT", row["measured"]["verification_result"])

    def test_arbitrary_400_and_success_to_empty_verifier_request_are_not_valid(self):
        for status, body in ((400, {"error": "bad request"}), (200, REJECTION)):
            self.assertFalse(self.probe("a11oy.public-verifier", body, status=status)["contract_validated"])

    def test_rate_limit_never_claims_available_even_with_valid_body(self):
        row = self.probe("a11oy.public-verifier", REJECTION, status=429)
        self.assertEqual("RATE_LIMITED", row["contract_state"])
        self.assertEqual("UNAVAILABLE", row["evidence_state"])
        self.assertEqual({}, row["measured"])

    def test_real_unknown_empty_organ_bind_remains_unknown(self):
        row = self.probe("a11oy.organ-integrity", UNKNOWN_ORGANS)
        self.assertTrue(row["contract_validated"])
        self.assertEqual("UNKNOWN", row["posture_state"])
        self.assertEqual("UNAVAILABLE", row["evidence_state"])
        self.assertEqual([], row["measured"]["organs"])
        self.assertIsNone(row["measured"]["live_count"])

    def test_live_requires_nonempty_consistent_organ_measurements(self):
        fixture = copy.deepcopy(UNKNOWN_ORGANS)
        fixture["body"].update(state="LIVE", live=True, live_count=1,
                               organs=[{"id": "brain", "status": "LIVE", "detail": "must-not-appear"}])
        row = self.probe("a11oy.organ-integrity", fixture)
        self.assertEqual("LIVE", row["evidence_state"])
        self.assertEqual("OBSERVED_LIVE", row["posture_state"])
        self.assertNotIn("must-not-appear", json.dumps(row))
        fixture["body"]["state"] = "UNKNOWN"
        self.assertEqual("UNAVAILABLE", self.probe("a11oy.organ-integrity", fixture)["evidence_state"])
        fixture["body"]["live_count"] = 2
        self.assertFalse(self.probe("a11oy.organ-integrity", fixture)["contract_validated"])

    def test_blocked_organ_measurements_are_measured_without_live_claim(self):
        fixture = copy.deepcopy(UNKNOWN_ORGANS)
        fixture["body"].update(state="BLOCKED", blocked=True, live_count=0,
                               organs=[{"id": "brain", "status": "DOWN"}])
        row = self.probe("a11oy.organ-integrity", fixture)
        self.assertEqual("MEASURED", row["evidence_state"])
        self.assertEqual("BLOCKED", row["posture_state"])

    def test_nonlive_measurements_are_observed_degraded_rather_than_unknown(self):
        fixture = copy.deepcopy(UNKNOWN_ORGANS)
        fixture["body"].update(state="DEGRADED", live=False, live_count=0,
                               organs=[{"id": "brain", "status": "DOWN"}])
        row = self.probe("a11oy.organ-integrity", fixture)
        self.assertEqual("MEASURED", row["evidence_state"])
        self.assertEqual("OBSERVED_DEGRADED", row["posture_state"])
        # An upstream live flag alone cannot override its own DEGRADED state.
        fixture["body"].update(live=True, live_count=1, organs=[{"id": "brain", "status": "LIVE"}])
        row = self.probe("a11oy.organ-integrity", fixture)
        self.assertEqual("MEASURED", row["evidence_state"])
        self.assertEqual("OBSERVED_DEGRADED", row["posture_state"])

    def test_malformed_and_oversized_json_fail_closed(self):
        for raw, code in ((b'{"partial":', "MALFORMED_JSON"),
                          (b"x" * (server.DEPENDENCY_MAX_BYTES + 50), "RESPONSE_TOO_LARGE")):
            row = self.probe(raw=raw)
            self.assertEqual(code, row["error"])
            self.assertEqual("UNAVAILABLE", row["evidence_state"])
            self.assertLessEqual(row["response_bytes"], server.DEPENDENCY_MAX_BYTES + 1)

    def test_error_statuses_and_network_failures_do_not_leak_diagnostics(self):
        for status, state in ((404, "MISSING"), (401, "ACCESS_DENIED"), (503, "DEGRADED")):
            row = self.probe(status=status)
            self.assertEqual(state, row["contract_state"])
            self.assertNotIn("must-not-appear", json.dumps(row))
        for exc, code in ((TimeoutError("must-not-appear"), "TIMEOUT"),
                          (urllib.error.URLError("must-not-appear"), "NETWORK_ERROR")):
            row = self.probe(error=exc)
            self.assertEqual(code, row["error"])
            self.assertEqual("UNREACHABLE", row["transport_state"])
            self.assertNotIn("must-not-appear", json.dumps(row))

    def test_unpinned_contract_and_html_browser_surface_remain_unknown(self):
        row = self.probe("receipt-verifier.space", content_type="text/html")
        self.assertEqual("UNKNOWN", row["contract_state"])
        self.assertFalse(row["contract_validated"])
        with self.assertRaisesRegex(ValueError, "UNPINNED_CONTRACT"):
            server._dependency_measurement("unversioned-json", 200, HONESTY)

    def test_killinchu_partial_source_contract_is_measured_not_live(self):
        fixture = {**KILLINCHU_EVIDENCE, "private_diagnostic": "must-not-appear"}
        row = self.probe("killinchu.evidence", fixture)
        self.assertEqual("https://szlholdings-killinchu.hf.space/evidence", row["url"])
        self.assertTrue(row["contract_validated"])
        self.assertEqual("MEASURED", row["evidence_state"])
        self.assertEqual("REPORTED", row["posture_state"])
        self.assertEqual({"service": "killinchu", "surface": "vessels",
                          "source_revision": KILLINCHU_EVIDENCE["gitSha"],
                          "reported_evidence_state": "PARTIAL", "receipt_count": 0}, row["measured"])
        self.assertNotIn("must-not-appear", json.dumps(row))
        self.assertNotIn("releaseReceipt", row["measured"])

    def test_killinchu_rejects_wrong_source_schema_and_malformed_fields(self):
        for field, value in (("gitSha", "main"), ("gitSha", None), ("service", "a11oy"),
                             ("surface", "finance"), ("schemaVersion", "unknown/v1"),
                             ("evidenceState", "LIVE"), ("receipts", {}),
                             ("releaseReceipt", None), ("limitations", "unchecked")):
            with self.subTest(field=field, value=value):
                row = self.probe("killinchu.evidence", {**KILLINCHU_EVIDENCE, field: value})
                self.assertFalse(row["contract_validated"])
                self.assertEqual("UNAVAILABLE", row["evidence_state"])

    def test_slow_body_hits_deadline_and_closes_response(self):
        dep = server.DEPENDENCIES[0]
        response = Response(json.dumps(HONESTY).encode())
        with mock.patch.object(server.urllib.request, "urlopen", return_value=response), \
             mock.patch.object(server.time, "monotonic", side_effect=[0, 5, 5]):
            row = server._probe_dependency(dep)
        self.assertTrue(response.closed)
        self.assertEqual("TIMEOUT", row["error"])
        self.assertEqual("REACHABLE", row["transport_state"])
        self.assertFalse(row["contract_validated"])

    def test_observation_counts_do_not_promote_unknown_contracts(self):
        measured = self.probe()
        unknown = self.probe("a11oy.organ-integrity", UNKNOWN_ORGANS)
        rejection = self.probe("a11oy.public-verifier", REJECTION, status=400)
        rows = {"a11oy.honesty": measured, "a11oy.public-verifier": rejection}
        with mock.patch.object(server, "_probe_cache", {"at": 0.0, "value": None}), \
             mock.patch.object(server, "_probe_dependency", side_effect=lambda dep: rows.get(dep["id"], unknown)):
            observation = server._dependency_evidence(force=True)
        self.assertEqual("MIXED", observation["evidence_state"])
        self.assertEqual(0, observation["summary"]["live"])
        self.assertEqual(2, observation["summary"]["measured"])

    def test_concurrent_forced_refresh_shares_one_bounded_batch(self):
        entered = threading.Event()
        release = threading.Event()
        clock = [1.0]
        calls = []
        def probe(dep):
            calls.append(dep["id"])
            entered.set()
            self.assertTrue(release.wait(3))
            return {**dep, "contract_validated": True, "evidence_state": "UNAVAILABLE",
                    "posture_state": "UNKNOWN", "transport_state": "REACHABLE"}
        with mock.patch.object(server, "_probe_cache", {"at": 0.0, "value": None}), \
             mock.patch.object(server, "_probe_dependency", side_effect=probe), \
             mock.patch.object(server.time, "monotonic", side_effect=lambda: clock[0]):
            with ThreadPoolExecutor(max_workers=6) as pool:
                futures = [pool.submit(server._dependency_evidence, True) for _ in range(6)]
                self.assertTrue(entered.wait(3))
                clock[0] = 2.0
                release.set()
                results = [future.result(timeout=3) for future in futures]
            self.assertEqual(len(server.DEPENDENCIES), len(calls))
            self.assertTrue(all(item is results[0] for item in results))
            self.assertEqual(0, results[0]["summary"]["live"])
            self.assertEqual(0, results[0]["summary"]["measured"])
            self.assertEqual(5, results[0]["summary"]["validated"])


if __name__ == "__main__":
    unittest.main()
