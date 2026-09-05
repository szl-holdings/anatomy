#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Materialize the public Second Brain projection for Living Anatomy.

The source repository remains authoritative. This operator resolves an exact Git
commit, downloads the public 575-chunk retrieval corpus plus the review-gated
frontier candidate set from that immutable revision, validates every row and
digest, then writes one source receipt beside the snapshot. It never reads or
exports the private Second Brain graph, trains weights, promotes candidates, or
grants action authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_REPOSITORY = "szl-holdings/szl-second-brain"
DEFAULT_REF = "main"
EXPECTED_PUBLIC_CHUNKS = 575
MIN_FRONTIER_CANDIDATES = 70
MIN_FRONTIER_SOURCES = 7
EXPECTED_ATTRIBUTED_FORMULAS = 30
EXPECTED_EXECUTABLE_FORMULAS = 21
EXPECTED_QUANT_DOMAINS = 9
EXPECTED_LOCKED_PROVEN = 8
MAX_MANIFEST_BYTES = 256 * 1024
MAX_CORPUS_BYTES = 4 * 1024 * 1024
MAX_FRONTIER_STATE_BYTES = 512 * 1024
MAX_FRONTIER_CANDIDATE_BYTES = 4 * 1024 * 1024
USER_AGENT = "szl-living-anatomy-second-brain-materializer/2.0"
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
FRONTIER_ID = re.compile(r"^frontier:[0-9a-f]{32}$")
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bhf_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)


class SnapshotError(RuntimeError):
    """A source-bound public snapshot violated its declared contract."""


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def request_bytes(url: str, *, token: str | None = None, limit: int) -> bytes:
    headers = {
        "Accept": "application/vnd.github+json, application/json, text/plain;q=0.9, */*;q=0.8",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            body = response.read(limit + 1)
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        raise SnapshotError(
            f"fetch failed for {url}: {type(exc).__name__}"
        ) from exc
    if len(body) > limit:
        raise SnapshotError(f"response exceeded {limit} bytes: {url}")
    return body


def resolve_revision(
    repository: str,
    ref: str,
    *,
    token: str | None = None,
    api_url: str = "https://api.github.com",
) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError(f"invalid GitHub repository: {repository!r}")
    encoded_ref = urllib.parse.quote(ref, safe="")
    url = f"{api_url.rstrip('/')}/repos/{repository}/commits/{encoded_ref}"
    try:
        raw = request_bytes(url, token=token, limit=MAX_MANIFEST_BYTES)
    except SnapshotError:
        # A repository-scoped Actions token can lack cross-repo read permission
        # even when the source repository is public. Retry the immutable public
        # read without credentials; never broaden token scope.
        if not token:
            raise
        raw = request_bytes(url, token=None, limit=MAX_MANIFEST_BYTES)
    payload = json.loads(raw)
    revision = (
        str(payload.get("sha") or "").lower()
        if isinstance(payload, dict)
        else ""
    )
    if not HEX_40.fullmatch(revision):
        raise SnapshotError("GitHub did not return an exact source revision")
    return revision


def validate_snapshot(
    manifest_raw: bytes,
    corpus_raw: bytes,
    *,
    expected_chunks: int = EXPECTED_PUBLIC_CHUNKS,
) -> dict[str, Any]:
    manifest = json.loads(manifest_raw.decode("utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be a JSON object")
    if str(manifest.get("secretScan") or "").upper() != "PASS":
        raise ValueError("public projection secretScan must be PASS")

    rows = 0
    by_source: dict[str, int] = {}
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
            raise ValueError(f"duplicate corpus id at line {line_number}: {node_id}")
        ids.add(node_id)
        text = str(row.get("text") or "")
        declared = str(row.get("sha256") or "")
        measured = sha256_bytes(text.encode("utf-8"))
        if declared and declared != measured:
            raise ValueError(f"row digest mismatch at line {line_number}: {node_id}")
        source = str(row.get("source") or "unknown")
        by_source[source] = by_source.get(source, 0) + 1
        rows += 1

    declared_count = int(manifest.get("publicChunkCount") or 0)
    if rows != declared_count or rows != expected_chunks:
        raise ValueError(
            "public chunk count mismatch: "
            f"loaded={rows}, manifest={declared_count}, expected={expected_chunks}"
        )
    declared_by_source = manifest.get("bySource")
    if isinstance(declared_by_source, dict):
        normalized = {
            str(key): int(value) for key, value in declared_by_source.items()
        }
        if normalized != by_source:
            raise ValueError(
                f"source histogram mismatch: loaded={by_source}, manifest={normalized}"
            )
    return {
        "public_chunk_count": rows,
        "by_source": by_source,
        "manifest_sha256": sha256_bytes(manifest_raw),
        "corpus_sha256": sha256_bytes(corpus_raw),
        "manifest_projection_sha256": manifest.get("projectionSha256"),
        "secret_scan": "PASS",
    }


def _reject_secret_like_material(value: str) -> None:
    for pattern in SECRET_PATTERNS:
        if pattern.search(value):
            raise ValueError("frontier candidate set contains secret-like material")


def validate_frontier_snapshot(
    state_raw: bytes,
    candidates_raw: bytes,
) -> dict[str, Any]:
    state = json.loads(state_raw.decode("utf-8"))
    if not isinstance(state, dict):
        raise ValueError("frontier state must be a JSON object")
    if state.get("schema") != "szl.second-brain.frontier-state/v1":
        raise ValueError("unsupported frontier state schema")
    expected = {
        "state": "REVIEW_REQUIRED",
        "public_content_access": "HANDLES_ONLY",
        "controller_content_access": "AUTHORIZED_CONTROLLER_ONLY",
        "training_authority": "NONE",
        "promotion_authority": "NONE",
        "execution_authority": "NONE",
        "merge_authority": "NONE",
        "lambda": "CONJECTURE_1",
    }
    for key, value in expected.items():
        if state.get(key) != value:
            raise ValueError(f"frontier authority drift: {key}")
    if int(state.get("private_graph_nodes_loaded") or 0) != 0:
        raise ValueError("private graph material entered the frontier snapshot")
    if int(state.get("raw_graph_nodes_admitted_to_gradients") or 0) != 0:
        raise ValueError("frontier snapshot admitted raw graph nodes to gradients")
    source_count = state.get("source_count")
    sources = state.get("sources")
    if type(source_count) is not int or source_count < MIN_FRONTIER_SOURCES:
        raise ValueError("frontier source inventory is incomplete")
    if not isinstance(sources, list) or len(sources) != source_count:
        raise ValueError("frontier source manifest count drifted")

    source_ids: set[str] = set()
    expected_source_counts: dict[tuple[str, str, str], int] = {}
    observed_source_counts: dict[tuple[str, str, str], int] = {}
    source_candidate_count = 0
    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            raise ValueError(f"invalid frontier source at index {index}")
        source_id = str(source.get("source_id") or "")
        repository = str(source.get("repository") or "")
        revision = str(source.get("revision") or "")
        digest = str(source.get("content_sha256") or "")
        parser = str(source.get("parser") or "")
        path = str(source.get("path") or "")
        candidate_count = source.get("candidate_count")
        if not source_id or source_id in source_ids:
            raise ValueError(f"frontier source identity failed at index {index}")
        if not re.fullmatch(
            r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository
        ):
            raise ValueError(f"frontier source repository failed at index {index}")
        if not HEX_40.fullmatch(revision) or not HEX_64.fullmatch(digest):
            raise ValueError(f"frontier source binding failed at index {index}")
        if (
            not isinstance(source.get("parser"), str)
            or not parser.strip()
            or not isinstance(source.get("path"), str)
            or not path.strip()
            or type(candidate_count) is not int
            or candidate_count < 1
        ):
            raise ValueError(f"frontier source metadata failed at index {index}")
        binding = (repository, revision, path)
        if binding in expected_source_counts:
            raise ValueError(f"duplicate frontier source binding at index {index}")
        expected_source_counts[binding] = candidate_count
        observed_source_counts[binding] = 0
        source_ids.add(source_id)
        source_candidate_count += candidate_count

    kind_counts = state.get("source_kind_counts")
    domain_counts = state.get("quant_domain_counts")
    if not isinstance(kind_counts, dict) or not isinstance(domain_counts, dict):
        raise ValueError("frontier formula and quant summaries are missing")
    if int(kind_counts.get("attributed-formula") or 0) != EXPECTED_ATTRIBUTED_FORMULAS:
        raise ValueError("attributed formula count drifted")
    if int(kind_counts.get("executable-formula") or 0) != EXPECTED_EXECUTABLE_FORMULAS:
        raise ValueError("executable formula count drifted")
    if int(kind_counts.get("quant-domain") or 0) != EXPECTED_QUANT_DOMAINS:
        raise ValueError("quant domain record count drifted")
    if len(domain_counts) != EXPECTED_QUANT_DOMAINS:
        raise ValueError("quant domain taxonomy drifted")

    decoded = candidates_raw.decode("utf-8")
    _reject_secret_like_material(decoded)
    rows = 0
    ids: set[str] = set()
    canonical_lines: list[bytes] = []
    formula_authority: dict[str, Any] | None = None
    for line_number, line in enumerate(decoded.splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        if (
            not isinstance(row, dict)
            or row.get("schema") != "szl.second-brain.frontier-candidate/v1"
        ):
            raise ValueError(f"invalid frontier candidate at line {line_number}")
        candidate_id = str(row.get("id") or "")
        if not FRONTIER_ID.fullmatch(candidate_id) or candidate_id in ids:
            raise ValueError(f"frontier candidate identity failed at line {line_number}")
        ids.add(candidate_id)
        revision = str(row.get("source_revision") or "")
        digest = str(row.get("content_sha256") or "")
        if not HEX_40.fullmatch(revision) or not HEX_64.fullmatch(digest):
            raise ValueError(f"frontier source binding failed at line {line_number}")
        binding = (
            str(row.get("source_repository") or ""),
            revision,
            str(row.get("source_path") or ""),
        )
        if binding not in expected_source_counts:
            raise ValueError(f"frontier source manifest binding failed at line {line_number}")
        observed_source_counts[binding] += 1
        content = str(row.get("content") or "")
        if sha256_bytes(content.encode("utf-8")) != digest:
            raise ValueError(f"frontier digest mismatch at line {line_number}")
        if row.get("candidate_state") != "DISCOVERED_REVIEW_REQUIRED":
            raise ValueError(f"frontier candidate was promoted at line {line_number}")
        if row.get("content_access") != "CONTROLLER_ONLY":
            raise ValueError(f"frontier content boundary drifted at line {line_number}")
        if row.get("source_kind") == "formula-authority":
            formula_authority = json.loads(content)
        canonical_lines.append(canonical_bytes(row) + b"\n")
        rows += 1

    declared_count = int(state.get("candidate_count") or -1)
    if rows != declared_count or rows < MIN_FRONTIER_CANDIDATES:
        raise ValueError(
            "frontier candidate count mismatch: "
            f"loaded={rows}, declared={declared_count}, minimum={MIN_FRONTIER_CANDIDATES}"
        )
    if source_candidate_count != declared_count:
        raise ValueError(
            "frontier source candidate total mismatch: "
            f"manifest={source_candidate_count}, declared={declared_count}"
        )
    if observed_source_counts != expected_source_counts:
        raise ValueError("frontier per-source candidate counts mismatch")
    measured_set = sha256_bytes(b"".join(canonical_lines))
    if state.get("candidate_set_sha256") != measured_set:
        raise ValueError("frontier candidate-set digest mismatch")
    if not HEX_64.fullmatch(str(state.get("state_sha256") or "")):
        raise ValueError("frontier state digest is malformed")
    if not isinstance(formula_authority, dict):
        raise ValueError("formula authority candidate is missing")
    if int(formula_authority.get("locked_proven_count") or 0) != EXPECTED_LOCKED_PROVEN:
        raise ValueError("locked-proven formula count drifted")
    if formula_authority.get("lambda_status") != "CONJECTURE_1_OPEN_ADVISORY_ONLY":
        raise ValueError("Lambda formula authority drifted")
    if formula_authority.get("f_number_to_executable_registry_mapping") != "UNKNOWN_NOT_INFERRED":
        raise ValueError("unknown formula mapping was silently inferred")

    return {
        "frontier_candidate_count": rows,
        "frontier_source_count": source_count,
        "frontier_state_sha256": sha256_bytes(state_raw),
        "frontier_candidates_sha256": sha256_bytes(candidates_raw),
        "frontier_candidate_set_sha256": measured_set,
        "formula_counts": {
            "attributed": EXPECTED_ATTRIBUTED_FORMULAS,
            "executable": EXPECTED_EXECUTABLE_FORMULAS,
            "locked_proven": EXPECTED_LOCKED_PROVEN,
        },
        "quant_domain_count": EXPECTED_QUANT_DOMAINS,
        "lambda_state": "CONJECTURE_1",
        "candidate_state": "DISCOVERED_REVIEW_REQUIRED",
    }


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent,
        prefix=f".{path.name}.",
        delete=False,
    ) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, path)


def materialize(
    output: Path,
    *,
    repository: str = DEFAULT_REPOSITORY,
    ref: str = DEFAULT_REF,
    token: str | None = None,
    api_url: str = "https://api.github.com",
    raw_url: str = "https://raw.githubusercontent.com",
) -> dict[str, Any]:
    revision = resolve_revision(repository, ref, token=token, api_url=api_url)
    immutable_base = f"{raw_url.rstrip('/')}/{repository}/{revision}/data"
    manifest_raw = request_bytes(
        f"{immutable_base}/manifest.json",
        limit=MAX_MANIFEST_BYTES,
    )
    corpus_raw = request_bytes(
        f"{immutable_base}/brain-corpus.public.jsonl",
        limit=MAX_CORPUS_BYTES,
    )
    frontier_state_raw = request_bytes(
        f"{immutable_base}/frontier-state.v1.json",
        limit=MAX_FRONTIER_STATE_BYTES,
    )
    frontier_candidates_raw = request_bytes(
        f"{immutable_base}/frontier-candidates.public.jsonl",
        limit=MAX_FRONTIER_CANDIDATE_BYTES,
    )
    retrieval = validate_snapshot(manifest_raw, corpus_raw)
    frontier = validate_frontier_snapshot(
        frontier_state_raw,
        frontier_candidates_raw,
    )
    receipt = {
        "schema": "szl.second-brain.snapshot/v1",
        "source_repository": repository,
        "source_ref": ref,
        "source_revision": revision,
        "source_relation": "github-exact-revision-public-projection-and-frontier",
        "canonical_dataset": "SZLHOLDINGS/szl-second-brain-inrepo",
        "manifest_path": "data/manifest.json",
        "corpus_path": "data/brain-corpus.public.jsonl",
        "frontier_state_path": "data/frontier-state.v1.json",
        "frontier_candidates_path": "data/frontier-candidates.public.jsonl",
        "manifest_sha256": retrieval["manifest_sha256"],
        "corpus_sha256": retrieval["corpus_sha256"],
        "manifest_projection_sha256": retrieval[
            "manifest_projection_sha256"
        ],
        "public_chunk_count": retrieval["public_chunk_count"],
        "by_source": retrieval["by_source"],
        "secret_scan": retrieval["secret_scan"],
        **frontier,
        "materialized_at": utc_now(),
        "authority_state": "READ_ONLY",
        "content_access": "HANDLES_ONLY",
        "frontier_content_access": "HANDLES_ONLY_PUBLIC_CONTROLLER_ONLY_INTERNAL",
        "private_graph_nodes_materialized": 0,
        "raw_graph_nodes_admitted_to_gradients": 0,
        "training_authority": "NONE",
        "promotion_authority": "NONE",
        "execution_authority": "NONE",
        "merge_authority": "NONE",
        "lambda_state": "CONJECTURE_1",
    }
    receipt["receipt_sha256"] = sha256_bytes(canonical_bytes(receipt))
    atomic_write(output / "manifest.json", manifest_raw)
    atomic_write(output / "brain-corpus.public.jsonl", corpus_raw)
    atomic_write(output / "frontier-state.v1.json", frontier_state_raw)
    atomic_write(
        output / "frontier-candidates.public.jsonl",
        frontier_candidates_raw,
    )
    atomic_write(
        output / "source.json",
        (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode("utf-8"),
    )
    return receipt


def token_from_environment() -> str | None:
    for key in ("GH_READ_TOKEN", "GH_ADMIN_TOKEN", "GITHUB_TOKEN"):
        value = os.environ.get(key)
        if value and value.strip():
            return value.strip()
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(".runtime/second-brain"),
    )
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    parser.add_argument("--ref", default=DEFAULT_REF)
    parser.add_argument(
        "--api-url",
        default=os.environ.get("GITHUB_API_URL", "https://api.github.com"),
    )
    parser.add_argument("--raw-url", default="https://raw.githubusercontent.com")
    args = parser.parse_args()
    receipt = materialize(
        args.output,
        repository=args.repository,
        ref=args.ref,
        token=token_from_environment(),
        api_url=args.api_url,
        raw_url=args.raw_url,
    )
    print(
        json.dumps(
            {
                "source_repository": receipt["source_repository"],
                "source_revision": receipt["source_revision"],
                "public_chunk_count": receipt["public_chunk_count"],
                "corpus_sha256": receipt["corpus_sha256"],
                "frontier_candidate_count": receipt[
                    "frontier_candidate_count"
                ],
                "frontier_candidate_set_sha256": receipt[
                    "frontier_candidate_set_sha256"
                ],
                "quant_domain_count": receipt["quant_domain_count"],
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
