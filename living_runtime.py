#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Unified runtime for SZL Living Anatomy + YACHAY Neural Quant v7.

The hardened Anatomy server remains the transport, evidence, receipt, and static
rendering authority. This module extends it in-process with the source-bound
575-chunk Second Brain, its 122+ review-gated frontier candidates, the attributed
formula/quant atlas, and bounded Ouroboros observations.

Public APIs expose handles, counts, source revisions, and digests only. Runtime
snapshot files are blocked from direct static access. No reverse proxy, second
process, model training, private graph, candidate promotion, execution, merge, or
provider-mutation authority is introduced.
"""
from __future__ import annotations

import functools
import json
from http.server import ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlsplit

import server as anatomy_server
from frontier_runtime import (
    ATLAS as FRONTIER_ATLAS,
    FORMULA_KINDS,
    holographic_v7_payload,
)
from second_brain_runtime import PublicSecondBrain

try:
    from fastapi import FastAPI
except ImportError:  # pragma: no cover - FastAPI is a declared runtime dep
    FastAPI = None  # type: ignore[misc,assignment]

app = (
    FastAPI(title="living-anatomy-space", version="1.3.0")
    if FastAPI is not None
    else None
)

BRAIN = PublicSecondBrain()

# Bind the v7 runtime and exact source snapshot into the existing deterministic
# Anatomy receipt before the first request can populate any receipt cache.
_EXTRA_ARTIFACTS = (
    "living_runtime.py",
    "frontier_runtime.py",
    "second_brain_runtime.py",
    "neural-quant-v7.js",
    "neural-quant-v7.css",
    "holographic-v7.js",
    "holographic-v7.css",
    ".runtime/second-brain/manifest.json",
    ".runtime/second-brain/brain-corpus.public.jsonl",
    ".runtime/second-brain/frontier-state.v1.json",
    ".runtime/second-brain/frontier-candidates.public.jsonl",
    ".runtime/second-brain/source.json",
)
anatomy_server.ARTIFACT_PATHS = tuple(
    dict.fromkeys((*anatomy_server.ARTIFACT_PATHS, *_EXTRA_ARTIFACTS))
)

_ORIGINAL_MANIFEST = anatomy_server._manifest
_ORIGINAL_VERSION = anatomy_server._version_contract
_ORIGINAL_EVIDENCE = anatomy_server._evidence_contract


def _living_manifest() -> dict[str, Any]:
    payload = _ORIGINAL_MANIFEST()
    brain = BRAIN.health()
    payload["service"] = "living-anatomy-space"
    payload["purpose"] = (
        "Read-only spatial evidence map with source-bound YACHAY Second Brain, "
        "formula/quant atlas, and bounded Ouroboros observations."
    )
    payload["contract_version"] = "1.3.0"
    payload["experience_version"] = "NEURAL_QUANT_V7"
    endpoints = payload.setdefault("endpoints", {})
    endpoints.update(
        {
            "living_health": "/api/anatomy/v1/living-health",
            "brain_health": "/api/anatomy/v1/brain/health",
            "brain_manifest": "/api/anatomy/v1/brain/manifest",
            "brain_search": "/api/anatomy/v1/brain/search",
            "brain_context": "/api/anatomy/v1/brain/context",
            "brain_frontier": "/api/anatomy/v1/brain/frontier",
            "brain_formulas": "/api/anatomy/v1/brain/formulas",
            "brain_quant": "/api/anatomy/v1/brain/quant",
            "brain_ouroboros": "/api/anatomy/v1/brain/ouroboros",
            "neural_quant_v7": "/api/anatomy/v1/brain/neural-quant-v7",
            "frontier_status": "/api/anatomy/v1/frontier/status",
            "frontier_handles": "/api/anatomy/v1/frontier/handles",
            "frontier_formulas": "/api/anatomy/v1/frontier/formulas",
            "frontier_ouroboros": "/api/anatomy/v1/frontier/ouroboros",
            "holographic_v7": "/api/anatomy/v1/holographic-v7",
        }
    )
    payload["organs"] = {
        "brain": {
            "name": "YACHAY",
            "state": brain["state"],
            "ready": BRAIN.ready,
            "source_repository": brain["source_repository"],
            "source_revision": BRAIN.source_revision,
            "chunk_count": brain["chunk_count"],
            "frontier_candidate_count": brain["frontier"]["candidate_count"],
            "candidate_set_sha256": brain["frontier"][
                "candidate_set_sha256"
            ],
            "authority_state": "READ_ONLY",
            "content_access": "HANDLES_ONLY",
        },
        "neural_quant": {
            "name": "NEURAL QUANT V7",
            "ready": BRAIN.ready,
            "attributed_formula_count": brain["formula_atlas"][
                "attributed_formula_count"
            ],
            "executable_formula_count": brain["formula_atlas"][
                "executable_formula_count"
            ],
            "locked_proven_count": brain["formula_atlas"][
                "locked_proven_count"
            ],
            "quant_domain_count": brain["quant_domain_count"],
            "lambda_state": "CONJECTURE_1",
            "authority_state": "READ_ONLY",
        },
    }
    payload.setdefault("limits", []).extend(
        [
            "Second Brain and frontier ranking are relevance signals, never correctness.",
            "Public interfaces contain handles and digests; raw snapshot content is not served.",
            "Frontier candidates remain review-required and cannot train or promote themselves.",
            "The private graph is not present, and this surface has no execution authority.",
        ]
    )
    return payload


def _living_version(force: bool = False) -> dict[str, Any]:
    payload = _ORIGINAL_VERSION(force=force)
    health = BRAIN.health()
    payload["contractVersion"] = "1.3.0"
    payload["experienceVersion"] = "NEURAL_QUANT_V7"
    payload["runtime"] = "living-anatomy+yachay-neural-quant-v7"
    payload["secondBrainSourceRevision"] = BRAIN.source_revision
    payload["secondBrainCandidateSetSha256"] = health["frontier"][
        "candidate_set_sha256"
    ]
    payload["secondBrainEvidenceState"] = (
        "MEASURED" if BRAIN.ready else "UNAVAILABLE"
    )
    return payload


def _living_evidence(force: bool = False) -> dict[str, Any]:
    payload = _ORIGINAL_EVIDENCE(force=force)
    brain = BRAIN.health()
    dependencies = payload.setdefault("dependencies", {})
    dependencies["secondBrain"] = {
        "ready": brain["ready"],
        "state": brain["state"],
        "sourceRepository": brain["source_repository"],
        "sourceRevision": brain["source_revision"],
        "chunkCount": brain["chunk_count"],
        "frontierCandidateCount": brain["frontier"]["candidate_count"],
        "frontierSourceCount": brain["frontier"]["source_count"],
        "candidateSetSha256": brain["frontier"]["candidate_set_sha256"],
        "attributedFormulaCount": brain["formula_atlas"][
            "attributed_formula_count"
        ],
        "executableFormulaCount": brain["formula_atlas"][
            "executable_formula_count"
        ],
        "lockedProvenCount": brain["formula_atlas"]["locked_proven_count"],
        "quantDomainCount": brain["quant_domain_count"],
        "lambdaState": brain["lambda_state"],
        "verificationState": brain["verification_state"],
        "authorityState": brain["authority_state"],
        "contentAccess": brain["content_access"],
        "details": "/api/anatomy/v1/brain/health",
        "neuralQuant": "/api/anatomy/v1/brain/neural-quant-v7",
    }
    runtime = payload.setdefault("runtime", {})
    if not BRAIN.ready:
        runtime["status"] = "DEGRADED"
        runtime["ready"] = False
        payload.setdefault("limitations", []).append(
            "YACHAY Second Brain/frontier snapshot is unavailable; Living Anatomy "
            "remains transport-reachable but the integrated v7 body is not ready."
        )
    return payload


anatomy_server._manifest = _living_manifest
anatomy_server._version_contract = _living_version
anatomy_server._evidence_contract = _living_evidence

if not any(
    isinstance(item, dict) and item.get("id") == "anatomy.yachay-second-brain"
    for item in anatomy_server.CAPABILITIES
):
    anatomy_server.CAPABILITIES.append(
        {
            "id": "anatomy.yachay-second-brain",
            "name": "YACHAY Neural Quant v7",
            "purpose": (
                "Ground the Living Anatomy brain organ in the source-bound public "
                "Second Brain, attributed formula/quant atlas, and bounded "
                "Ouroboros frontier observations."
            ),
            "try": {
                "method": "GET",
                "path": "/api/anatomy/v1/brain/neural-quant-v7?k=12",
                "action": "Inspect the source-bound handles-only v7 observation.",
            },
            "evidence": {
                "state": "MEASURED" if BRAIN.ready else "UNAVAILABLE",
                "basis": (
                    "Exact Second Brain Git revision; retrieval, frontier, and source "
                    "digests; per-row SHA-256; formula/quant counts; locked-eight and "
                    "Lambda-conjecture boundary replay."
                ),
                "source_revision": BRAIN.source_revision,
                "chunk_count": BRAIN.health()["chunk_count"],
                "frontier_candidate_count": BRAIN.health()["frontier"][
                    "candidate_count"
                ],
                "candidate_set_sha256": BRAIN.frontier_candidate_set_sha256,
            },
            "limits": [
                "Lexical overlap is not correctness or proof.",
                "No corpus or candidate content is returned by public APIs.",
                "No private graph node is bundled or queried.",
                "No training, promotion, execution, merge, or provider authority is granted.",
            ],
            "reproduce": {
                "steps": [
                    "GET /api/anatomy/v1/brain/health",
                    "Compare source_revision with szl-holdings/szl-second-brain main.",
                    "Replay candidate_set_sha256 against the materialized JSONL.",
                    "GET /api/anatomy/v1/brain/neural-quant-v7 and verify handles-only output.",
                ]
            },
            "authority_state": "READ_ONLY",
            "formula_refs": ["F1", "F4", "F7", "F11", "F12", "F18", "F19", "F22"],
            "provenance": [
                "https://github.com/szl-holdings/szl-second-brain",
                "https://github.com/szl-holdings/szl-formulas",
                "https://github.com/szl-holdings/szl-ouroboros",
                "https://huggingface.co/datasets/SZLHOLDINGS/szl-second-brain-inrepo",
            ],
        }
    )


class LivingAnatomyHandler(anatomy_server.HardenedHandler):
    """Add YACHAY v7 APIs while preserving every hardened Anatomy route."""

    def _brain_headers(self, evidence_state: str) -> dict[str, str]:
        return {
            "X-SZL-Brain-State": (
                "SOURCE_BOUND_RETRIEVAL_AND_FRONTIER"
                if BRAIN.ready
                else "UNAVAILABLE"
            ),
            "X-SZL-Brain-Authority": "READ_ONLY",
            "X-SZL-Brain-Evidence": evidence_state,
            "X-SZL-Brain-Content": "HANDLES_ONLY",
        }

    @staticmethod
    def _bounded_k(value: Any) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = 6
        return max(1, min(parsed, 24))

    @staticmethod
    def _blocked_internal_path(path: str) -> bool:
        return (
            path == "/.runtime"
            or path.startswith("/.runtime/")
            or path == "/.git"
            or path.startswith("/.git/")
        )

    def _read_json_body(
        self,
        maximum: int = 32_768,
    ) -> tuple[int, dict[str, Any] | None]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > maximum:
            return 400, None
        try:
            payload = json.loads(self.rfile.read(length))
        except Exception:
            return 400, None
        if not isinstance(payload, dict):
            return 400, None
        return 200, payload

    def _send_brain_payload(self, payload: dict[str, Any]) -> None:
        ready = bool(payload.get("ready"))
        evidence = "COMPUTED" if ready else "UNAVAILABLE"
        self._send_json(
            payload,
            status=200 if ready else 503,
            evidence_state=evidence,
            extra_headers=self._brain_headers(evidence),
        )

    def _send_frontier_payload(self, payload: dict[str, Any]) -> None:
        ready = bool(payload.get("ready"))
        evidence = "COMPUTED" if ready else "UNAVAILABLE"
        self._send_json(
            payload,
            status=200 if ready else 503,
            evidence_state=evidence,
            extra_headers={
                "X-SZL-Surface": "LIVING_ANATOMY_V7",
                "X-SZL-Authority": "READ_ONLY",
                "X-SZL-Content-Access": "HANDLES_ONLY",
            },
        )

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if self._blocked_internal_path(path):
            self._send_json(
                {
                    "error": "not_found",
                    "state": "BLOCKED_INTERNAL_RUNTIME_PATH",
                },
                status=404,
                evidence_state="UNAVAILABLE",
                extra_headers=self._brain_headers("UNAVAILABLE"),
            )
            return
        if path == "/api/anatomy/v1/frontier/status":
            self._send_frontier_payload(FRONTIER_ATLAS.status())
            return
        if path == "/api/anatomy/v1/frontier/handles":
            phrase = str((query.get("q") or [""])[0])[:2000]
            k = max(1, min(self._bounded_k((query.get("k") or [24])[0]), 48))
            self._send_frontier_payload(FRONTIER_ATLAS.search(phrase, k=k))
            return
        if path == "/api/anatomy/v1/frontier/formulas":
            phrase = str((query.get("q") or [""])[0])[:2000]
            domain = str((query.get("domain") or [""])[0])[:80] or None
            k = max(1, min(self._bounded_k((query.get("k") or [48])[0]), 48))
            self._send_frontier_payload(
                FRONTIER_ATLAS.search(
                    phrase,
                    k=k,
                    allowed_kinds=FORMULA_KINDS,
                    quant_domain=domain,
                )
            )
            return
        if path == "/api/anatomy/v1/frontier/ouroboros":
            phrase = str(
                (query.get("q") or ["bounded loop convergence receipt"])[0]
            )[:2000]
            k = max(1, min(self._bounded_k((query.get("k") or [24])[0]), 48))
            self._send_frontier_payload(
                FRONTIER_ATLAS.search(
                    phrase,
                    k=k,
                    source_repository="szl-holdings/szl-ouroboros",
                )
            )
            return
        if path == "/api/anatomy/v1/holographic-v7":
            self._send_frontier_payload(holographic_v7_payload())
            return
        if path == "/api/anatomy/v1/living-health":
            if query.get("refresh") == ["1"]:
                BRAIN.reload()
            brain = BRAIN.health()
            payload = {
                "schema": "szl.living-anatomy.health/v2",
                "status": "ok" if brain["ready"] else "degraded",
                "ready": bool(brain["ready"]),
                "service": "living-anatomy-space",
                "experience": "NEURAL_QUANT_V7",
                "transport_state": "REACHABLE",
                "evidence_state": (
                    "MEASURED" if brain["ready"] else "UNAVAILABLE"
                ),
                "verification_state": (
                    "STRUCTURAL_ONLY" if brain["ready"] else "FAILED"
                ),
                "authority_state": "READ_ONLY",
                "organs": {
                    "anatomy": {
                        "ready": True,
                        "state": "REACHABLE",
                        "contract": "/healthz",
                    },
                    "brain": {
                        "ready": brain["ready"],
                        "state": brain["state"],
                        "source_revision": brain["source_revision"],
                        "chunk_count": brain["chunk_count"],
                        "frontier_candidate_count": brain["frontier"][
                            "candidate_count"
                        ],
                        "candidate_set_sha256": brain["frontier"][
                            "candidate_set_sha256"
                        ],
                        "contract": "/api/anatomy/v1/brain/health",
                    },
                    "neural_quant": {
                        "ready": brain["ready"],
                        "attributed_formula_count": brain["formula_atlas"][
                            "attributed_formula_count"
                        ],
                        "executable_formula_count": brain["formula_atlas"][
                            "executable_formula_count"
                        ],
                        "locked_proven_count": brain["formula_atlas"][
                            "locked_proven_count"
                        ],
                        "quant_domain_count": brain["quant_domain_count"],
                        "lambda_state": "CONJECTURE_1",
                        "contract": "/api/anatomy/v1/brain/neural-quant-v7",
                    },
                },
                "note": (
                    "Combined readiness requires Anatomy transport plus exact, "
                    "source-bound Second Brain retrieval and frontier snapshots."
                ),
            }
            evidence = str(payload["evidence_state"])
            self._send_json(
                payload,
                status=200 if brain["ready"] else 503,
                evidence_state=evidence,
                extra_headers=self._brain_headers(evidence),
            )
            return
        if path == "/api/anatomy/v1/brain/health":
            if query.get("refresh") == ["1"]:
                BRAIN.reload()
            payload = BRAIN.health()
            evidence = str(payload["evidence_state"])
            self._send_json(
                payload,
                status=200 if payload["ready"] else 503,
                evidence_state=evidence,
                extra_headers=self._brain_headers(evidence),
            )
            return
        if path == "/api/anatomy/v1/brain/manifest":
            self._send_brain_payload(BRAIN.manifest())
            return
        if path in (
            "/api/anatomy/v1/brain/search",
            "/api/anatomy/v1/brain/query",
        ):
            phrase = (query.get("q") or query.get("query") or [""])[0]
            k = self._bounded_k((query.get("k") or [6])[0])
            self._send_brain_payload(BRAIN.search(phrase, k=k))
            return
        if path == "/api/anatomy/v1/brain/context":
            phrase = (query.get("q") or query.get("query") or [""])[0]
            k = self._bounded_k((query.get("k") or [6])[0])
            self._send_brain_payload(BRAIN.context(phrase, k=k))
            return
        if path == "/api/anatomy/v1/brain/frontier":
            phrase = (
                query.get("q")
                or query.get("query")
                or ["brain formula quant anatomy ouroboros"]
            )[0]
            k = self._bounded_k((query.get("k") or [12])[0])
            kinds_value = (query.get("kind") or [""])[0]
            kinds = {
                item.strip()
                for item in str(kinds_value).split(",")
                if item.strip()
            }
            domain = str((query.get("domain") or [""])[0]).strip() or None
            repository = (
                str((query.get("repository") or [""])[0]).strip() or None
            )
            self._send_brain_payload(
                BRAIN.frontier_search(
                    phrase,
                    k=k,
                    source_kinds=kinds or None,
                    quant_domain=domain,
                    source_repository=repository,
                )
            )
            return
        if path == "/api/anatomy/v1/brain/formulas":
            phrase = (
                query.get("q")
                or query.get("query")
                or ["formula authority proof status"]
            )[0]
            k = self._bounded_k((query.get("k") or [24])[0])
            self._send_brain_payload(BRAIN.formula_view(phrase, k=k))
            return
        if path == "/api/anatomy/v1/brain/quant":
            phrase = (
                query.get("q")
                or query.get("query")
                or ["quant math information geometry coding trust energy"]
            )[0]
            k = self._bounded_k((query.get("k") or [24])[0])
            self._send_brain_payload(BRAIN.quant_view(phrase, k=k))
            return
        if path == "/api/anatomy/v1/brain/ouroboros":
            k = self._bounded_k((query.get("k") or [16])[0])
            self._send_brain_payload(BRAIN.ouroboros_view(k=k))
            return
        if path == "/api/anatomy/v1/brain/neural-quant-v7":
            k = self._bounded_k((query.get("k") or [24])[0])
            self._send_brain_payload(BRAIN.neural_quant_view(k=k))
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        if path not in (
            "/api/anatomy/v1/brain/search",
            "/api/anatomy/v1/brain/query",
            "/api/anatomy/v1/brain/context",
            "/api/anatomy/v1/brain/frontier",
        ):
            super().do_POST()
            return
        status, body = self._read_json_body()
        if body is None:
            self._send_json(
                {
                    "error": "invalid_body",
                    "detail": "JSON object required; maximum 32,768 bytes.",
                },
                status=status,
                evidence_state="UNAVAILABLE",
                extra_headers=self._brain_headers("UNAVAILABLE"),
            )
            return
        phrase = str(body.get("query") or body.get("q") or "")
        k = self._bounded_k(body.get("k", 6))
        if path.endswith("/context"):
            payload = BRAIN.context(phrase, k=k)
        elif path.endswith("/frontier"):
            kinds_value = body.get("kinds") or body.get("kind") or []
            if isinstance(kinds_value, str):
                kinds = {
                    item.strip()
                    for item in kinds_value.split(",")
                    if item.strip()
                }
            elif isinstance(kinds_value, list):
                kinds = {
                    str(item).strip()
                    for item in kinds_value
                    if str(item).strip()
                }
            else:
                kinds = set()
            payload = BRAIN.frontier_search(
                phrase,
                k=k,
                source_kinds=kinds or None,
                quant_domain=str(body.get("domain") or "").strip() or None,
                source_repository=(
                    str(body.get("repository") or "").strip() or None
                ),
            )
        else:
            payload = BRAIN.search(phrase, k=k)
        self._send_brain_payload(payload)


def make_server(
    host: str = "0.0.0.0",
    port: int = anatomy_server.PORT,
) -> ThreadingHTTPServer:
    handler = functools.partial(
        LivingAnatomyHandler,
        directory=str(anatomy_server.DIRECTORY),
    )
    return ThreadingHTTPServer((host, port), handler)


if __name__ == "__main__":
    httpd = make_server()
    health = BRAIN.health()
    print(
        "Serving SZL Living Anatomy + YACHAY Neural Quant v7 "
        f"from {anatomy_server.DIRECTORY} on 0.0.0.0:{anatomy_server.PORT}; "
        f"brain_ready={BRAIN.ready} source={BRAIN.source_revision} "
        f"frontier={health['frontier']['candidate_count']}",
        flush=True,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
