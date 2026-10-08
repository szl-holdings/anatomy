# SPDX-License-Identifier: Apache-2.0
"""Adversarial contract tests; every run identity below is a synthetic fixture."""
from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pipeline_observation as consumer

NOW = datetime(2026, 10, 8, 23, 0, tzinfo=timezone.utc)


def stamp(value):
    return value.isoformat().replace("+00:00", "Z")


def expected_source():
    return {
        "controller_repository": "szl-holdings/szl-ouroboros",
        "controller_revision": "b" * 40,
        "workflow": ".github/workflows/codex-continuous-frontier.yml",
        "second_brain_repository": "szl-holdings/szl-second-brain",
        "second_brain_revision": "a" * 40,
        "state_file_sha256": "1" * 64,
        "candidate_file_sha256": "2" * 64,
        "candidate_set_sha256": "3" * 64,
        "candidate_count": 141,
    }


def observation_fixture():
    value = {
        "schema": consumer.OBSERVATION_SCHEMA,
        "state": "OBSERVED", "reason": "VALIDATED_REVIEW_ATTEMPT",
        "source": expected_source(),
        "run": {"id": 123, "attempt": 1, "head_sha": "b" * 40,
                "status": "completed", "conclusion": "success",
                "url": "https://github.com/szl-holdings/szl-ouroboros/actions/runs/123",
                "updated_at": stamp(NOW)},
        "artifact": {"id": 456, "name": "ouroboros-frontier-123-1",
                     "archive_sha256": "4" * 64, "receipt_sha256": "5" * 64},
        "observation": {"bounded": True, "terminated": True, "receipt_closed": True,
                        "steps": 1, "max_budget": 1, "wall_ms": 10.5,
                        "exit": "converged", "review_state": "VALIDATED",
                        "review_sha256": "6" * 64, "recommendation_count": 1},
        "freshness": {"observed_at": stamp(NOW),
                      "expires_at": stamp(NOW + timedelta(seconds=21600)),
                      "max_age_seconds": 21600},
        "authority": dict(consumer.AUTHORITY),
        "claims": {"signature_verified": False, "review_is_accepted_truth": False,
                   "production_verified": False, "private_graph_loaded": False,
                   "measurement_scope": "RECORDED_REVIEW_ATTEMPT"},
    }
    value["observation_sha256"] = consumer.digest(value)
    return value


def dag_fixture():
    nodes = [{"id": name, "label": name.title(), "role": "worker", "authority": "READ_ONLY",
              "depends_on": [prior] if prior else [], "control_after": [],
              "side_effecting": False, "writes": []}
             for name, prior in (("observe", None), ("orient", "observe"), ("propose", "orient"),
                                 ("verify", "propose"), ("hold", "verify"))]
    graph = {"schema": "szl.governed-graph/v1", "graph_id": "fixture-review", "nodes": nodes}
    return {"schema": "szl.governed-graph.analysis/v1", "evidence_label": "MODELED",
            "execution": {"mode": "PLAN_ONLY", "authorized": False, "effectors": 0,
                          "provider_calls": 0, "writes": 0},
            "contract_digest": consumer.digest(graph), "normalized_contract": graph,
            "topology": {"node_count": 5, "layers": [[node["id"]] for node in nodes]},
            "decision": "READY_TO_ORCHESTRATE"}


def snapshot_fixture():
    return {"schema": consumer.UPSTREAM_SCHEMA,
            "authority": {**consumer.AUTHORITY, "private_graph_present": False,
                          "public_content_access": "HANDLES_ONLY"},
            "ouroboros_observation": observation_fixture(), "advisory_dag": dag_fixture()}


class PipelineSourceBindingTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "pipeline-source.json"

    def _load(self, snapshot, *, now=NOW, rehash_observation=True):
        snapshot = copy.deepcopy(snapshot)
        observation = snapshot.get("ouroboros_observation")
        if observation is not None and rehash_observation:
            observation.pop("observation_sha256", None)
            observation["observation_sha256"] = consumer.digest(observation)
        snapshot.pop("snapshot_sha256", None)
        snapshot["snapshot_sha256"] = consumer.digest(snapshot)
        raw = json.dumps(snapshot, indent=2).encode()
        wrapper = {"schema": consumer.SNAPSHOT_SCHEMA,
                   "source_repository": consumer.UPSTREAM_REPOSITORY,
                   "source_revision": "c" * 40, "source_path": consumer.UPSTREAM_PATH,
                   "source_snapshot_sha256": hashlib.sha256(raw).hexdigest(),
                   "snapshot_json": raw.decode(), "captured_at": stamp(NOW)}
        wrapper["receipt_sha256"] = consumer.digest(wrapper)
        payload = json.dumps(wrapper).encode()
        self.path.write_bytes(payload)
        return consumer.load_pipeline_snapshot(self.path, expected_source(),
                                              file_sha256=hashlib.sha256(payload).hexdigest(), now=now)

    def test_source_bound_record_and_analyzed_dag_are_inspection_only(self):
        result = self._load(snapshot_fixture())
        self.assertTrue(result["ready"])
        self.assertEqual("OBSERVED", result["state"])
        self.assertEqual("MODELED_PLAN_ONLY", result["dag"]["state"])
        self.assertFalse(result["dag"]["execution_authorized"])
        self.assertEqual("SOURCE_BOUND_PRODUCER_REPORT", result["ouroboros_observation"]["verification"])
        self.assertEqual(5, result["dag"]["node_count"])
        self.assertNotIn("normalized_contract", result["dag"])

    def test_every_brain_and_controller_input_must_match_even_after_rehash(self):
        for key in ("controller_revision", "second_brain_revision", "state_file_sha256",
                    "candidate_file_sha256", "candidate_set_sha256", "candidate_count"):
            with self.subTest(binding=key):
                snapshot = snapshot_fixture()
                old = snapshot["ouroboros_observation"]["source"][key]
                snapshot["ouroboros_observation"]["source"][key] = old + 1 if isinstance(old, int) else "f" * len(old)
                result = self._load(snapshot)
                self.assertFalse(result["ready"])
                self.assertEqual("STALE", result["state"])

    def test_expiry_uses_recorded_time_and_preserves_original_receipt_identity(self):
        snapshot = snapshot_fixture()
        original_digest = snapshot["ouroboros_observation"]["observation_sha256"]
        result = self._load(snapshot, now=NOW + timedelta(seconds=21600))
        self.assertTrue(result["ready"])
        self.assertEqual("STALE", result["state"])
        observation = result["ouroboros_observation"]
        self.assertEqual("OBSERVED", observation["recorded_state"])
        self.assertEqual(original_digest, observation["observation_sha256"])
        self.assertTrue(all(value is None for value in observation["observation"].values()))

    def test_future_timestamp_cannot_extend_validity(self):
        result = self._load(snapshot_fixture(), now=NOW - timedelta(seconds=301))
        self.assertEqual("FUTURE_OBSERVATION", result["reason"])

    def test_bad_artifact_identity_and_hash_tampering_are_rejected(self):
        snapshot = snapshot_fixture()
        snapshot["ouroboros_observation"]["artifact"]["name"] = "ouroboros-frontier-999-1"
        self.assertEqual("ARTIFACT_IDENTITY", self._load(snapshot)["reason"])
        snapshot = snapshot_fixture()
        snapshot["ouroboros_observation"]["observation"]["wall_ms"] = 99
        self.assertEqual("DIGEST_MISMATCH", self._load(snapshot, rehash_observation=False)["reason"])

    def test_unavailable_and_failed_receipts_never_keep_success_measurements(self):
        for state in consumer.STATES - {"OBSERVED"}:
            with self.subTest(state=state):
                snapshot = snapshot_fixture()
                snapshot["ouroboros_observation"]["state"] = state
                self.assertEqual("UNOBSERVED_MEASUREMENTS", self._load(snapshot)["reason"])
                snapshot["ouroboros_observation"]["observation"] = dict.fromkeys(consumer.MEASUREMENT_KEYS)
                self.assertEqual(state, self._load(snapshot)["state"])

    def test_execution_authority_and_signature_claims_cannot_be_promoted(self):
        for key in consumer.AUTHORITY:
            snapshot = snapshot_fixture()
            snapshot["ouroboros_observation"]["authority"][key] = "WRITE"
            self.assertEqual("AUTHORITY_ESCALATION", self._load(snapshot)["reason"])
        for field in (True, 0):
            snapshot = snapshot_fixture()
            snapshot["ouroboros_observation"]["claims"]["signature_verified"] = field
            self.assertFalse(self._load(snapshot)["ready"])

    def test_extra_raw_fields_and_invalid_numerical_domains_are_rejected(self):
        snapshot = snapshot_fixture()
        snapshot["ouroboros_observation"]["raw_review"] = "fixture content must not appear"
        self.assertEqual("OBSERVATION_SHAPE", self._load(snapshot)["reason"])
        for key, value in (("wall_ms", "10"), ("wall_ms", -1), ("steps", True), ("recommendation_count", -1)):
            with self.subTest(key=key, value=value):
                snapshot = snapshot_fixture()
                snapshot["ouroboros_observation"]["observation"][key] = value
                self.assertFalse(self._load(snapshot)["ready"])

    def test_dag_unknown_dependency_cycle_and_effectors_are_rejected(self):
        for target, reason in (("missing", "DAG_MISSING_DEPENDENCY"), ("hold", "DAG_CYCLE")):
            snapshot = snapshot_fixture()
            dag = snapshot["advisory_dag"]
            dag["normalized_contract"]["nodes"][0]["depends_on"] = [target]
            dag["contract_digest"] = consumer.digest(dag["normalized_contract"])
            self.assertEqual(reason, self._load(snapshot)["reason"])
        snapshot = snapshot_fixture()
        snapshot["advisory_dag"]["execution"]["authorized"] = True
        self.assertEqual("DAG_EXECUTION_AUTHORITY", self._load(snapshot)["reason"])

    def test_prebridge_snapshot_does_not_synthesize_a_current_run(self):
        snapshot = snapshot_fixture()
        del snapshot["ouroboros_observation"]
        del snapshot["advisory_dag"]
        result = self._load(snapshot)
        self.assertEqual("UPSTREAM_BRIDGE_NOT_ADMITTED", result["reason"])
        self.assertIsNone(result["ouroboros_observation"])
        self.assertIsNone(result["dag"])

    def test_malformed_nested_shapes_fail_closed_without_breaking_the_reader(self):
        for key, reason in (("execution", "DAG_EXECUTION_AUTHORITY"), ("topology", "DAG_TOPOLOGY")):
            with self.subTest(key=key):
                snapshot = snapshot_fixture()
                snapshot["advisory_dag"][key] = []
                result = self._load(snapshot)
                self.assertFalse(result["ready"])
                self.assertEqual(reason, result["reason"])
        snapshot = snapshot_fixture()
        snapshot["authority"] = None
        self.assertEqual("UPSTREAM_AUTHORITY", self._load(snapshot)["reason"])


if __name__ == "__main__":
    unittest.main()
