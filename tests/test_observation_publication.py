"""Exercise release checks without a Hub dependency, credentials or remote writes."""
import ast
import copy
from pathlib import Path
from types import SimpleNamespace
from typing import Any
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = "a" * 40
PARENT = "b" * 40
MARKER = "szl.anatomy-dependency-observation/v1"


class ObservationPublicationTest(unittest.TestCase):
    def setUp(self):
        tree = ast.parse((ROOT / "scripts/sync_hf_creator_profile.py").read_text(encoding="utf-8"))
        names = {"verify_dependency_observations", "publication_parent"}
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in names]
        self.assertEqual({node.name for node in functions}, names)
        self.ns = {
            "Any": Any, "HfApi": object, "SPACE_ID": "betterwithage/anatomy",
            "current_protected_main": lambda repository, token: SOURCE,
        }
        exec(compile(ast.Module(body=functions, type_ignores=[]), "<publisher checks>", "exec"), self.ns)
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        self.commit = next(node for node in main.body if isinstance(node, ast.Assign)
                           and isinstance(node.value, ast.Call)
                           and isinstance(node.value.func, ast.Attribute)
                           and node.value.func.attr == "create_commit")
        self.payload = {
            "observation_contract": MARKER, "authority_state": "READ_ONLY",
            "summary": {"total": 5, "live": 0, "measured": 0},
            "dependencies": [{
                "id": name, "observation_contract": MARKER,
                "contract_validated": False, "contract_state": "UNREACHABLE",
                "observed_at": "2026-09-24T13:00:00Z", "measured": {},
                "evidence_state": "UNAVAILABLE", "posture_state": "UNKNOWN",
            } for name in (
                "a11oy.honesty", "a11oy.public-verifier", "a11oy.organ-integrity",
                "killinchu.evidence", "receipt-verifier.space",
            )],
        }

    def check(self, payload=None):
        self.ns["verify_dependency_observations"](payload or self.payload)

    def test_honest_dependency_outage_does_not_block_a_valid_release(self):
        self.check()

    def test_unknown_organ_response_must_never_be_published_as_live(self):
        row = self.payload["dependencies"][2]
        row.update(contract_validated=True, contract_state="AVAILABLE", evidence_state="LIVE")
        row["measured"] = {"live": False, "live_count": 0}
        self.payload["summary"].update(live=1, measured=1)
        with self.assertRaises(AssertionError):
            self.check()

    def test_transport_only_response_cannot_be_promoted_to_measured(self):
        self.payload["dependencies"][0]["evidence_state"] = "MEASURED"
        self.payload["summary"]["measured"] = 1
        with self.assertRaises(AssertionError):
            self.check()

    def test_valid_live_and_measured_rows_have_reconciled_counts(self):
        row = self.payload["dependencies"][2]
        row.update(contract_validated=True, contract_state="AVAILABLE", evidence_state="LIVE",
                   posture_state="OBSERVED_LIVE", measured={"state": "LIVE", "live": True,
                   "blocked": False, "live_count": 2, "organ_count": 2,
                   "organs": [{"id": "heart", "status": "LIVE"}, {"id": "brain", "status": "LIVE"}]})
        self.payload["summary"].update(live=1, measured=1)
        self.check()
        bad = copy.deepcopy(self.payload)
        bad["summary"]["live"] = 5
        with self.assertRaises(AssertionError):
            self.check(bad)
        for altered in ({"organs": []}, {"blocked": True}, {"state": "DEGRADED"},
                        {"organs": [{"id": "heart", "status": "LIVE"}] * 2},
                        {"live_count": True}, {"organ_count": 1}):
            with self.subTest(altered=altered):
                bad = copy.deepcopy(self.payload)
                bad["dependencies"][2]["measured"].update(altered)
                with self.assertRaises(AssertionError):
                    self.check(bad)

    def test_legacy_or_duplicate_dependency_payload_is_rejected(self):
        legacy = copy.deepcopy(self.payload)
        legacy.pop("observation_contract")
        with self.assertRaises(AssertionError):
            self.check(legacy)
        self.payload["dependencies"][0] = self.payload["dependencies"][1]
        with self.assertRaises(AssertionError):
            self.check()

    def publish(self, head=PARENT, changed=False):
        calls = []
        def create_commit(**kwargs):
            calls.append(kwargs)
            if changed:
                raise RuntimeError("Hub parent conflict")
            self.assertEqual(kwargs["parent_commit"], PARENT)
            return SimpleNamespace(oid="c" * 40)
        self.ns.update(
            api=SimpleNamespace(repo_info=lambda **kw: SimpleNamespace(sha=head), create_commit=create_commit),
            repository="szl-holdings/anatomy", github_token="fixture-not-a-credential",
            source_revision=SOURCE, workflow_run_id="123", operations=[],
        )
        exec(compile(ast.Module(body=[self.commit], type_ignores=[]), "<actual publisher commit>", "exec"), self.ns)
        return calls

    def test_actual_publication_uses_exact_destination_parent(self):
        self.assertEqual(len(self.publish()), 1)

    def test_changed_source_invalid_parent_and_provider_conflict_stop_publication(self):
        with self.assertRaisesRegex(RuntimeError, "parent revision"):
            self.publish(head="")
        with self.assertRaisesRegex(RuntimeError, "Hub parent conflict"):
            self.publish(changed=True)
        self.ns["current_protected_main"] = lambda *args: "d" * 40
        with self.assertRaisesRegex(RuntimeError, "stale source"):
            self.publish()


if __name__ == "__main__":
    unittest.main()
