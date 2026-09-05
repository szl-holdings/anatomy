#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Source-bound Second Brain + frontier runtime for SZL Living Anatomy v7.

The runtime loads two immutable public-memory planes bundled by the deployment
workflow:

1. the 575-chunk governed retrieval projection; and
2. the review-gated frontier candidate set bound to its public source manifest.

Every source revision, row digest, set digest, formula count, quant-domain count,
and authority boundary is replayed before readiness. Public methods return handles,
counts, and digests only. Candidate and corpus content remain internal to this
read-only process. The owner's private graph is never loaded, model weights are not
trained, and no promotion, execution, merge, or provider authority is granted.
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

SCHEMA_HEALTH = "szl.living-anatomy.second-brain.health/v2"
SCHEMA_SEARCH = "szl.living-anatomy.second-brain.search/v1"
SCHEMA_CONTEXT = "szl.living-anatomy.second-brain.context/v1"
SCHEMA_MANIFEST = "szl.living-anatomy.second-brain.manifest/v2"
SCHEMA_FRONTIER = "szl.living-anatomy.frontier-search/v1"
SCHEMA_FORMULAS = "szl.living-anatomy.formula-atlas/v1"
SCHEMA_QUANT = "szl.living-anatomy.quant-atlas/v1"
SCHEMA_OUROBOROS = "szl.living-anatomy.ouroboros-observation/v1"
SCHEMA_NEURAL_QUANT = "szl.living-anatomy.neural-quant-v7/v1"
SOURCE_REPOSITORY = "szl-holdings/szl-second-brain"
CANONICAL_DATASET = "SZLHOLDINGS/szl-second-brain-inrepo"
PUBLIC_CHUNK_COUNT = 575
MIN_FRONTIER_CANDIDATES = 70
MIN_FRONTIER_SOURCES = 6
EXPECTED_ATTRIBUTED_FORMULAS = 30
EXPECTED_EXECUTABLE_FORMULAS = 21
EXPECTED_QUANT_DOMAINS = 9
EXPECTED_LOCKED_PROVEN = 8
PRIVATE_GRAPH_NODES_DISCLOSED = 9464
MAX_QUERY_CHARS = 500
MAX_K = 24
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
FRONTIER_ID = re.compile(r"^frontier:[0-9a-f]{32}$")
TOKEN = re.compile(r"[a-z0-9λ_.:/+-]+", re.I)
STOP = {
    "the",
    "is",
    "a",
    "an",
    "of",
    "and",
    "or",
    "to",
    "in",
    "for",
    "on",
    "at",
    "by",
    "as",
    "what",
    "which",
    "who",
    "how",
    "why",
    "does",
    "did",
    "are",
    "was",
    "be",
    "it",
    "this",
    "that",
    "with",
    "from",
    "into",
    "over",
    "not",
}

ROOT = Path(__file__).resolve().parent
SNAPSHOT_ROOT = Path(
    os.environ.get(
        "SECOND_BRAIN_SNAPSHOT_ROOT",
        str(ROOT / ".runtime" / "second-brain"),
    )
).resolve()


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _canonical_sha256(value: Any) -> str:
    return _sha256_bytes(_canonical_bytes(value))


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
    return isinstance(value, str) and bool(HEX_40.fullmatch(value.lower()))


def _valid_digest(value: Any) -> bool:
    return isinstance(value, str) and bool(HEX_64.fullmatch(value.lower()))


def _bounded_k(value: Any, default: int = 6) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(1, min(parsed, MAX_K))


class PublicSecondBrain:
    """Validated read-only index over retrieval and frontier public memory."""

    def __init__(self, snapshot_root: Path | None = None) -> None:
        self.snapshot_root = Path(snapshot_root or SNAPSHOT_ROOT).resolve()
        self.manifest_path = self.snapshot_root / "manifest.json"
        self.corpus_path = self.snapshot_root / "brain-corpus.public.jsonl"
        self.frontier_state_path = self.snapshot_root / "frontier-state.v1.json"
        self.frontier_candidates_path = (
            self.snapshot_root / "frontier-candidates.public.jsonl"
        )
        self.source_path = self.snapshot_root / "source.json"
        self._lock = threading.RLock()
        self._rows: list[dict[str, Any]] = []
        self._df: Counter[str] = Counter()
        self._frontier_rows: list[dict[str, Any]] = []
        self._frontier_df: Counter[str] = Counter()
        self._manifest: dict[str, Any] = {}
        self._frontier_state: dict[str, Any] = {}
        self._formula_authority: dict[str, Any] = {}
        self._source: dict[str, Any] = {}
        self._load_error: str | None = None
        self._loaded_at: str | None = None
        self.reload()

    def reload(self) -> dict[str, Any]:
        with self._lock:
            self._rows = []
            self._df = Counter()
            self._frontier_rows = []
            self._frontier_df = Counter()
            self._manifest = {}
            self._frontier_state = {}
            self._formula_authority = {}
            self._source = {}
            self._load_error = None
            self._loaded_at = None
            try:
                manifest_raw = self.manifest_path.read_bytes()
                corpus_raw = self.corpus_path.read_bytes()
                frontier_state_raw = self.frontier_state_path.read_bytes()
                frontier_candidates_raw = self.frontier_candidates_path.read_bytes()
                source = _read_json(self.source_path)
                manifest = json.loads(manifest_raw.decode("utf-8"))
                frontier_state = json.loads(frontier_state_raw.decode("utf-8"))
                if not isinstance(manifest, dict):
                    raise ValueError("manifest.json must contain a JSON object")
                if not isinstance(frontier_state, dict):
                    raise ValueError("frontier-state.v1.json must contain a JSON object")
                self._validate_source_receipt(
                    source,
                    manifest_raw=manifest_raw,
                    corpus_raw=corpus_raw,
                    frontier_state_raw=frontier_state_raw,
                    frontier_candidates_raw=frontier_candidates_raw,
                )
                rows, document_frequency = self._load_retrieval_rows(
                    manifest,
                    corpus_raw,
                    source,
                )
                (
                    frontier_rows,
                    frontier_frequency,
                    formula_authority,
                ) = self._load_frontier_rows(
                    frontier_state,
                    frontier_candidates_raw,
                    source,
                )
                self._rows = rows
                self._df = document_frequency
                self._frontier_rows = frontier_rows
                self._frontier_df = frontier_frequency
                self._manifest = manifest
                self._frontier_state = frontier_state
                self._formula_authority = formula_authority
                self._source = source
                self._loaded_at = _utc_now()
            except Exception as exc:
                self._load_error = f"{type(exc).__name__}: {exc}"
            return self.health()

    @staticmethod
    def _validate_source_receipt(
        source: dict[str, Any],
        *,
        manifest_raw: bytes,
        corpus_raw: bytes,
        frontier_state_raw: bytes,
        frontier_candidates_raw: bytes,
    ) -> None:
        if source.get("schema") != "szl.second-brain.snapshot/v1":
            raise ValueError("unsupported source receipt schema")
        if source.get("source_repository") != SOURCE_REPOSITORY:
            raise ValueError("unexpected Second Brain source repository")
        if not _valid_revision(source.get("source_revision")):
            raise ValueError("Second Brain source revision is not an exact Git SHA")
        expected_digests = {
            "manifest_sha256": _sha256_bytes(manifest_raw),
            "corpus_sha256": _sha256_bytes(corpus_raw),
            "frontier_state_sha256": _sha256_bytes(frontier_state_raw),
            "frontier_candidates_sha256": _sha256_bytes(frontier_candidates_raw),
        }
        for key, measured in expected_digests.items():
            if source.get(key) != measured:
                raise ValueError(f"Second Brain {key} mismatch")
        expected_authority = {
            "private_graph_nodes_materialized": 0,
            "raw_graph_nodes_admitted_to_gradients": 0,
            "training_authority": "NONE",
            "promotion_authority": "NONE",
            "execution_authority": "NONE",
            "merge_authority": "NONE",
            "lambda_state": "CONJECTURE_1",
        }
        for key, value in expected_authority.items():
            if source.get(key) != value:
                raise ValueError(f"Second Brain source authority drift: {key}")

    @staticmethod
    def _load_retrieval_rows(
        manifest: dict[str, Any],
        corpus_raw: bytes,
        source: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], Counter[str]]:
        rows: list[dict[str, Any]] = []
        document_frequency: Counter[str] = Counter()
        ids: set[str] = set()
        for line_number, line in enumerate(
            corpus_raw.decode("utf-8").splitlines(),
            start=1,
        ):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict) or not row.get("id"):
                raise ValueError(f"invalid corpus row at line {line_number}")
            node_id = str(row["id"])
            if node_id in ids:
                raise ValueError(f"duplicate corpus id at line {line_number}")
            ids.add(node_id)
            text = str(row.get("text") or "")
            declared_digest = str(row.get("sha256") or "")
            measured_digest = _sha256_bytes(text.encode("utf-8"))
            if declared_digest and declared_digest != measured_digest:
                raise ValueError(f"row digest mismatch at line {line_number}")
            tokens = _tokenize(f"{row.get('title', '')} {text}")
            stored = {
                "id": node_id,
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
        return rows, document_frequency

    @staticmethod
    def _load_frontier_rows(
        state: dict[str, Any],
        candidates_raw: bytes,
        source: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], Counter[str], dict[str, Any]]:
        if state.get("schema") != "szl.second-brain.frontier-state/v1":
            raise ValueError("unsupported frontier state schema")
        expected_state = {
            "state": "REVIEW_REQUIRED",
            "public_content_access": "HANDLES_ONLY",
            "controller_content_access": "AUTHORIZED_CONTROLLER_ONLY",
            "training_authority": "NONE",
            "promotion_authority": "NONE",
            "execution_authority": "NONE",
            "merge_authority": "NONE",
            "lambda": "CONJECTURE_1",
        }
        for key, value in expected_state.items():
            if state.get(key) != value:
                raise ValueError(f"frontier authority drift: {key}")
        if int(state.get("private_graph_nodes_loaded") or 0) != 0:
            raise ValueError("private graph material entered the frontier index")
        if int(state.get("raw_graph_nodes_admitted_to_gradients") or 0) != 0:
            raise ValueError("frontier index admitted raw graph nodes to gradients")
        source_count = state.get("source_count")
        sources = state.get("sources")
        if type(source_count) is not int or source_count < MIN_FRONTIER_SOURCES:
            raise ValueError("frontier source inventory is incomplete")
        if not isinstance(sources, list) or len(sources) != source_count:
            raise ValueError("frontier source manifest count drifted")
        source_ids: set[str] = set()
        expected_source_counts: dict[tuple[str, str, str], int] = {}
        observed_source_counts: dict[tuple[str, str, str], int] = {}
        for index, entry in enumerate(sources, start=1):
            if not isinstance(entry, dict):
                raise ValueError(f"invalid frontier source at index {index}")
            source_id = str(entry.get("source_id") or "")
            repository = str(entry.get("repository") or "")
            revision = str(entry.get("revision") or "")
            digest = str(entry.get("content_sha256") or "")
            parser = entry.get("parser")
            path = entry.get("path")
            candidate_count = entry.get("candidate_count")
            if not source_id or source_id in source_ids:
                raise ValueError(f"frontier source identity failed at index {index}")
            if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
                raise ValueError(f"frontier source repository failed at index {index}")
            if not HEX_40.fullmatch(revision) or not HEX_64.fullmatch(digest):
                raise ValueError(f"frontier source binding failed at index {index}")
            if (
                not isinstance(parser, str)
                or not parser.strip()
                or not isinstance(path, str)
                or not path.strip()
                or type(candidate_count) is not int
                or candidate_count < 1
            ):
                raise ValueError(f"frontier source metadata failed at index {index}")
            binding = (repository, revision, path)
            if binding in expected_source_counts:
                raise ValueError(f"duplicate frontier source binding at index {index}")
            source_ids.add(source_id)
            expected_source_counts[binding] = candidate_count
            observed_source_counts[binding] = 0

        kind_counts = state.get("source_kind_counts")
        domain_counts = state.get("quant_domain_counts")
        if not isinstance(kind_counts, dict) or not isinstance(domain_counts, dict):
            raise ValueError("frontier formula/quant summaries are unavailable")
        if int(kind_counts.get("attributed-formula") or 0) != EXPECTED_ATTRIBUTED_FORMULAS:
            raise ValueError("attributed formula count drifted")
        if int(kind_counts.get("executable-formula") or 0) != EXPECTED_EXECUTABLE_FORMULAS:
            raise ValueError("executable formula count drifted")
        if int(kind_counts.get("quant-domain") or 0) != EXPECTED_QUANT_DOMAINS:
            raise ValueError("quant-domain record count drifted")
        if len(domain_counts) != EXPECTED_QUANT_DOMAINS:
            raise ValueError("quant-domain taxonomy drifted")

        rows: list[dict[str, Any]] = []
        document_frequency: Counter[str] = Counter()
        ids: set[str] = set()
        canonical_lines: list[bytes] = []
        formula_authority: dict[str, Any] | None = None
        for line_number, line in enumerate(
            candidates_raw.decode("utf-8").splitlines(),
            start=1,
        ):
            if not line.strip():
                continue
            row = json.loads(line)
            if (
                not isinstance(row, dict)
                or row.get("schema")
                != "szl.second-brain.frontier-candidate/v1"
            ):
                raise ValueError(f"invalid frontier candidate at line {line_number}")
            candidate_id = str(row.get("id") or "")
            if not FRONTIER_ID.fullmatch(candidate_id) or candidate_id in ids:
                raise ValueError(
                    f"frontier candidate identity failed at line {line_number}"
                )
            ids.add(candidate_id)
            revision = str(row.get("source_revision") or "")
            digest = str(row.get("content_sha256") or "")
            if not _valid_revision(revision) or not _valid_digest(digest):
                raise ValueError(
                    f"frontier source binding failed at line {line_number}"
                )
            binding = (
                str(row.get("source_repository") or ""),
                revision,
                str(row.get("source_path") or ""),
            )
            if binding not in expected_source_counts:
                raise ValueError(f"frontier source manifest binding failed at line {line_number}")
            observed_source_counts[binding] += 1
            content = str(row.get("content") or "")
            if _sha256_bytes(content.encode("utf-8")) != digest:
                raise ValueError(f"frontier digest mismatch at line {line_number}")
            if row.get("candidate_state") != "DISCOVERED_REVIEW_REQUIRED":
                raise ValueError(
                    f"frontier candidate was promoted at line {line_number}"
                )
            if row.get("content_access") != "CONTROLLER_ONLY":
                raise ValueError(
                    f"frontier content boundary drifted at line {line_number}"
                )
            tokens = _tokenize(
                " ".join(
                    (
                        str(row.get("title") or ""),
                        str(row.get("source_repository") or ""),
                        str(row.get("source_path") or ""),
                        str(row.get("source_kind") or ""),
                        str(row.get("quant_domain") or ""),
                        content,
                    )
                )
            )
            stored = {
                "id": candidate_id,
                "title": str(row.get("title") or ""),
                "content": content,
                "sha256": digest,
                "source_repository": str(row.get("source_repository") or ""),
                "source_revision": revision,
                "source_path": str(row.get("source_path") or ""),
                "source_kind": str(row.get("source_kind") or ""),
                "quant_domain": (
                    str(row.get("quant_domain"))
                    if row.get("quant_domain")
                    else None
                ),
                "admission": str(row.get("admission") or ""),
                "_tf": Counter(tokens),
            }
            rows.append(stored)
            document_frequency.update(set(tokens))
            if stored["source_kind"] == "formula-authority":
                formula_authority = json.loads(content)
            canonical_lines.append(_canonical_bytes(row) + b"\n")

        declared_count = int(state.get("candidate_count") or -1)
        receipt_count = int(source.get("frontier_candidate_count") or -1)
        if (
            len(rows) != declared_count
            or len(rows) != receipt_count
            or len(rows) < MIN_FRONTIER_CANDIDATES
        ):
            raise ValueError(
                "frontier candidate count mismatch "
                f"(state={declared_count}, receipt={receipt_count}, loaded={len(rows)})"
            )
        if observed_source_counts != expected_source_counts:
            raise ValueError("frontier per-source candidate counts mismatch")
        measured_set = _sha256_bytes(b"".join(canonical_lines))
        if state.get("candidate_set_sha256") != measured_set:
            raise ValueError("frontier state candidate-set digest mismatch")
        if source.get("frontier_candidate_set_sha256") != measured_set:
            raise ValueError("frontier receipt candidate-set digest mismatch")
        if not isinstance(formula_authority, dict):
            raise ValueError("frontier formula authority is unavailable")
        if int(formula_authority.get("locked_proven_count") or 0) != EXPECTED_LOCKED_PROVEN:
            raise ValueError("locked-proven formula count drifted")
        if (
            formula_authority.get("lambda_status")
            != "CONJECTURE_1_OPEN_ADVISORY_ONLY"
        ):
            raise ValueError("Lambda formula authority drifted")
        if (
            formula_authority.get("f_number_to_executable_registry_mapping")
            != "UNKNOWN_NOT_INFERRED"
        ):
            raise ValueError("unknown formula mapping was silently inferred")
        return rows, document_frequency, formula_authority

    @property
    def ready(self) -> bool:
        return (
            self._load_error is None
            and len(self._rows) == PUBLIC_CHUNK_COUNT
            and len(self._frontier_rows) >= MIN_FRONTIER_CANDIDATES
        )

    @property
    def source_revision(self) -> str | None:
        value = self._source.get("source_revision")
        return str(value) if _valid_revision(value) else None

    @property
    def frontier_candidate_set_sha256(self) -> str | None:
        value = self._frontier_state.get("candidate_set_sha256")
        return str(value) if _valid_digest(value) else None

    def health(self) -> dict[str, Any]:
        with self._lock:
            by_source: dict[str, int] = {}
            for row in self._rows:
                source = str(row.get("source") or "unknown")
                by_source[source] = by_source.get(source, 0) + 1
            return {
                "schema": SCHEMA_HEALTH,
                "service": "living-anatomy-yachay-second-brain-v7",
                "ready": self.ready,
                "state": (
                    "SOURCE_BOUND_RETRIEVAL_AND_FRONTIER"
                    if self.ready
                    else "UNAVAILABLE"
                ),
                "transport_state": "REACHABLE",
                "evidence_state": "MEASURED" if self.ready else "UNAVAILABLE",
                "verification_state": (
                    "STRUCTURAL_ONLY" if self.ready else "FAILED"
                ),
                "authority_state": "READ_ONLY",
                "kind": "SOFTWARE",
                "content_access": "HANDLES_ONLY",
                "source_repository": SOURCE_REPOSITORY,
                "source_revision": self.source_revision,
                "canonical_dataset": CANONICAL_DATASET,
                "chunk_count": len(self._rows),
                "declared_public_chunk_count": PUBLIC_CHUNK_COUNT,
                "by_source": by_source,
                "frontier": {
                    "ready": self.ready,
                    "state": self._frontier_state.get("state", "UNAVAILABLE"),
                    "candidate_count": len(self._frontier_rows),
                    "source_count": self._frontier_state.get("source_count", 0),
                    "candidate_set_sha256": self.frontier_candidate_set_sha256,
                    "public_content_access": "HANDLES_ONLY",
                    "internal_content_access": "READ_ONLY_PROCESS_INTERNAL",
                    "candidate_state": "DISCOVERED_REVIEW_REQUIRED",
                    "learning_definition": self._frontier_state.get(
                        "learning_definition"
                    ),
                },
                "formula_atlas": {
                    "attributed_formula_count": int(
                        self._frontier_state.get("source_kind_counts", {}).get(
                            "attributed-formula",
                            0,
                        )
                    ),
                    "executable_formula_count": int(
                        self._frontier_state.get("source_kind_counts", {}).get(
                            "executable-formula",
                            0,
                        )
                    ),
                    "locked_proven_count": self._formula_authority.get(
                        "locked_proven_count",
                        0,
                    ),
                    "locked_proven_ids": self._formula_authority.get(
                        "locked_proven_ids",
                        [],
                    ),
                    "mapping": self._formula_authority.get(
                        "f_number_to_executable_registry_mapping",
                        "UNKNOWN_NOT_INFERRED",
                    ),
                    "lambda_status": self._formula_authority.get(
                        "lambda_status",
                        "CONJECTURE_1_OPEN_ADVISORY_ONLY",
                    ),
                },
                "quant_domain_count": len(
                    self._frontier_state.get("quant_domain_counts", {})
                ),
                "snapshot_root": str(self.snapshot_root),
                "loaded_at": self._loaded_at,
                "load_error": self._load_error,
                "index_is_model_weights": False,
                "private_graph_nodes_loaded": 0,
                "private_graph_nodes_disclosed_elsewhere": (
                    PRIVATE_GRAPH_NODES_DISCLOSED
                ),
                "raw_graph_nodes_admitted_to_gradients": 0,
                "training_authority": "NONE",
                "promotion_authority": "NONE",
                "execution_authority": "NONE",
                "merge_authority": "NONE",
                "lambda_state": "CONJECTURE_1",
                "limits": [
                    "Lexical overlap is not correctness.",
                    "Public APIs return handles and digests, never corpus or candidate content.",
                    "Frontier candidates require separate human-governed review.",
                    "The owner's private graph is not bundled, queried, or exposed.",
                    "This read-only organ cannot train, promote, merge, authorize, or execute an action.",
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
            "retrieval": {
                "chunk_count": len(self._rows),
                "by_source": health["by_source"],
                "manifest": self._manifest,
            },
            "frontier": {
                "state": self._frontier_state,
                "candidate_count": len(self._frontier_rows),
                "candidate_set_sha256": self.frontier_candidate_set_sha256,
                "formula_atlas": health["formula_atlas"],
                "quant_domain_count": health["quant_domain_count"],
            },
            "interfaces": {
                "health": "/api/anatomy/v1/brain/health",
                "manifest": "/api/anatomy/v1/brain/manifest",
                "search": "/api/anatomy/v1/brain/search",
                "context": "/api/anatomy/v1/brain/context",
                "frontier": "/api/anatomy/v1/brain/frontier",
                "formulas": "/api/anatomy/v1/brain/formulas",
                "quant": "/api/anatomy/v1/brain/quant",
                "ouroboros": "/api/anatomy/v1/brain/ouroboros",
                "neural_quant_v7": "/api/anatomy/v1/brain/neural-quant-v7",
            },
            "authority_state": "READ_ONLY",
            "content_access": "HANDLES_ONLY",
            "training_authority": "NONE",
            "promotion_authority": "NONE",
            "execution_authority": "NONE",
            "merge_authority": "NONE",
            "limits": health["limits"],
        }

    @staticmethod
    def _retrieval_handle(row: dict[str, Any]) -> dict[str, Any]:
        return {
            "nodeId": row["id"],
            "nodeKind": "INDEX",
            "label": "DECLARED",
            "note": str(row.get("title") or "")[:160],
            "source": row.get("source"),
            "sourceId": row.get("sourceId"),
            "sha256": row.get("sha256"),
        }

    @staticmethod
    def _frontier_handle(row: dict[str, Any]) -> dict[str, Any]:
        handle: dict[str, Any] = {
            "nodeId": row["id"],
            "nodeKind": "FRONTIER_CANDIDATE",
            "label": "REVIEW_REQUIRED",
            "note": str(row.get("title") or "")[:180],
            "sourceRepository": row.get("source_repository"),
            "sourceRevision": row.get("source_revision"),
            "sourcePath": row.get("source_path"),
            "sourceKind": row.get("source_kind"),
            "sha256": row.get("sha256"),
            "admission": row.get("admission"),
            "candidateState": "DISCOVERED_REVIEW_REQUIRED",
            "contentAccess": "HANDLES_ONLY",
        }
        if row.get("quant_domain"):
            handle["quantDomain"] = row["quant_domain"]
        return handle

    @staticmethod
    def _score_rows(
        query: str,
        rows: list[dict[str, Any]],
        document_frequency: Counter[str],
        *,
        k: int,
    ) -> list[tuple[float, dict[str, Any]]]:
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []
        query_frequency = Counter(query_tokens)
        total = max(1, len(rows))
        scored: list[tuple[float, dict[str, Any]]] = []
        for row in rows:
            score = 0.0
            row_frequency: Counter[str] = row["_tf"]
            length = max(1, sum(row_frequency.values()))
            for term, query_count in query_frequency.items():
                term_frequency = row_frequency.get(term, 0)
                if not term_frequency:
                    continue
                inverse_document_frequency = math.log(
                    1.0
                    + (total - document_frequency.get(term, 0) + 0.5)
                    / (document_frequency.get(term, 0) + 0.5)
                )
                score += (
                    inverse_document_frequency
                    * ((term_frequency * 2.2) / (
                        term_frequency + 1.2 + 0.75 * length / 180.0
                    ))
                    * query_count
                )
            if score > 0:
                scored.append((score, row))
        scored.sort(key=lambda item: (-item[0], str(item[1]["id"])))
        return scored[:k]

    def search(self, query: str, k: int = 6) -> dict[str, Any]:
        query = str(query or "").strip()[:MAX_QUERY_CHARS]
        requested_k = _bounded_k(k, default=6)
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
            top = self._score_rows(
                query,
                self._rows,
                self._df,
                k=requested_k,
            )
            handles = [self._retrieval_handle(row) for _, row in top]
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

    def frontier_search(
        self,
        query: str,
        k: int = 12,
        *,
        source_kinds: set[str] | None = None,
        quant_domain: str | None = None,
        source_repository: str | None = None,
    ) -> dict[str, Any]:
        query = str(query or "").strip()[:MAX_QUERY_CHARS]
        requested_k = _bounded_k(k, default=12)
        with self._lock:
            if not self.ready:
                return {
                    "schema": SCHEMA_FRONTIER,
                    "ready": False,
                    "state": "UNAVAILABLE",
                    "query": query,
                    "handles": [],
                    "scores": [],
                    "source_revision": self.source_revision,
                    "error": self._load_error or "frontier snapshot unavailable",
                    "content_access": "HANDLES_ONLY",
                    "execution_authority": "NONE",
                }
            filtered = [
                row
                for row in self._frontier_rows
                if (
                    source_kinds is None
                    or row.get("source_kind") in source_kinds
                )
                and (
                    quant_domain is None
                    or row.get("quant_domain") == quant_domain
                )
                and (
                    source_repository is None
                    or row.get("source_repository") == source_repository
                )
            ]
            local_df: Counter[str] = Counter()
            for row in filtered:
                local_df.update(row["_tf"].keys())
            top = self._score_rows(
                query,
                filtered,
                local_df,
                k=requested_k,
            )
            handles = [self._frontier_handle(row) for _, row in top]
            scores = [round(score, 6) for score, _ in top]
            body = {
                "query": query,
                "handles": handles,
                "scores": scores,
                "candidate_count": len(self._frontier_rows),
                "filtered_candidate_count": len(filtered),
                "candidate_set_sha256": self.frontier_candidate_set_sha256,
                "source_revision": self.source_revision,
                "ranking": "LEXICAL_RELEVANCE_NOT_CORRECTNESS",
                "content_access": "HANDLES_ONLY",
            }
            return {
                "schema": SCHEMA_FRONTIER,
                "ready": True,
                "state": "REVIEW_REQUIRED",
                **body,
                "result_sha256": _canonical_sha256(body),
                "candidate_state": "DISCOVERED_REVIEW_REQUIRED",
                "training_authority": "NONE",
                "promotion_authority": "NONE",
                "execution_authority": "NONE",
                "merge_authority": "NONE",
            }

    def formula_view(self, query: str = "formula authority", k: int = 24) -> dict[str, Any]:
        kinds = {
            "formula-authority",
            "attributed-formula",
            "executable-formula",
        }
        search = self.frontier_search(
            query or "formula authority proof status",
            k=k,
            source_kinds=kinds,
        )
        return {
            "schema": SCHEMA_FORMULAS,
            "ready": search.get("ready", False),
            "state": search.get("state", "UNAVAILABLE"),
            "source_revision": self.source_revision,
            "candidate_set_sha256": self.frontier_candidate_set_sha256,
            "attributed_formula_count": EXPECTED_ATTRIBUTED_FORMULAS,
            "executable_formula_count": EXPECTED_EXECUTABLE_FORMULAS,
            "locked_proven_count": self._formula_authority.get(
                "locked_proven_count",
                0,
            ),
            "locked_proven_ids": self._formula_authority.get(
                "locked_proven_ids",
                [],
            ),
            "f_number_mapping": self._formula_authority.get(
                "f_number_to_executable_registry_mapping",
                "UNKNOWN_NOT_INFERRED",
            ),
            "lambda_status": self._formula_authority.get(
                "lambda_status",
                "CONJECTURE_1_OPEN_ADVISORY_ONLY",
            ),
            "handles": search.get("handles", []),
            "scores": search.get("scores", []),
            "content_access": "HANDLES_ONLY",
            "proof_boundary": (
                "Per-obligation status, source-reported status, and locked-proven "
                "membership are separate. No status string promotes a formula."
            ),
            "execution_authority": "NONE",
        }

    def quant_view(
        self,
        query: str = "quant math information geometry coding trust energy",
        k: int = 24,
    ) -> dict[str, Any]:
        search = self.frontier_search(
            query,
            k=k,
            source_kinds={
                "quant-domain",
                "attributed-formula",
                "executable-formula",
            },
        )
        domain_counts = self._frontier_state.get("quant_domain_counts", {})
        domains = [
            {
                "id": domain,
                "candidate_count": int(count),
                "authority": "REFERENCE_AND_CONSTRAINT_INPUT_ONLY",
            }
            for domain, count in sorted(domain_counts.items())
        ]
        return {
            "schema": SCHEMA_QUANT,
            "ready": search.get("ready", False),
            "state": search.get("state", "UNAVAILABLE"),
            "source_revision": self.source_revision,
            "candidate_set_sha256": self.frontier_candidate_set_sha256,
            "quant_domain_count": len(domains),
            "domains": domains,
            "handles": search.get("handles", []),
            "scores": search.get("scores", []),
            "content_access": "HANDLES_ONLY",
            "lambda_status": "CONJECTURE_1_OPEN_ADVISORY_ONLY",
            "execution_authority": "NONE",
        }

    def ouroboros_view(self, k: int = 16) -> dict[str, Any]:
        search = self.frontier_search(
            "ouroboros bounded loop convergence termination receipt closure codex",
            k=k,
            source_repository="szl-holdings/ouroboros",
        )
        source_receipt = next(
            (
                source
                for source in self._frontier_state.get("sources", [])
                if source.get("source_id") == "ouroboros_runtime"
            ),
            {},
        )
        return {
            "schema": SCHEMA_OUROBOROS,
            "ready": search.get("ready", False),
            "state": search.get("state", "UNAVAILABLE"),
            "source": source_receipt,
            "candidate_set_sha256": self.frontier_candidate_set_sha256,
            "handles": search.get("handles", []),
            "scores": search.get("scores", []),
            "loop_contract": {
                "bounded": True,
                "terminating": True,
                "receipt_closed": True,
                "codex_role": "ADVISORY_REVIEW_ONLY",
                "recommendations_executed": False,
            },
            "content_access": "HANDLES_ONLY",
            "training_authority": "NONE",
            "execution_authority": "NONE",
        }

    def neural_quant_view(self, k: int = 24) -> dict[str, Any]:
        health = self.health()
        formulas = self.formula_view(k=k)
        quant = self.quant_view(k=k)
        ouroboros = self.ouroboros_view(k=min(k, 16))
        core = {
            "source_revision": self.source_revision,
            "candidate_set_sha256": self.frontier_candidate_set_sha256,
            "brain": {
                "chunk_count": health["chunk_count"],
                "frontier_candidate_count": health["frontier"][
                    "candidate_count"
                ],
                "frontier_source_count": health["frontier"]["source_count"],
                "candidate_state": "DISCOVERED_REVIEW_REQUIRED",
            },
            "formulas": {
                "attributed": formulas["attributed_formula_count"],
                "executable": formulas["executable_formula_count"],
                "locked_proven": formulas["locked_proven_count"],
                "locked_proven_ids": formulas["locked_proven_ids"],
                "mapping": formulas["f_number_mapping"],
                "lambda_status": formulas["lambda_status"],
                "handles": formulas["handles"],
            },
            "quant": {
                "domain_count": quant["quant_domain_count"],
                "domains": quant["domains"],
                "handles": quant["handles"],
            },
            "ouroboros": {
                "source": ouroboros["source"],
                "loop_contract": ouroboros["loop_contract"],
                "handles": ouroboros["handles"],
            },
            "content_access": "HANDLES_ONLY",
            "authority": {
                "training": "NONE",
                "promotion": "NONE",
                "execution": "NONE",
                "merge": "NONE",
                "provider_mutation": "NONE",
            },
        }
        return {
            "schema": SCHEMA_NEURAL_QUANT,
            "version": "7.0.0",
            "ready": self.ready,
            "state": "MEASURED" if self.ready else "UNAVAILABLE",
            **core,
            "view_sha256": _canonical_sha256(core),
            "honesty": (
                "A read-only holographic observation of source-bound public memory, "
                "formula/quant constraints, and bounded loop metadata. It neither "
                "trains nor executes."
            ),
        }
