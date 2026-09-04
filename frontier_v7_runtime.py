# SPDX-License-Identifier: Apache-2.0
"""Read-only Living Anatomy v7 adapter for Second Brain frontier memory.

The adapter consumes an exact, pre-materialized Second Brain snapshot. It exposes
only handles, source revisions, classifications, quant domains, and digests. The
candidate content stays inside the process and is never returned by these routes.
The adapter has no write, training, promotion, merge, tool, or provider authority.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import threading
from collections import Counter
from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI, Query
from fastapi.responses import JSONResponse

ROOT = Path(__file__).resolve().parent
DEFAULT_SNAPSHOT = ROOT / ".runtime" / "second-brain"
STATE_FILE = "frontier-state.v1.json"
CANDIDATE_FILE = "frontier-candidates.public.jsonl"
MAX_CANDIDATES = 256
MAX_SNAPSHOT_BYTES = 4 * 1024 * 1024
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_.:/+-]{1,63}")

FORMULA_KINDS = frozenset(
    {
        "formula-authority",
        "attributed-formula",
        "executable-formula",
        "quant-domain",
    }
)


class FrontierV7Error(RuntimeError):
    """Snapshot or query violated the Living Anatomy v7 boundary."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def snapshot_path() -> Path:
    configured = os.environ.get("SZL_SECOND_BRAIN_SNAPSHOT", "").strip()
    return Path(configured) if configured else DEFAULT_SNAPSHOT


def _bounded_read(path: Path, limit: int) -> bytes:
    stat = path.stat()
    if stat.st_size > limit:
        raise FrontierV7Error(f"snapshot file exceeds {limit} bytes")
    return path.read_bytes()


def _tokens(value: str) -> list[str]:
    return TOKEN_RE.findall(value.lower())


class FrontierV7Snapshot:
    """Thread-safe immutable snapshot cache keyed by file size and mtime."""

    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory or snapshot_path()
        self._lock = threading.Lock()
        self._fingerprint: tuple[int, int, int, int] | None = None
        self._state: dict[str, Any] | None = None
        self._rows: tuple[dict[str, Any], ...] = ()
        self._error: str | None = None

    def _current_fingerprint(self) -> tuple[int, int, int, int]:
        state = (self.directory / STATE_FILE).stat()
        candidates = (self.directory / CANDIDATE_FILE).stat()
        return (
            state.st_mtime_ns,
            state.st_size,
            candidates.st_mtime_ns,
            candidates.st_size,
        )

    def _load(self) -> None:
        try:
            fingerprint = self._current_fingerprint()
        except OSError as exc:
            with self._lock:
                self._state = None
                self._rows = ()
                self._error = type(exc).__name__
                self._fingerprint = None
            return
        if fingerprint == self._fingerprint and self._state is not None:
            return
        with self._lock:
            if fingerprint == self._fingerprint and self._state is not None:
                return
            try:
                state_raw = _bounded_read(
                    self.directory / STATE_FILE,
                    512 * 1024,
                )
                candidate_raw = _bounded_read(
                    self.directory / CANDIDATE_FILE,
                    MAX_SNAPSHOT_BYTES,
                )
                state = json.loads(state_raw)
                rows = tuple(
                    json.loads(line)
                    for line in candidate_raw.decode("utf-8").splitlines()
                    if line.strip()
                )
                self._validate(state, rows)
                self._state = state
                self._rows = rows
                self._error = None
                self._fingerprint = fingerprint
            except Exception as exc:
                self._state = None
                self._rows = ()
                self._error = type(exc).__name__
                self._fingerprint = fingerprint

    @staticmethod
    def _validate(state: Any, rows: tuple[dict[str, Any], ...]) -> None:
        if not isinstance(state, dict):
            raise FrontierV7Error("frontier state must be an object")
        if state.get("schema") != "szl.second-brain.frontier-state/v1":
            raise FrontierV7Error("unsupported frontier state schema")
        if state.get("state") != "REVIEW_REQUIRED":
            raise FrontierV7Error("frontier candidates must remain review-required")
        for field in (
            "training_authority",
            "promotion_authority",
            "execution_authority",
            "merge_authority",
        ):
            if state.get(field) != "NONE":
                raise FrontierV7Error(f"frontier state grants {field}")
        if state.get("public_content_access") != "HANDLES_ONLY":
            raise FrontierV7Error("frontier public access is not handles-only")
        if int(state.get("candidate_count") or -1) != len(rows):
            raise FrontierV7Error("frontier candidate count does not match")
        if not rows or len(rows) > MAX_CANDIDATES:
            raise FrontierV7Error("frontier candidate count is outside bounds")

        seen: set[str] = set()
        canonical = bytearray()
        for row in rows:
            if not isinstance(row, dict):
                raise FrontierV7Error("frontier candidate must be an object")
            if row.get("schema") != "szl.second-brain.frontier-candidate/v1":
                raise FrontierV7Error("unsupported frontier candidate schema")
            candidate_id = str(row.get("id") or "")
            revision = str(row.get("source_revision") or "")
            digest = str(row.get("content_sha256") or "")
            content = str(row.get("content") or "")
            if not candidate_id or candidate_id in seen:
                raise FrontierV7Error("frontier candidate IDs are missing or duplicated")
            seen.add(candidate_id)
            if not HEX_40.fullmatch(revision):
                raise FrontierV7Error("frontier source revision is not exact")
            if not HEX_64.fullmatch(digest):
                raise FrontierV7Error("frontier content digest is malformed")
            if sha256_bytes(content.encode("utf-8")) != digest:
                raise FrontierV7Error("frontier content digest does not replay")
            if row.get("candidate_state") != "DISCOVERED_REVIEW_REQUIRED":
                raise FrontierV7Error("frontier candidate was promoted")
            if row.get("content_access") != "CONTROLLER_ONLY":
                raise FrontierV7Error("frontier candidate content boundary drifted")
            canonical.extend(canonical_bytes(row))
            canonical.extend(b"\n")
        measured = sha256_bytes(bytes(canonical))
        if state.get("candidate_set_sha256") != measured:
            raise FrontierV7Error("frontier candidate-set digest does not replay")

    @property
    def ready(self) -> bool:
        self._load()
        return self._state is not None and bool(self._rows) and self._error is None

    def status(self) -> dict[str, Any]:
        self._load()
        if not self.ready:
            return {
                "schema": "szl.anatomy.frontier-health/v1",
                "state": "UNAVAILABLE",
                "ready": False,
                "reason": self._error or "SNAPSHOT_NOT_READY",
                "content_access": "HANDLES_ONLY",
                "training_authority": "NONE",
                "promotion_authority": "NONE",
                "execution_authority": "NONE",
                "private_graph_nodes_loaded": 0,
                "raw_graph_nodes_admitted_to_gradients": 0,
                "lambda": "CONJECTURE_1",
            }
        assert self._state is not None
        kind_counts = Counter(str(row.get("source_kind") or "unknown") for row in self._rows)
        domains = Counter(
            str(row["quant_domain"])
            for row in self._rows
            if row.get("quant_domain")
        )
        return {
            "schema": "szl.anatomy.frontier-health/v1",
            "state": "REVIEW_REQUIRED",
            "ready": True,
            "source_repository": "szl-holdings/szl-second-brain",
            "source_revision": self._common_source_revision(),
            "candidate_count": len(self._rows),
            "candidate_set_sha256": self._state["candidate_set_sha256"],
            "source_count": self._state.get("source_count"),
            "source_kind_counts": dict(sorted(kind_counts.items())),
            "quant_domain_counts": dict(sorted(domains.items())),
            "content_access": "HANDLES_ONLY",
            "training_authority": "NONE",
            "promotion_authority": "NONE",
            "execution_authority": "NONE",
            "merge_authority": "NONE",
            "private_graph_nodes_loaded": 0,
            "raw_graph_nodes_admitted_to_gradients": 0,
            "lambda": "CONJECTURE_1",
        }

    def _common_source_revision(self) -> str | None:
        if self._state is None:
            return None
        revisions = {
            str(source.get("revision"))
            for source in self._state.get("sources", [])
            if isinstance(source, dict)
            and source.get("source_id") == "living_anatomy"
        }
        return next(iter(revisions)) if len(revisions) == 1 else None

    @staticmethod
    def _handle(row: dict[str, Any]) -> dict[str, Any]:
        handle: dict[str, Any] = {
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
        }
        if row.get("quant_domain"):
            handle["quantDomain"] = row["quant_domain"]
        return handle

    def query(
        self,
        *,
        query: str = "",
        kinds: set[str] | None = None,
        repositories: set[str] | None = None,
        require_quant_domain: bool = False,
        limit: int = 24,
    ) -> dict[str, Any]:
        self._load()
        status = self.status()
        if not self.ready:
            return {
                **status,
                "schema": "szl.anatomy.frontier-handles/v1",
                "handles": [],
                "scores": [],
            }
        tokens = _tokens(query)
        selected: list[tuple[float, dict[str, Any]]] = []
        for row in self._rows:
            kind = str(row.get("source_kind") or "")
            repository = str(row.get("source_repository") or "")
            if kinds is not None and kind not in kinds:
                continue
            if repositories is not None and repository not in repositories:
                continue
            if require_quant_domain and not row.get("quant_domain"):
                continue
            haystack = " ".join(
                (
                    str(row.get("title") or ""),
                    repository,
                    str(row.get("source_path") or ""),
                    kind,
                    str(row.get("quant_domain") or ""),
                    str(row.get("content") or ""),
                )
            ).lower()
            if tokens:
                hits = sum(haystack.count(token) for token in tokens)
                if hits <= 0:
                    continue
                score = round(math.log1p(hits), 8)
            else:
                score = 1.0
            selected.append((score, row))
        selected.sort(key=lambda item: (-item[0], str(item[1]["id"])))
        bounded = selected[: max(1, min(int(limit), 48))]
        handles = [self._handle(row) for _score, row in bounded]
        return {
            "schema": "szl.anatomy.frontier-handles/v1",
            "state": "REVIEW_REQUIRED",
            "ready": True,
            "source_repository": "szl-holdings/szl-second-brain",
            "candidate_set_sha256": status["candidate_set_sha256"],
            "content_access": "HANDLES_ONLY",
            "handles": handles,
            "scores": [score for score, _row in bounded],
            "result_set_sha256": sha256_bytes(canonical_bytes(handles)),
            "ranking": "LEXICAL_RELEVANCE_NOT_CORRECTNESS",
            "training_authority": "NONE",
            "promotion_authority": "NONE",
            "execution_authority": "NONE",
            "private_graph_nodes_loaded": 0,
        }


_SNAPSHOT: FrontierV7Snapshot | None = None
_SNAPSHOT_LOCK = threading.Lock()


def get_snapshot() -> FrontierV7Snapshot:
    global _SNAPSHOT
    if _SNAPSHOT is None:
        with _SNAPSHOT_LOCK:
            if _SNAPSHOT is None:
                _SNAPSHOT = FrontierV7Snapshot()
    return _SNAPSHOT


def create_frontier_v7_router(snapshot: FrontierV7Snapshot | None = None) -> APIRouter:
    source = snapshot or get_snapshot()
    router = APIRouter(tags=["Living Anatomy v7", "Second Brain"])

    @router.get("/api/anatomy/v1/frontier-health")
    def frontier_health() -> JSONResponse:
        return JSONResponse(source.status())

    @router.get("/api/anatomy/v1/brain/frontier")
    def frontier(
        q: str = Query("", max_length=512),
        limit: int = Query(24, ge=1, le=48),
    ) -> JSONResponse:
        return JSONResponse(source.query(query=q, limit=limit))

    @router.get("/api/anatomy/v1/brain/formulas")
    def formulas(
        q: str = Query("", max_length=512),
        limit: int = Query(48, ge=1, le=48),
    ) -> JSONResponse:
        payload = source.query(query=q, kinds=set(FORMULA_KINDS), limit=limit)
        payload["schema"] = "szl.anatomy.formula-handles/v1"
        payload["locked_proven_count"] = 8
        payload["locked_proven_ids"] = [
            "F1",
            "F4",
            "F7",
            "F11",
            "F12",
            "F18",
            "F19",
            "F22",
        ]
        payload["f_number_mapping"] = "UNKNOWN_NOT_INFERRED"
        payload["lambda"] = "CONJECTURE_1"
        return JSONResponse(payload)

    @router.get("/api/anatomy/v1/brain/quant")
    def quant(
        q: str = Query("", max_length=512),
        limit: int = Query(48, ge=1, le=48),
    ) -> JSONResponse:
        payload = source.query(
            query=q,
            require_quant_domain=True,
            limit=limit,
        )
        payload["schema"] = "szl.anatomy.quant-handles/v1"
        return JSONResponse(payload)

    @router.get("/api/anatomy/v1/brain/ouroboros")
    def ouroboros(
        q: str = Query("", max_length=512),
        limit: int = Query(24, ge=1, le=48),
    ) -> JSONResponse:
        payload = source.query(
            query=q,
            repositories={
                "szl-holdings/ouroboros",
                "szl-holdings/szl-ouroboros",
            },
            limit=limit,
        )
        payload["schema"] = "szl.anatomy.ouroboros-handles/v1"
        payload["loop_authority"] = "OBSERVE_AND_PROPOSE_ONLY"
        return JSONResponse(payload)

    return router


def install_frontier_v7_routes(
    app: FastAPI,
    *,
    snapshot: FrontierV7Snapshot | None = None,
) -> None:
    """Install routes exactly once on an existing Living Anatomy application."""

    marker = "_szl_frontier_v7_installed"
    if getattr(app.state, marker, False):
        return
    app.include_router(create_frontier_v7_router(snapshot))
    setattr(app.state, marker, True)
