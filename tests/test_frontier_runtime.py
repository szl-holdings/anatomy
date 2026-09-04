from __future__ import annotations

import hashlib
import json
from collections import Counter
from typing import Any

from fastapi.testclient import TestClient

import frontier_runtime


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def make_row(index: int, kind: str, domain: str | None = None) -> dict[str, Any]:
    content = f"bounded review candidate {index} for {kind}; no execution authority"
    row: dict[str, Any] = {
        "schema": "szl.second-brain.frontier-candidate/v1",
        "id": f"frontier:{index:032x}",
        "title": f"Candidate {index}",
        "content": content,
        "content_sha256": hashlib.sha256(content.encode()).hexdigest(),
        "source_repository": "szl-holdings/szl-formulas",
        "source_revision": "1" * 40,
        "source_path": "atlas/formula-atlas.v1.json",
        "source_kind": kind,
        "admission": "REFERENCE_AND_CONSTRAINT_INPUT_ONLY",
        "candidate_state": "DISCOVERED_REVIEW_REQUIRED",
        "content_access": "CONTROLLER_ONLY",
    }
    if domain:
        row["quant_domain"] = domain
    return row


def snapshot() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    rows.append(make_row(1, "formula-authority", "trust_aggregation"))
    for index in range(2, 32):
        rows.append(make_row(index, "attributed-formula", f"domain-{index % 9}"))
    for index in range(32, 53):
        rows.append(make_row(index, "executable-formula"))
    for index in range(53, 62):
        rows.append(make_row(index, "quant-domain", f"domain-{index - 53}"))
    for index in range(62, 72):
        rows.append(make_row(index, "source-document"))
    rows.sort(key=lambda row: row["id"])
    candidate_set = hashlib.sha256(
        b"".join(canonical_bytes(row) + b"\n" for row in rows)
    ).hexdigest()
    kinds = Counter(str(row["source_kind"]) for row in rows)
    domains = Counter(
        str(row["quant_domain"]) for row in rows if row.get("quant_domain")
    )
    state = {
        "schema": "szl.second-brain.frontier-state/v1",
        "state": "REVIEW_REQUIRED",
        "candidate_count": len(rows),
        "candidate_set_sha256": candidate_set,
        "source_count": 7,
        "sources": [],
        "source_kind_counts": dict(kinds),
        "quant_domain_counts": dict(domains),
        "public_content_access": "HANDLES_ONLY",
        "controller_content_access": "AUTHORIZED_CONTROLLER_ONLY",
        "private_graph_nodes_loaded": 0,
        "raw_graph_nodes_admitted_to_gradients": 0,
        "training_authority": "NONE",
        "promotion_authority": "NONE",
        "execution_authority": "NONE",
        "merge_authority": "NONE",
        "lambda": "CONJECTURE_1",
    }
    source = {
        "schema": "szl.second-brain.snapshot/v2",
        "source_repository": "szl-holdings/szl-second-brain",
        "source_revision": "2" * 40,
        "frontier": {
            "candidate_count": len(rows),
            "candidate_set_sha256": candidate_set,
        },
    }
    return state, rows, source


def test_exact_frontier_snapshot_accepts_formula_and_quant_contract() -> None:
    state, rows, source = snapshot()
    frontier_runtime.FrontierAtlas._validate(state, rows, source)


def test_snapshot_rejects_promotion_content_drift_and_private_graph() -> None:
    state, rows, source = snapshot()
    promoted = [dict(row) for row in rows]
    promoted[0]["candidate_state"] = "PROMOTED"
    try:
        frontier_runtime.FrontierAtlas._validate(state, promoted, source)
    except ValueError as error:
        assert "promoted" in str(error)
    else:
        raise AssertionError("promoted candidate was accepted")

    state, rows, source = snapshot()
    rows[0]["content_sha256"] = "0" * 64
    try:
        frontier_runtime.FrontierAtlas._validate(state, rows, source)
    except ValueError as error:
        assert "digest" in str(error)
    else:
        raise AssertionError("content digest drift was accepted")

    state, rows, source = snapshot()
    state["private_graph_nodes_loaded"] = 1
    try:
        frontier_runtime.FrontierAtlas._validate(state, rows, source)
    except ValueError as error:
        assert "private graph" in str(error)
    else:
        raise AssertionError("private graph admission was accepted")


class FakeAtlas:
    def status(self) -> dict[str, Any]:
        return {
            "schema": "szl.anatomy.frontier-status/v1",
            "state": "SOURCE_BOUND_REVIEW_MEMORY",
            "ready": True,
            "anatomy_surface": "HOLOGRAPHIC_V7",
            "second_brain_source_repository": "szl-holdings/szl-second-brain",
            "second_brain_source_revision": "2" * 40,
            "candidate_count": 101,
            "candidate_set_sha256": "3" * 64,
            "source_count": 7,
            "source_kind_counts": {
                "formula-authority": 1,
                "attributed-formula": 30,
                "executable-formula": 21,
                "quant-domain": 9,
                "source-document": 40,
            },
            "quant_domain_counts": {"trust_aggregation": 5},
            "formula_atlas": {
                "attributed_formula_count": 30,
                "executable_formula_count": 21,
                "quant_domain_count": 9,
                "locked_proven_formula_count": 8,
                "f_number_to_executable_mapping": "UNKNOWN_NOT_INFERRED",
            },
            "content_access": "HANDLES_ONLY",
            "authority": "READ_ONLY",
            "training_authority": "NONE",
            "promotion_authority": "NONE",
            "execution_authority": "NONE",
            "private_graph_present": False,
            "raw_graph_nodes_admitted_to_gradients": 0,
            "lambda": "CONJECTURE_1",
        }

    def search(self, query: str, *, k: int, **_filters: Any) -> dict[str, Any]:
        handle = {
            "schema": "szl.anatomy.frontier-handle/v1",
            "nodeId": "frontier:" + "a" * 32,
            "title": "Formula authority",
            "sha256": "4" * 64,
            "repository": "szl-holdings/szl-formulas",
            "revision": "5" * 40,
            "path": "atlas/formula-atlas.v1.json",
            "kind": "formula-authority",
            "admission": "REFERENCE_AND_CONSTRAINT_INPUT_ONLY",
            "candidateState": "DISCOVERED_REVIEW_REQUIRED",
            "contentAccess": "HANDLES_ONLY",
            "authority": "NONE",
            "quantDomain": "trust_aggregation",
        }
        return {
            "schema": "szl.anatomy.frontier-handles/v1",
            "state": "REVIEW_REQUIRED",
            "ready": True,
            "anatomy_surface": "HOLOGRAPHIC_V7",
            "query": query,
            "candidate_set_sha256": "3" * 64,
            "matched_count": 1,
            "returned_count": 1,
            "handles": [handle][:k],
            "scores": [1.0][:k],
            "ranking": "LEXICAL_RELEVANCE_NOT_CORRECTNESS",
            "content_access": "HANDLES_ONLY",
            "training_authority": "NONE",
            "promotion_authority": "NONE",
            "execution_authority": "NONE",
        }


def test_public_routes_are_handles_only_and_read_only(monkeypatch) -> None:
    monkeypatch.setattr(frontier_runtime, "ATLAS", FakeAtlas())
    client = TestClient(frontier_runtime.app)

    status = client.get("/api/anatomy/v1/frontier/status")
    assert status.status_code == 200
    assert status.headers["x-szl-surface"] == "LIVING_ANATOMY_V7"
    assert status.headers["x-szl-authority"] == "READ_ONLY"
    assert status.headers["x-szl-content-access"] == "HANDLES_ONLY"
    assert status.json()["formula_atlas"] == {
        "attributed_formula_count": 30,
        "executable_formula_count": 21,
        "quant_domain_count": 9,
        "locked_proven_formula_count": 8,
        "f_number_to_executable_mapping": "UNKNOWN_NOT_INFERRED",
    }

    formulas = client.get(
        "/api/anatomy/v1/frontier/formulas",
        params={"q": "Lambda", "k": 12},
    )
    assert formulas.status_code == 200
    assert formulas.json()["content_access"] == "HANDLES_ONLY"
    assert formulas.json()["handles"][0]["contentAccess"] == "HANDLES_ONLY"

    loops = client.get("/api/anatomy/v1/frontier/ouroboros")
    assert loops.status_code == 200
    assert loops.json()["execution_authority"] == "NONE"

    for response in (status, formulas, loops):
        serialized = response.text.lower()
        assert '"content"' not in serialized
        assert '"text"' not in serialized


def test_holographic_v7_contract_discloses_every_non_authority(monkeypatch) -> None:
    monkeypatch.setattr(frontier_runtime, "ATLAS", FakeAtlas())
    client = TestClient(frontier_runtime.app)
    response = client.get("/api/anatomy/v1/holographic-v7")
    assert response.status_code == 200
    payload = response.json()
    assert payload["surface"] == "LIVING_ANATOMY_HOLOGRAPHIC_V7"
    assert payload["frontier"]["lambda"] == "CONJECTURE_1"
    assert payload["frontier"]["formula_atlas"]["locked_proven_formula_count"] == 8
    assert payload["claims"] == {
        "content_exposed": False,
        "weights_trained": False,
        "claim_promoted": False,
        "private_graph_used": False,
        "execution_performed": False,
        "human_review_required": True,
    }
