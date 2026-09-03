#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Unified Python runtime for SZL Living Anatomy + YACHAY Second Brain.

The existing Anatomy server remains the transport, evidence, receipt, and static
rendering authority. This module extends it in-process with a source-bound,
handles-only Second Brain organ and makes the combined body the Docker entry
point. No reverse proxy, second process, model inference, private graph, or
write authority is introduced.
"""
from __future__ import annotations

import functools
import json
from http.server import ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlsplit

import server as anatomy_server
from second_brain_runtime import PublicSecondBrain

BRAIN = PublicSecondBrain()

# Bind the new runtime and its source snapshot into the existing deterministic
# Anatomy receipt before the first request can populate any receipt cache.
_EXTRA_ARTIFACTS = (
    "living_runtime.py",
    "second_brain_runtime.py",
    ".runtime/second-brain/manifest.json",
    ".runtime/second-brain/brain-corpus.public.jsonl",
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
    payload["service"] = "living-anatomy-space"
    payload["purpose"] = (
        "Read-only spatial evidence map with a source-bound YACHAY Second Brain organ."
    )
    payload["contract_version"] = "1.2.0"
    endpoints = payload.setdefault("endpoints", {})
    endpoints.update(
        {
            "living_health": "/api/anatomy/v1/living-health",
            "brain_health": "/api/anatomy/v1/brain/health",
            "brain_manifest": "/api/anatomy/v1/brain/manifest",
            "brain_search": "/api/anatomy/v1/brain/search",
            "brain_context": "/api/anatomy/v1/brain/context",
        }
    )
    payload["organs"] = {
        "brain": {
            "name": "YACHAY",
            "state": BRAIN.health()["state"],
            "ready": BRAIN.ready,
            "source_repository": BRAIN.health()["source_repository"],
            "source_revision": BRAIN.source_revision,
            "authority_state": "READ_ONLY",
            "content_access": "HANDLES_ONLY",
        }
    }
    payload.setdefault("limits", []).extend(
        [
            "Second Brain ranking is lexical relevance, never correctness.",
            "The public projection contains handles only; the private graph is not present.",
        ]
    )
    return payload


def _living_version(force: bool = False) -> dict[str, Any]:
    payload = _ORIGINAL_VERSION(force=force)
    payload["contractVersion"] = "1.2.0"
    payload["runtime"] = "living-anatomy+yachay"
    payload["secondBrainSourceRevision"] = BRAIN.source_revision
    payload["secondBrainEvidenceState"] = "MEASURED" if BRAIN.ready else "UNAVAILABLE"
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
        "verificationState": brain["verification_state"],
        "authorityState": brain["authority_state"],
        "details": "/api/anatomy/v1/brain/health",
    }
    runtime = payload.setdefault("runtime", {})
    if not BRAIN.ready:
        runtime["status"] = "DEGRADED"
        runtime["ready"] = False
        payload.setdefault("limitations", []).append(
            "YACHAY Second Brain snapshot is unavailable; Living Anatomy remains transport-reachable but the integrated body is not ready."
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
            "name": "YACHAY source-bound Second Brain",
            "purpose": (
                "Ground the Living Anatomy brain organ in the public 575-chunk "
                "Second Brain projection without exposing corpus text or private nodes."
            ),
            "try": {
                "method": "GET",
                "path": "/api/anatomy/v1/brain/search?q=governed%20receipts&k=6",
                "action": "Retrieve source-bound public handles.",
            },
            "evidence": {
                "state": "MEASURED" if BRAIN.ready else "UNAVAILABLE",
                "basis": (
                    "Deployment-pinned GitHub revision, manifest digest, corpus digest, "
                    "per-row SHA-256 checks, and exact chunk count."
                ),
                "source_revision": BRAIN.source_revision,
                "chunk_count": BRAIN.health()["chunk_count"],
            },
            "limits": [
                "Lexical overlap is not correctness.",
                "No corpus text is returned by the retrieval API.",
                "No private graph node is bundled or queried.",
                "No write or training authority is granted.",
            ],
            "reproduce": {
                "steps": [
                    "GET /api/anatomy/v1/brain/health",
                    "Compare source_revision with szl-holdings/szl-second-brain.",
                    "GET /api/anatomy/v1/brain/manifest and inspect the snapshot receipt.",
                    "Run a search and verify every result is a handle with a SHA-256 pointer.",
                ]
            },
            "authority_state": "READ_ONLY",
            "formula_refs": ["F1", "F22"],
            "provenance": [
                "https://github.com/szl-holdings/szl-second-brain",
                "https://huggingface.co/datasets/SZLHOLDINGS/szl-second-brain-inrepo",
            ],
        }
    )


class LivingAnatomyHandler(anatomy_server.HardenedHandler):
    """Add the YACHAY API while preserving every existing Anatomy route."""

    def _brain_headers(self, evidence_state: str) -> dict[str, str]:
        return {
            "X-SZL-Brain-State": (
                "SOURCE_BOUND_PUBLIC_PROJECTION" if BRAIN.ready else "UNAVAILABLE"
            ),
            "X-SZL-Brain-Authority": "READ_ONLY",
            "X-SZL-Brain-Evidence": evidence_state,
        }

    @staticmethod
    def _bounded_k(value: Any) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = 6
        return max(1, min(parsed, 12))

    def _read_json_body(self, maximum: int = 32_768) -> tuple[int, dict[str, Any] | None]:
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

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        if path == "/api/anatomy/v1/living-health":
            if query.get("refresh") == ["1"]:
                BRAIN.reload()
            brain = BRAIN.health()
            payload = {
                "schema": "szl.living-anatomy.health/v1",
                "status": "ok" if brain["ready"] else "degraded",
                "ready": bool(brain["ready"]),
                "service": "living-anatomy-space",
                "transport_state": "REACHABLE",
                "evidence_state": "MEASURED" if brain["ready"] else "UNAVAILABLE",
                "verification_state": "STRUCTURAL_ONLY" if brain["ready"] else "FAILED",
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
                        "contract": "/api/anatomy/v1/brain/health",
                    },
                },
                "note": (
                    "Combined readiness requires both the Anatomy transport and the "
                    "source-bound public Second Brain projection."
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
            payload = BRAIN.manifest()
            evidence = "MEASURED" if payload["ready"] else "UNAVAILABLE"
            self._send_json(
                payload,
                status=200 if payload["ready"] else 503,
                evidence_state=evidence,
                extra_headers=self._brain_headers(evidence),
            )
            return
        if path in (
            "/api/anatomy/v1/brain/search",
            "/api/anatomy/v1/brain/query",
        ):
            phrase = (query.get("q") or query.get("query") or [""])[0]
            k = self._bounded_k((query.get("k") or [6])[0])
            payload = BRAIN.search(phrase, k=k)
            evidence = "COMPUTED" if payload["ready"] else "UNAVAILABLE"
            self._send_json(
                payload,
                status=200 if payload["ready"] else 503,
                evidence_state=evidence,
                extra_headers=self._brain_headers(evidence),
            )
            return
        if path == "/api/anatomy/v1/brain/context":
            phrase = (query.get("q") or query.get("query") or [""])[0]
            k = self._bounded_k((query.get("k") or [6])[0])
            payload = BRAIN.context(phrase, k=k)
            evidence = "COMPUTED" if payload["ready"] else "UNAVAILABLE"
            self._send_json(
                payload,
                status=200 if payload["ready"] else 503,
                evidence_state=evidence,
                extra_headers=self._brain_headers(evidence),
            )
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        if path not in (
            "/api/anatomy/v1/brain/search",
            "/api/anatomy/v1/brain/query",
            "/api/anatomy/v1/brain/context",
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
        payload = (
            BRAIN.context(phrase, k=k)
            if path.endswith("/context")
            else BRAIN.search(phrase, k=k)
        )
        evidence = "COMPUTED" if payload["ready"] else "UNAVAILABLE"
        self._send_json(
            payload,
            status=200 if payload["ready"] else 503,
            evidence_state=evidence,
            extra_headers=self._brain_headers(evidence),
        )


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
    print(
        "Serving SZL Living Anatomy + YACHAY Second Brain "
        f"from {anatomy_server.DIRECTORY} on 0.0.0.0:{anatomy_server.PORT}; "
        f"brain_ready={BRAIN.ready} source={BRAIN.source_revision}",
        flush=True,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
