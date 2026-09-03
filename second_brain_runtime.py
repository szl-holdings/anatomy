#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Source-bound public Second Brain runtime for SZL Living Anatomy.

This module is deliberately read-only. It loads the public, source-bound
Second Brain projection bundled by the deployment workflow, validates the
snapshot receipt, and exposes lexical retrieval as handles only. It never
loads the owner's private graph, never returns corpus text, never trains model
weights, and never grants write authority.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import threading
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_HEALTH = "szl.living-anatomy.second-brain.health/v1"
SCHEMA_SEARCH = "szl.living-anatomy.second-brain.search/v1"
SCHEMA_CONTEXT = "szl.living-anatomy.second-brain.context/v1"
SCHEMA_MANIFEST = "szl.living-anatomy.second-brain.manifest/v1"
SOURCE_REPOSITORY = "szl-holdings/szl-second-brain"
CANONICAL_DATASET = "SZLHOLDINGS/szl-second-brain-inrepo"
PUBLIC_CHUNK_COUNT = 575
PRIVATE_GRAPH_NODES_DISCLOSED = 9464
MAX_QUERY_CHARS = 500
MAX_K = 12

TOKEN = re.compile(r"[a-z0-9λ]+", re.I)
STOP = {
    "the", "is", "a", "an", "of", "and", "or", "to", "in", "for", "on", "at",
    "by", "as", "what", "which", "who", "how", "why", "does", "did", "are",
    "was", "be", "it", "this", "that", "with", "from", "into", "over", "not",
}

ROOT = Path(__file__).resolve().parent
SNAPSHOT_ROOT = Path(
    os.environ.get(
        "SECOND_BRAIN_SNAPSHOT_ROOT",
        str(ROOT / ".runtime" / "second-brain"),
    )
).resolve()
MANIFEST_PATH = SNAPSHOT_ROOT / "manifest.json"
CORPUS_PATH = SNAPSHOT_ROOT / "brain-corpus.public.jsonl"
SOURCE_PATH = SNAPSHOT_ROOT / "source.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_sha256(value: Any) -> str:
    return _sha256_bytes(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    )


def _tokenize(value: str) -> list[str]:
    return [
        token.lower()
        for token in TOKEN.findall(value or "")
        if len(token) > 1 and token.lower() not in STOP
    ]


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return payload


def _valid_revision(value: Any) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{40}", value.lower()))


class PublicSecondBrain:
    """Validated lexical index over the public handles-only projection."""

    def __init__(self, snapshot_root: Path | None = None) -> None:
        self.snapshot_root = Path(snapshot_root or SNAPSHOT_ROOT).resolve()
        self.manifest_path = self.snapshot_root / "manifest.json"
        self.corpus_path = self.snapshot_root / "brain-corpus.public.jsonl"
        self.source_path = self.snapshot_root / "source.json"
        self._lock = threading.RLock()
        self._rows: list[dict[str, Any]] = []
        self._df: Counter[str] = Counter()
        self._manifest: dict[str, Any] = {}
        self._source: dict[str, Any] = {}
        self._load_error: str | None = None
        self._loaded_at: str | None = None
        self.reload()

    def reload(self) -> dict[str, Any]:
        with self._lock:
            self._rows = []
            self._df = Counter()
            self._manifest = {}
            self._source = {}
            self._load_error = None
            self._loaded_at = None
            try:
                manifest_raw = self.manifest_path.read_bytes()
                corpus_raw = self.corpus_path.read_bytes()
                source = _read_json(self.source_path)
                manifest = json.loads(manifest_raw.decode("utf-8"))
                if not isinstance(manifest, dict):
                    raise ValueError("manifest.json must contain a JSON object")
                if source.get("schema") != "szl.second-brain.snapshot/v1":
                    raise ValueError("unsupported source receipt schema")
                if source.get("source_repository") != SOURCE_REPOSITORY:
                    raise ValueError("unexpected Second Brain source repository")
                if not _valid_revision(source.get("source_revision")):
                    raise ValueError("Second Brain source revision is not an exact Git SHA")
                if source.get("manifest_sha256") != _sha256_bytes(manifest_raw):
                    raise ValueError("Second Brain manifest digest mismatch")
                if source.get("corpus_sha256") != _sha256_bytes(corpus_raw):
                    raise ValueError("Second Brain corpus digest mismatch")

                rows: list[dict[str, Any]] = []
                document_frequency: Counter[str] = Counter()
                for line_number, line in enumerate(corpus_raw.decode("utf-8").splitlines(), start=1):
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    if not isinstance(row, dict) or not row.get("id"):
                        raise ValueError(f"invalid corpus row at line {line_number}")
                    text = str(row.get("text") or "")
                    declared_digest = str(row.get("sha256") or "")
                    measured_digest = _sha256_bytes(text.encode("utf-8"))
                    if declared_digest and declared_digest != measured_digest:
                        raise ValueError(f"row digest mismatch at line {line_number}")
                    tokens = _tokenize(f"{row.get('title', '')} {text}")
                    stored = {
                        "id": str(row["id"]),
                        "title": str(row.get("title") or ""),
                        "source": str(row.get("source") or "unknown"),
                        "sourceId": row.get("sourceId"),
                        "sha256": measured_digest,
                        "_tf": Counter(tokens),
                    }
                    rows.append(stored)
                    document_frequency.update(set(tokens))

                declared_count = int(manifest.get("publicChunkCount") or 0)
                receipt_count = int(source.get("public_chunk_count") or 0)
                if declared_count != len(rows) or receipt_count != len(rows):
                    raise ValueError(
                        "public chunk count mismatch "
                        f"(manifest={declared_count}, receipt={receipt_count}, loaded={len(rows)})"
                    )
                if len(rows) != PUBLIC_CHUNK_COUNT:
                    raise ValueError(
                        f"expected {PUBLIC_CHUNK_COUNT} public chunks, loaded {len(rows)}"
                    )
                if str(manifest.get("secretScan") or "").upper() != "PASS":
                    raise ValueError("public projection secret scan is not PASS")

                self._rows = rows
                self._df = document_frequency
                self._manifest = manifest
                self._source = source
                self._loaded_at = _utc_now()
            except Exception as exc:
                self._load_error = f"{type(exc).__name__}: {exc}"
            return self.health()

    @property
    def ready(self) -> bool:
        return self._load_error is None and len(self._rows) == PUBLIC_CHUNK_COUNT

    @property
    def source_revision(self) -> str | None:
        value = self._source.get("source_revision")
        return str(value) if _valid_revision(value) else None

    def health(self) -> dict[str, Any]:
        with self._lock:
            by_source: dict[str, int] = {}
            for row in self._rows:
                source = str(row.get("source") or "unknown")
                by_source[source] = by_source.get(source, 0) + 1
            return {
                "schema": SCHEMA_HEALTH,
                "service": "living-anatomy-yachay-second-brain",
                "ready": self.ready,
                "state": "SOURCE_BOUND_PUBLIC_PROJECTION" if self.ready else "UNAVAILABLE",
                "transport_state": "REACHABLE",
                "evidence_state": "MEASURED" if self.ready else "UNAVAILABLE",
                "verification_state": "STRUCTURAL_ONLY" if self.ready else "FAILED",
                "authority_state": "READ_ONLY",
                "kind": "SOFTWARE",
                "content_access": "HANDLES_ONLY",
                "source_repository": SOURCE_REPOSITORY,
                "source_revision": self.source_revision,
                "canonical_dataset": CANONICAL_DATASET,
                "chunk_count": len(self._rows),
                "declared_public_chunk_count": PUBLIC_CHUNK_COUNT,
                "by_source": by_source,
                "snapshot_root": str(self.snapshot_root),
                "loaded_at": self._loaded_at,
                "load_error": self._load_error,
                "index_is_model_weights": False,
                "private_graph_nodes_loaded": 0,
                "private_graph_nodes_disclosed_elsewhere": PRIVATE_GRAPH_NODES_DISCLOSED,
                "raw_graph_nodes_admitted_to_gradients": 0,
                "lambda_state": "CONJECTURE_1",
                "limits": [
                    "Lexical overlap is not correctness.",
                    "Only public handles are returned; corpus text remains inside the controller.",
                    "The owner's private graph is not bundled, queried, or exposed.",
                    "This read-only organ cannot authorize or execute an action.",
                ],
            }

    def manifest(self) -> dict[str, Any]:
        health = self.health()
        return {
            "schema": SCHEMA_MANIFEST,
            "service": health["service"],
            "ready": health["ready"],
            "source": {
                "repository": SOURCE_REPOSITORY,
                "revision": self.source_revision,
                "dataset": CANONICAL_DATASET,
                "snapshot_receipt": self._source,
            },
            "corpus": {
                "chunk_count": len(self._rows),
                "by_source": health["by_source"],
                "manifest": self._manifest,
            },
            "interfaces": {
                "health": "/api/anatomy/v1/brain/health",
                "manifest": "/api/anatomy/v1/brain/manifest",
                "search": "/api/anatomy/v1/brain/search",
                "context": "/api/anatomy/v1/brain/context",
            },
            "authority_state": "READ_ONLY",
            "content_access": "HANDLES_ONLY",
            "limits": health["limits"],
        }

    @staticmethod
    def _handle(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "nodeId": row["id"],
            "nodeKind": "INDEX",
            "label": "DECLARED",
            "note": str(row.get("title") or "")[:160],
            "source": row.get("source"),
            "sourceId": row.get("sourceId"),
            "sha256": row.get("sha256"),
        }

    def search(self, query: str, k: int = 6) -> dict[str, Any]:
        query = str(query or "").strip()
        if len(query) > MAX_QUERY_CHARS:
            query = query[:MAX_QUERY_CHARS]
        try:
            requested_k = int(k)
        except (TypeError, ValueError):
            requested_k = 6
        requested_k = max(1, min(requested_k, MAX_K))

        with self._lock:
            if not self.ready:
                return {
                    "schema": SCHEMA_SEARCH,
                    "ready": False,
                    "query": query,
                    "handles": [],
                    "scores": [],
                    "source_revision": self.source_revision,
                    "error": self._load_error or "Second Brain snapshot unavailable",
                    "authority_state": "READ_ONLY",
                    "content_access": "HANDLES_ONLY",
                }
            query_tokens = _tokenize(query)
            if not query_tokens:
                return {
                    "schema": SCHEMA_SEARCH,
                    "ready": True,
                    "query": query,
                    "handles": [],
                    "scores": [],
                    "source_revision": self.source_revision,
                    "honesty": "Empty or stop-word-only query; no ranking fabricated.",
                    "authority_state": "READ_ONLY",
                    "content_access": "HANDLES_ONLY",
                }

            query_frequency = Counter(query_tokens)
            scored: list[tuple[float, dict[str, Any]]] = []
            total = max(1, len(self._rows))
            for row in self._rows:
                score = 0.0
                row_frequency: Counter[str] = row["_tf"]
                for term, query_count in query_frequency.items():
                    term_frequency = row_frequency.get(term, 0)
                    if not term_frequency:
                        continue
                    inverse_document_frequency = (
                        math.log((total + 1) / (1 + self._df.get(term, 0))) + 1.0
                    )
                    score += (
                        term_frequency / (term_frequency + 1.2)
                    ) * inverse_document_frequency * query_count
                if score > 0:
                    scored.append((score, row))
            scored.sort(key=lambda item: (-item[0], str(item[1]["id"])))
            top = scored[:requested_k]
            handles = [self._handle(row) for _, row in top]
            scores = [round(score, 6) for score, _ in top]
            result_body = {
                "query": query,
                "handles": handles,
                "scores": scores,
                "source_revision": self.source_revision,
                "corpus_chunk_count": len(self._rows),
                "ranking": "BM25_LIKE_LEXICAL",
                "content_access": "HANDLES_ONLY",
            }
            return {
                "schema": SCHEMA_SEARCH,
                "ready": True,
                **result_body,
                "result_sha256": _canonical_sha256(result_body),
                "authority_state": "READ_ONLY",
                "index_is_model_weights": False,
                "honesty": (
                    "Ranked lexical overlap over the public source-bound projection; "
                    "scores are relevance signals, never correctness or proof."
                ),
            }

    def context(self, query: str, k: int = 6) -> dict[str, Any]:
        search = self.search(query, k=k)
        handles = search.get("handles") if isinstance(search, dict) else []
        handles = handles if isinstance(handles, list) else []
        model_handles = [
            {
                key: handle[key]
                for key in ("nodeId", "nodeKind", "label", "note")
                if key in handle
            }
            for handle in handles
            if isinstance(handle, dict)
        ]
        evidence = [
            {
                "node_id": handle.get("nodeId"),
                "source": handle.get("source"),
                "source_id": handle.get("sourceId"),
                "sha256": handle.get("sha256"),
            }
            for handle in handles
            if isinstance(handle, dict)
        ]
        body = {
            "query": search.get("query"),
            "model_handles": model_handles,
            "evidence": evidence,
            "source_revision": search.get("source_revision"),
            "ready": bool(search.get("ready")),
        }
        return {
            "schema": SCHEMA_CONTEXT,
            **body,
            "context_sha256": _canonical_sha256(body),
            "training_authority": "NONE",
            "write_authority": "NONE",
            "private_graph_nodes_loaded": 0,
            "honesty": search.get("honesty"),
            "error": search.get("error"),
        }
