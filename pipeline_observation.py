# SPDX-License-Identifier: Apache-2.0
"""Bounded read-only consumer of the admitted A11oy review snapshot.

This module performs no network request and imports no executor. Source hashes
bind a producer report; they do not verify a signature or establish its truth.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

SNAPSHOT_SCHEMA = "szl.living-anatomy.pipeline-source/v1"
UPSTREAM_SCHEMA = "szl.a11oy.brain-frontier-holographic-v7/v1"
OBSERVATION_SCHEMA = "szl.ouroboros.frontier-observation/v1"
UPSTREAM_REPOSITORY = "szl-holdings/a11oy"
UPSTREAM_PATH = "console/assets/brain-frontier-v7.json"
MAX_SNAPSHOT_BYTES = 512 * 1024
MAX_WRAPPER_BYTES = 2 * 1024 * 1024
MAX_AGE_SECONDS = 21600
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
STATES = {"OBSERVED", "UNAVAILABLE", "PENDING", "FAILED", "STALE", "REJECTED"}
AUTHORITY = dict.fromkeys(("training", "promotion", "execution", "merge", "provider_mutation"), "NONE")
OBSERVATION_KEYS = {
    "schema", "state", "reason", "source", "run", "artifact", "observation",
    "freshness", "authority", "claims", "observation_sha256",
}
MEASUREMENT_KEYS = {
    "bounded", "terminated", "receipt_closed", "steps", "max_budget", "wall_ms",
    "exit", "review_state", "review_sha256", "recommendation_count",
}


class PipelineError(ValueError):
    def __init__(self, reason: str, state: str = "REJECTED") -> None:
        super().__init__(reason)
        self.reason = reason
        self.state = state


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _require(condition: bool, reason: str, state: str = "REJECTED") -> None:
    if not condition:
        raise PipelineError(reason, state)


def _sha(value: Any, length: int = 64) -> bool:
    return isinstance(value, str) and bool((HEX_40 if length == 40 else HEX_64).fullmatch(value))


def _integer(value: Any, minimum: int = 0, maximum: int = 1_000_000) -> bool:
    return type(value) is int and minimum <= value <= maximum


def _text(value: Any, maximum: int = 128) -> bool:
    return isinstance(value, str) and 0 < len(value) <= maximum


def _timestamp(value: Any) -> datetime:
    _require(_text(value, 40), "INVALID_TIMESTAMP")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PipelineError("INVALID_TIMESTAMP") from exc
    _require(result.tzinfo is not None, "INVALID_TIMESTAMP")
    return result.astimezone(timezone.utc)


def _hash_check(value: dict[str, Any], field: str) -> None:
    _require(_sha(value.get(field)), "INVALID_DIGEST")
    body = {key: item for key, item in value.items() if key != field}
    _require(value[field] == digest(body), "DIGEST_MISMATCH")


def validate_observation(value: Any, expected: dict[str, Any],
                         *, now: datetime | None = None) -> dict[str, Any]:
    """Validate a producer report and derive freshness on the consumer clock."""
    now = now or datetime.now(timezone.utc)
    _require(isinstance(value, dict) and set(value) == OBSERVATION_KEYS, "OBSERVATION_SHAPE")
    _require(value["schema"] == OBSERVATION_SCHEMA and value["state"] in STATES, "OBSERVATION_SCHEMA")
    _hash_check(value, "observation_sha256")
    _require(_text(value["reason"], 128) and re.fullmatch(r"[A-Z0-9_]+", value["reason"]) is not None,
             "OBSERVATION_REASON")
    source = value["source"]
    _require(isinstance(source, dict) and set(source) == set(expected), "OBSERVATION_SOURCE_SHAPE")
    _require(source == expected, "BRAIN_OR_CONTROLLER_SOURCE_MISMATCH", "STALE")
    _require(value["authority"] == AUTHORITY, "AUTHORITY_ESCALATION")
    _require(value["claims"] == {
        "signature_verified": False, "review_is_accepted_truth": False,
        "production_verified": False, "private_graph_loaded": False,
        "measurement_scope": "RECORDED_REVIEW_ATTEMPT",
    }, "CLAIM_ESCALATION")
    # Python equality admits 0 == False; enforce the declared boolean types.
    _require(all(type(value["claims"][key]) is bool for key in (
        "signature_verified", "review_is_accepted_truth", "production_verified", "private_graph_loaded"
    )), "CLAIM_TYPE")
    measurements = value["observation"]
    _require(isinstance(measurements, dict) and set(measurements) == MEASUREMENT_KEYS,
             "MEASUREMENT_SHAPE")
    freshness = value["freshness"]
    _require(isinstance(freshness, dict) and set(freshness) == {
        "observed_at", "expires_at", "max_age_seconds"
    }, "FRESHNESS_SHAPE")
    _require(type(freshness["max_age_seconds"]) is int
             and freshness["max_age_seconds"] == MAX_AGE_SECONDS, "FRESHNESS_BUDGET")
    run = value["run"]
    if run is not None:
        _require(isinstance(run, dict) and set(run) == {
            "id", "attempt", "head_sha", "status", "conclusion", "url", "updated_at"
        }, "RUN_SHAPE")
        _require(_integer(run["id"], 1, 2**53 - 1) and _integer(run["attempt"], 1, 1000)
                 and _sha(run["head_sha"], 40), "RUN_IDENTITY")
        _require(run["status"] in ("queued", "in_progress", "completed", "waiting", "pending", "requested")
                 and run["conclusion"] in (None, "success", "failure", "cancelled", "timed_out",
                                            "neutral", "skipped", "action_required", "stale", "startup_failure"),
                 "RUN_STATUS")
        _require(run["url"] == f'https://github.com/szl-holdings/szl-ouroboros/actions/runs/{run["id"]}',
                 "RUN_URL")
        observed_at = _timestamp(run["updated_at"])
        _require(_timestamp(freshness["observed_at"]) == observed_at, "FRESHNESS_RUN_MISMATCH")
        expires_at = _timestamp(freshness["expires_at"])
        _require(expires_at == observed_at + timedelta(seconds=MAX_AGE_SECONDS), "FRESHNESS_EXPIRY")
        _require(observed_at <= now + timedelta(seconds=300), "FUTURE_OBSERVATION")
    else:
        _require(freshness["observed_at"] is None and freshness["expires_at"] is None,
                 "FRESHNESS_WITHOUT_RUN")
        expires_at = None
    artifact = value["artifact"]
    if artifact is not None:
        _require(isinstance(artifact, dict) and set(artifact) == {
            "id", "name", "archive_sha256", "receipt_sha256"
        }, "ARTIFACT_SHAPE")
        _require(run is not None and _integer(artifact["id"], 1, 2**53 - 1), "ARTIFACT_RUN")
        _require(artifact["name"] == f'ouroboros-frontier-{run["id"]}-{run["attempt"]}', "ARTIFACT_IDENTITY")
        _require(_sha(artifact["archive_sha256"]) and _sha(artifact["receipt_sha256"]), "ARTIFACT_DIGEST")
    if value["state"] == "OBSERVED":
        _require(run is not None and artifact is not None, "OBSERVED_WITHOUT_ARTIFACT")
        _require(run["status"] == "completed" and run["conclusion"] == "success"
                 and run["head_sha"] == expected["controller_revision"], "OBSERVED_RUN_MISMATCH")
        _require(all(type(measurements[key]) is bool for key in ("bounded", "terminated", "receipt_closed")),
                 "MEASUREMENT_BOOLEAN")
        _require(_integer(measurements["steps"]) and _integer(measurements["max_budget"], 1)
                 and _integer(measurements["recommendation_count"], 0, 100), "MEASUREMENT_COUNT")
        wall = measurements["wall_ms"]
        _require(type(wall) in (int, float) and math.isfinite(wall) and wall >= 0, "MEASUREMENT_TIME")
        _require(measurements["bounded"] is (measurements["steps"] <= measurements["max_budget"]),
                 "MEASUREMENT_BUDGET")
        _require(_text(measurements["exit"], 64) and _text(measurements["review_state"], 64)
                 and _sha(measurements["review_sha256"]), "MEASUREMENT_REVIEW")
    else:
        _require(all(item is None for item in measurements.values()), "UNOBSERVED_MEASUREMENTS")
    expired = expires_at is not None and now >= expires_at
    return {
        "state": "STALE" if expired else value["state"],
        "recorded_state": value["state"],
        "reason": "OBSERVATION_EXPIRED" if expired else value["reason"],
        "source": source,
        "run": run,
        "artifact": artifact,
        "observation": dict.fromkeys(MEASUREMENT_KEYS) if expired else measurements,
        "freshness": freshness,
        "observation_sha256": value["observation_sha256"],
        "verification": "SOURCE_BOUND_PRODUCER_REPORT",
        "measurement_scope": "RECORDED_REVIEW_ATTEMPT",
    }


def project_dag(value: Any) -> dict[str, Any]:
    _require(isinstance(value, dict) and value.get("schema") == "szl.governed-graph.analysis/v1",
             "DAG_SCHEMA")
    _require(value.get("evidence_label") == "MODELED", "DAG_EVIDENCE_LABEL")
    execution = value.get("execution", {})
    _require(isinstance(execution, dict) and execution.get("mode") == "PLAN_ONLY"
             and execution.get("authorized") is False,
             "DAG_EXECUTION_AUTHORITY")
    _require(all(type(execution.get(key)) is int and execution[key] == 0
                 for key in ("effectors", "provider_calls", "writes")), "DAG_EFFECTORS")
    graph = value.get("normalized_contract")
    _require(isinstance(graph, dict) and graph.get("schema") == "szl.governed-graph/v1", "DAG_CONTRACT")
    _require(_sha(value.get("contract_digest")) and value["contract_digest"] == digest(graph),
             "DAG_CONTRACT_DIGEST")
    nodes = graph.get("nodes")
    _require(isinstance(nodes, list) and 1 <= len(nodes) <= 64, "DAG_NODE_COUNT")
    ids = [node.get("id") if isinstance(node, dict) else None for node in nodes]
    _require(all(_text(node_id, 64) for node_id in ids) and len(set(ids)) == len(ids), "DAG_NODE_IDENTITY")
    by_id = {}
    for node in nodes:
        _require(node.get("side_effecting") is False and node.get("writes") == [], "DAG_SIDE_EFFECT")
        _require(node.get("authority") in {"READ_ONLY", "PROPOSE", "HUMAN"}, "DAG_NODE_AUTHORITY")
        _require(_text(node.get("label"), 128) and _text(node.get("role"), 32), "DAG_NODE_LABEL")
        dependencies = node.get("depends_on")
        controls = node.get("control_after")
        _require(isinstance(dependencies, list) and isinstance(controls, list)
                 and len(dependencies) <= 64 and len(controls) <= 64, "DAG_DEPENDENCIES")
        _require(all(item in ids for item in dependencies + controls), "DAG_MISSING_DEPENDENCY")
        by_id[node["id"]] = set(dependencies + controls)
    pending = dict(by_id)
    layers = []
    while pending:
        layer = sorted(node_id for node_id, deps in pending.items() if not deps)
        _require(bool(layer), "DAG_CYCLE")
        layers.append(layer)
        pending = {node_id: deps - set(layer) for node_id, deps in pending.items() if node_id not in layer}
    topology = value.get("topology", {})
    _require(isinstance(topology, dict) and topology.get("layers") == layers
             and type(topology.get("node_count")) is int and topology["node_count"] == len(nodes),
             "DAG_TOPOLOGY")
    _require(value.get("decision") in {"READY_TO_ORCHESTRATE", "REVISE"}, "DAG_DECISION")
    return {
        "state": "MODELED_PLAN_ONLY", "decision": value["decision"],
        "contract_digest": value["contract_digest"], "execution_authorized": False,
        "nodes": [{key: node[key] for key in ("id", "label", "role", "depends_on", "control_after")}
                  for node in nodes],
        "layers": layers, "node_count": len(nodes),
    }


def unavailable(reason: str, state: str = "UNAVAILABLE") -> dict[str, Any]:
    return {"ready": False, "state": state, "reason": reason, "source": None,
            "dag": None, "ouroboros_observation": None, "snapshot_sha256": None}


def load_pipeline_snapshot(path: Path, expected: dict[str, Any], *, file_sha256: str | None,
                           now: datetime | None = None) -> dict[str, Any]:
    source_binding = None
    snapshot_digest = None
    try:
        _require(_sha(file_sha256), "PIPELINE_NOT_MATERIALIZED", "UNAVAILABLE")
        with path.open("rb") as handle:
            raw = handle.read(MAX_WRAPPER_BYTES + 1)
        _require(len(raw) <= MAX_WRAPPER_BYTES, "PIPELINE_SIZE")
        _require(hashlib.sha256(raw).hexdigest() == file_sha256, "PIPELINE_FILE_DIGEST")
        wrapper = json.loads(raw)
        _require(isinstance(wrapper, dict) and wrapper.get("schema") == SNAPSHOT_SCHEMA, "PIPELINE_SCHEMA")
        _hash_check(wrapper, "receipt_sha256")
        _require(wrapper.get("source_repository") == UPSTREAM_REPOSITORY
                 and wrapper.get("source_path") == UPSTREAM_PATH, "PIPELINE_SOURCE")
        if wrapper.get("snapshot_json") is None:
            return unavailable("UPSTREAM_SNAPSHOT_UNAVAILABLE")
        _require(_sha(wrapper.get("source_revision"), 40), "PIPELINE_REVISION")
        _require(isinstance(wrapper["snapshot_json"], str), "UPSTREAM_JSON_TYPE")
        snapshot_raw = wrapper["snapshot_json"].encode("utf-8")
        _require(len(snapshot_raw) <= MAX_SNAPSHOT_BYTES, "UPSTREAM_SIZE")
        _require(hashlib.sha256(snapshot_raw).hexdigest() == wrapper.get("source_snapshot_sha256"),
                 "UPSTREAM_DIGEST")
        snapshot = json.loads(snapshot_raw)
        _require(isinstance(snapshot, dict) and snapshot.get("schema") == UPSTREAM_SCHEMA, "UPSTREAM_SCHEMA")
        _hash_check(snapshot, "snapshot_sha256")
        source_binding = {
            "repository": UPSTREAM_REPOSITORY, "revision": wrapper["source_revision"],
            "path": UPSTREAM_PATH, "sha256": wrapper["source_snapshot_sha256"],
        }
        snapshot_digest = snapshot["snapshot_sha256"]
        authority = snapshot.get("authority", {})
        _require(isinstance(authority, dict)
                 and all(authority.get(key) == "NONE" for key in AUTHORITY), "UPSTREAM_AUTHORITY")
        _require(authority.get("private_graph_present") is False
                 and authority.get("public_content_access") == "HANDLES_ONLY", "UPSTREAM_CONTENT_BOUNDARY")
        if "ouroboros_observation" not in snapshot or "advisory_dag" not in snapshot:
            raise PipelineError("UPSTREAM_BRIDGE_NOT_ADMITTED", "UNAVAILABLE")
        observed = validate_observation(snapshot["ouroboros_observation"], expected, now=now)
        dag = project_dag(snapshot["advisory_dag"])
        return {
            "ready": True, "state": observed["state"], "reason": observed["reason"],
            "source": source_binding,
            "dag": dag, "ouroboros_observation": observed,
            "snapshot_sha256": snapshot["snapshot_sha256"],
        }
    except PipelineError as exc:
        return {**unavailable(exc.reason, exc.state), "source": source_binding,
                "snapshot_sha256": snapshot_digest}
    except (OSError, ValueError, TypeError, KeyError, OverflowError):
        return unavailable("INVALID_PIPELINE_SNAPSHOT", "REJECTED")
