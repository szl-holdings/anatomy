#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Living Anatomy v7: read-only Second Brain, formula, quant, and loop tissue.

This module extends the source-bound Living Anatomy app in process. It loads the
exact frontier snapshot bundled by ``scripts/materialize_second_brain.py`` and
exposes handles, digests, source receipts, and aggregate counts only. Candidate
content remains internal to the process; there is no public hydration, training,
promotion, tool execution, provider mutation, or private-graph path.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import threading
from collections import Counter
from pathlib import Path
from typing import Any

from fastapi import Query
from fastapi.responses import JSONResponse

from living_runtime import app

ROOT = Path(__file__).resolve().parent
SNAPSHOT = ROOT / ".runtime" / "second-brain"
STATE_PATH = SNAPSHOT / "frontier-state.v1.json"
CANDIDATES_PATH = SNAPSHOT / "frontier-candidates.public.jsonl"
SOURCE_PATH = SNAPSHOT / "source.json"
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_.:/+-]{1,63}")
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
FRONTIER_ID = re.compile(r"^frontier:[0-9a-f]{32}$")
FORMULA_KINDS = {
    "formula-authority",
    "attributed-formula",
    "executable-formula",
    "quant-domain",
}


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _tokens(value: str) -> list[str]:
    return TOKEN_RE.findall(value.lower())


def _response(payload: dict[str, Any], *, status_code: int = 200) -> JSONResponse:
    response = JSONResponse(payload, status_code=status_code)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-SZL-Surface"] = "LIVING_ANATOMY_V7"
    response.headers["X-SZL-Authority"] = "READ_ONLY"
    response.headers["X-SZL-Content-Access"] = "HANDLES_ONLY"
    return response


class FrontierAtlas:
    """Lazy, immutable and fail-closed view over the materialized snapshot."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._loaded = False
        self._load_error: str | None = None
        self._state: dict[str, Any] = {}
        self._source: dict[str, Any] = {}
        self._rows: tuple[dict[str, Any], ...] = ()
        self._frequencies: tuple[Counter[str], ...] = ()
        self._document_frequency: Counter[str] = Counter()

    def _load(self) -> None:
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            try:
                state_raw = STATE_PATH.read_bytes()
                candidates_raw = CANDIDATES_PATH.read_bytes()
                source = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
                state = json.loads(state_raw)
                rows = [
                    json.loads(line)
                    for line in candidates_raw.splitlines()
                    if line.strip()
                ]
                self._validate(state, rows, source)
                frequencies: list[Counter[str]] = []
                document_frequency: Counter[str] = Counter()
                for row in rows:
                    terms = _tokens(
                        " ".join(
                            (
                                str(row.get("title") or ""),
                                str(row.get("source_repository") or ""),
                                str(row.get("source_path") or ""),
                                str(row.get("source_kind") or ""),
                                str(row.get("quant_domain") or ""),
                                str(row.get("content") or ""),
                            )
                        )
                    )
                    frequency = Counter(terms)
                    frequencies.append(frequency)
                    document_frequency.update(frequency.keys())
                self._state = state
                self._source = source
                self._rows = tuple(rows)
                self._frequencies = tuple(frequencies)
                self._document_frequency = document_frequency
            except Exception as exc:  # public detail remains type-only
                self._load_error = type(exc).__name__
            self._loaded = True

    @staticmethod
    def _validate(
        state: Any,
        rows: list[Any],
        source: Any,
    ) -> None:
        if not isinstance(state, dict):
            raise ValueError("frontier state must be an object")
        expected = {
            "schema": "szl.second-brain.frontier-state/v1",
            "state": "REVIEW_REQUIRED",
            "public_content_access": "HANDLES_ONLY",
            "controller_content_access": "AUTHORIZED_CONTROLLER_ONLY",
            "training_authority": "NONE",
            "promotion_authority": "NONE",
            "execution_authority": "NONE",
            "merge_authority": "NONE",
            "lambda": "CONJECTURE_1",
        }
        for key, wanted in expected.items():
            if state.get(key) != wanted:
                raise ValueError(f"frontier state boundary mismatch: {key}")
        if int(state.get("private_graph_nodes_loaded") or 0) != 0:
            raise ValueError("private graph entered the frontier snapshot")
        if int(state.get("raw_graph_nodes_admitted_to_gradients") or 0) != 0:
            raise ValueError("raw graph nodes entered gradients")
        if not isinstance(source, dict):
            raise ValueError("Second Brain source receipt is missing")
        if source.get("schema") != "szl.second-brain.snapshot/v2":
            raise ValueError("Second Brain source receipt is not v2")
        if source.get("source_repository") != "szl-holdings/szl-second-brain":
            raise ValueError("Second Brain source repository drifted")
        if not HEX_40.fullmatch(str(source.get("source_revision") or "")):
            raise ValueError("Second Brain source revision is not exact")
        frontier_receipt = source.get("frontier")
        if not isinstance(frontier_receipt, dict):
            raise ValueError("Second Brain frontier source receipt is missing")

        seen: set[str] = set()
        canonical_lines: list[bytes] = []
        kind_counts: Counter[str] = Counter()
        for row in rows:
            if not isinstance(row, dict):
                raise ValueError("frontier candidate must be an object")
            if row.get("schema") != "szl.second-brain.frontier-candidate/v1":
                raise ValueError("frontier candidate schema mismatch")
            node_id = str(row.get("id") or "")
            if not FRONTIER_ID.fullmatch(node_id) or node_id in seen:
                raise ValueError("frontier candidate id is invalid or duplicated")
            seen.add(node_id)
            if not HEX_40.fullmatch(str(row.get("source_revision") or "")):
                raise ValueError("frontier candidate source revision is not exact")
            if row.get("candidate_state") != "DISCOVERED_REVIEW_REQUIRED":
                raise ValueError("frontier candidate was promoted")
            if row.get("content_access") != "CONTROLLER_ONLY":
                raise ValueError("frontier candidate content boundary drifted")
            content = str(row.get("content") or "")
            measured = _sha256(content.encode("utf-8"))
            if measured != row.get("content_sha256") or not HEX_64.fullmatch(measured):
                raise ValueError("frontier candidate content digest mismatch")
            kind_counts[str(row.get("source_kind") or "unknown")] += 1
            canonical_lines.append(_canonical_bytes(row) + b"\n")

        if len(rows) != int(state.get("candidate_count") or -1):
            raise ValueError("frontier candidate count mismatch")
        candidate_set = _sha256(b"".join(canonical_lines))
        if candidate_set != state.get("candidate_set_sha256"):
            raise ValueError("frontier candidate-set digest mismatch")
        if frontier_receipt.get("candidate_set_sha256") != candidate_set:
            raise ValueError("source receipt candidate-set digest mismatch")
        if frontier_receipt.get("candidate_count") != len(rows):
            raise ValueError("source receipt candidate count mismatch")
        if kind_counts["attributed-formula"] != 30:
            raise ValueError("attributed formula count drifted")
        if kind_counts["executable-formula"] != 21:
            raise ValueError("executable formula count drifted")
        if kind_counts["quant-domain"] != 9:
            raise ValueError("quant domain count drifted")

    @property
    def ready(self) -> bool:
        self._load()
        return self._load_error is None and bool(self._rows)

    def status(self) -> dict[str, Any]:
        self._load()
        if not self.ready:
            return {
                "schema": "szl.anatomy.frontier-status/v1",
                "state": "UNAVAILABLE",
                "ready": False,
                "reason": self._load_error,
                "content_access": "HANDLES_ONLY",
                "authority": "READ_ONLY",
                "training_authority": "NONE",
                "promotion_authority": "NONE",
                "execution_authority": "NONE",
                "private_graph_present": False,
            }
        kind_counts = Counter(
            str(row.get("source_kind") or "unknown") for row in self._rows
        )
        domain_counts = Counter(
            str(row["quant_domain"])
            for row in self._rows
            if row.get("quant_domain")
        )
        return {
            "schema": "szl.anatomy.frontier-status/v1",
            "state": "SOURCE_BOUND_REVIEW_MEMORY",
            "ready": True,
            "anatomy_surface": "HOLOGRAPHIC_V7",
            "second_brain_source_repository": self._source[
                "source_repository"
            ],
            "second_brain_source_revision": self._source["source_revision"],
            "candidate_count": len(self._rows),
            "candidate_set_sha256": self._state["candidate_set_sha256"],
            "source_count": self._state["source_count"],
            "source_kind_counts": dict(sorted(kind_counts.items())),
            "quant_domain_counts": dict(sorted(domain_counts.items())),
            "formula_atlas": {
                "attributed_formula_count": kind_counts[
                    "attributed-formula"
                ],
                "executable_formula_count": kind_counts[
                    "executable-formula"
                ],
                "quant_domain_count": kind_counts["quant-domain"],
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

    @staticmethod
    def _handle(row: dict[str, Any]) -> dict[str, Any]:
        handle: dict[str, Any] = {
            "schema": "szl.anatomy.frontier-handle/v1",
            "nodeId": row["id"],
            "title": row["title"],
            "sha256": row["content_sha256"],
            "repository": row["source_repository"],
            "revision": row["source_revision"],
            "path": row["source_path"],
            "kind": row["source_kind"],
            "admission": row["admission"],
            "candidateState": "DISCOVERED_REVIEW_REQUIRED",
            "contentAccess": "HANDLES_ONLY",
            "authority": "NONE",
        }
        if row.get("quant_domain"):
            handle["quantDomain"] = row["quant_domain"]
        return handle

    def search(
        self,
        query: str,
        *,
        k: int,
        allowed_kinds: set[str] | None = None,
        quant_domain: str | None = None,
        source_repository: str | None = None,
    ) -> dict[str, Any]:
        self._load()
        if not self.ready:
            return {
                "schema": "szl.anatomy.frontier-handles/v1",
                "state": "UNAVAILABLE",
                "ready": False,
                "handles": [],
                "scores": [],
                "content_access": "HANDLES_ONLY",
                "reason": self._load_error,
            }
        terms = _tokens(query)
        limit = max(1, min(int(k), 48))
        selected_indices = [
            index
            for index, row in enumerate(self._rows)
            if (
                allowed_kinds is None
                or str(row.get("source_kind") or "") in allowed_kinds
            )
            and (
                quant_domain is None
                or str(row.get("quant_domain") or "") == quant_domain
            )
            and (
                source_repository is None
                or str(row.get("source_repository") or "")
                == source_repository
            )
        ]
        scored: list[tuple[float, int]] = []
        if terms:
            n_documents = max(1, len(self._rows))
            for index in selected_indices:
                frequency = self._frequencies[index]
                length = max(1, sum(frequency.values()))
                score = 0.0
                for term in terms:
                    tf = frequency.get(term, 0)
                    if not tf:
                        continue
                    df = self._document_frequency.get(term, 0)
                    inverse = math.log(
                        1.0 + (n_documents - df + 0.5) / (df + 0.5)
                    )
                    score += inverse * (
                        (tf * 2.2)
                        / (tf + 1.2 + 0.75 * length / 180.0)
                    )
                if score > 0:
                    scored.append((round(score, 8), index))
            scored.sort(
                key=lambda item: (
                    -item[0],
                    str(self._rows[item[1]]["id"]),
                )
            )
        else:
            scored = [(0.0, index) for index in selected_indices]
            scored.sort(key=lambda item: str(self._rows[item[1]]["id"]))
        chosen = scored[:limit]
        handles = [self._handle(self._rows[index]) for _score, index in chosen]
        return {
            "schema": "szl.anatomy.frontier-handles/v1",
            "state": "REVIEW_REQUIRED",
            "ready": True,
            "anatomy_surface": "HOLOGRAPHIC_V7",
            "query": query[:240],
            "candidate_set_sha256": self._state["candidate_set_sha256"],
            "matched_count": len(scored),
            "returned_count": len(handles),
            "handles": handles,
            "scores": [score for score, _index in chosen],
            "ranking": "LEXICAL_RELEVANCE_NOT_CORRECTNESS",
            "content_access": "HANDLES_ONLY",
            "training_authority": "NONE",
            "promotion_authority": "NONE",
            "execution_authority": "NONE",
        }


ATLAS = FrontierAtlas()


@app.get("/api/anatomy/v1/frontier/status")
def frontier_status_route() -> JSONResponse:
    payload = ATLAS.status()
    return _response(payload, status_code=200 if payload.get("ready") else 503)


@app.get("/api/anatomy/v1/frontier/handles")
def frontier_handles_route(
    q: str = Query("", alias="q", max_length=2000),
    k: int = Query(24, ge=1, le=48),
) -> JSONResponse:
    return _response(ATLAS.search(q, k=k))


@app.get("/api/anatomy/v1/frontier/formulas")
def frontier_formulas_route(
    q: str = Query("", alias="q", max_length=2000),
    domain: str | None = Query(None, max_length=80),
    k: int = Query(48, ge=1, le=48),
) -> JSONResponse:
    return _response(
        ATLAS.search(
            q,
            k=k,
            allowed_kinds=FORMULA_KINDS,
            quant_domain=domain,
        )
    )


@app.get("/api/anatomy/v1/frontier/ouroboros")
def frontier_ouroboros_route(
    q: str = Query("bounded loop convergence receipt", max_length=2000),
    k: int = Query(24, ge=1, le=48),
) -> JSONResponse:
    return _response(
        ATLAS.search(
            q,
            k=k,
            source_repository="szl-holdings/ouroboros",
        )
    )


@app.get("/api/anatomy/v1/holographic-v7")
def holographic_v7_route() -> JSONResponse:
    status = ATLAS.status()
    return _response(
        {
            "schema": "szl.anatomy.holographic-v7/v1",
            "state": (
                "SOURCE_BOUND_READ_ONLY"
                if status.get("ready")
                else "UNAVAILABLE"
            ),
            "ready": bool(status.get("ready")),
            "surface": "LIVING_ANATOMY_HOLOGRAPHIC_V7",
            "organs": [
                {
                    "id": "yachay-second-brain",
                    "role": "handles_and_candidate_receipts",
                    "authority": "READ_ONLY",
                },
                {
                    "id": "formula-quant-atlas",
                    "role": "constraints_proof_status_and_quant_domains",
                    "authority": "REFERENCE_AND_EVALUATION",
                },
                {
                    "id": "ouroboros-loop",
                    "role": "bounded_observe_orient_propose_verify_hold",
                    "authority": "REVIEW_ONLY",
                },
                {
                    "id": "codex-review",
                    "role": "structured_recommendation_proposals",
                    "authority": "NO_EXECUTION",
                },
            ],
            "frontier": status,
            "claims": {
                "content_exposed": False,
                "weights_trained": False,
                "claim_promoted": False,
                "private_graph_used": False,
                "execution_performed": False,
                "human_review_required": True,
            },
        },
        status_code=200 if status.get("ready") else 503,
    )


if __name__ == "__main__":
    import os

    import uvicorn

    uvicorn.run(
        "frontier_runtime:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "7860")),
        reload=False,
    )
