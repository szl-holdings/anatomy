#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Materialize the review-gated Second Brain frontier snapshot for Anatomy v7.

The source repository remains authoritative. This operator resolves one exact
Second Brain commit, downloads only the public frontier state and candidate
JSONL from that immutable revision, validates every candidate and digest, and
writes an immutable source receipt beside the existing 575-chunk Brain snapshot.
It never fetches the private graph and grants no training or execution authority.
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
STATE_PATH = "data/frontier-state.v1.json"
CANDIDATES_PATH = "data/frontier-candidates.public.jsonl"
MAX_STATE_BYTES = 512 * 1024
MAX_CANDIDATE_BYTES = 4 * 1024 * 1024
MAX_CANDIDATES = 256
USER_AGENT = "szl-living-anatomy-frontier-materializer/1.0"
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{24,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bhf_[A-Za-z0-9]{30,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)


class FrontierMaterializationError(RuntimeError):
    """The source snapshot violated an exact or authority boundary."""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def reject_secret_like(value: str) -> None:
    for pattern in SECRET_PATTERNS:
        if pattern.search(value):
            raise FrontierMaterializationError(
                "secret-like material was rejected from the public frontier snapshot"
            )


def request_bytes(url: str, *, token: str | None = None, limit: int) -> bytes:
    headers = {
        "Accept": "application/vnd.github+json, application/json, text/plain;q=0.9, */*;q=0.8",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = response.read(limit + 1)
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        raise FrontierMaterializationError(
            f"bounded source fetch failed: {type(exc).__name__}"
        ) from exc
    if len(payload) > limit:
        raise FrontierMaterializationError(
            f"public frontier source exceeded {limit} bytes"
        )
    return payload


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
        raw = request_bytes(url, token=token, limit=MAX_STATE_BYTES)
    except FrontierMaterializationError:
        if not token:
            raise
        raw = request_bytes(url, token=None, limit=MAX_STATE_BYTES)
    payload = json.loads(raw)
    revision = str(payload.get("sha") or "").lower() if isinstance(payload, dict) else ""
    if not HEX_40.fullmatch(revision):
        raise FrontierMaterializationError(
            "GitHub did not return an exact Second Brain revision"
        )
    return revision


def validate_snapshot(
    state_raw: bytes,
    candidate_raw: bytes,
    *,
    expected_source_count: int = 6,
) -> dict[str, Any]:
    state = json.loads(state_raw.decode("utf-8"))
    if not isinstance(state, dict):
        raise FrontierMaterializationError("frontier state must be a JSON object")
    if state.get("schema") != "szl.second-brain.frontier-state/v1":
        raise FrontierMaterializationError("unsupported frontier state schema")
    if state.get("state") != "REVIEW_REQUIRED":
        raise FrontierMaterializationError(
            "frontier state must remain REVIEW_REQUIRED"
        )
    if state.get("public_content_access") != "HANDLES_ONLY":
        raise FrontierMaterializationError(
            "public frontier access must remain HANDLES_ONLY"
        )
    if state.get("controller_content_access") != "AUTHORIZED_CONTROLLER_ONLY":
        raise FrontierMaterializationError(
            "frontier controller access boundary drifted"
        )
    for field in (
        "training_authority",
        "promotion_authority",
        "execution_authority",
        "merge_authority",
    ):
        if state.get(field) != "NONE":
            raise FrontierMaterializationError(
                f"frontier state unexpectedly grants {field}"
            )
    if int(state.get("source_count") or -1) != expected_source_count:
        raise FrontierMaterializationError("frontier source count drifted")
    if state.get("lambda") != "CONJECTURE_1":
        raise FrontierMaterializationError("Lambda honesty boundary drifted")

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    canonical = bytearray()
    for line_number, line in enumerate(
        candidate_raw.decode("utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise FrontierMaterializationError(
                f"frontier candidate at line {line_number} is not an object"
            )
        if row.get("schema") != "szl.second-brain.frontier-candidate/v1":
            raise FrontierMaterializationError(
                f"frontier candidate schema mismatch at line {line_number}"
            )
        candidate_id = str(row.get("id") or "")
        revision = str(row.get("source_revision") or "")
        digest = str(row.get("content_sha256") or "")
        content = str(row.get("content") or "")
        if not candidate_id or candidate_id in seen:
            raise FrontierMaterializationError(
                f"frontier candidate ID is missing or duplicated at line {line_number}"
            )
        seen.add(candidate_id)
        if not HEX_40.fullmatch(revision):
            raise FrontierMaterializationError(
                f"frontier source revision is not exact at line {line_number}"
            )
        if not HEX_64.fullmatch(digest):
            raise FrontierMaterializationError(
                f"frontier content digest is malformed at line {line_number}"
            )
        if sha256_bytes(content.encode("utf-8")) != digest:
            raise FrontierMaterializationError(
                f"frontier content digest mismatch at line {line_number}"
            )
        if row.get("candidate_state") != "DISCOVERED_REVIEW_REQUIRED":
            raise FrontierMaterializationError(
                f"frontier candidate was promoted at line {line_number}"
            )
        if row.get("content_access") != "CONTROLLER_ONLY":
            raise FrontierMaterializationError(
                f"frontier content boundary drifted at line {line_number}"
            )
        reject_secret_like(content)
        rows.append(row)
        canonical.extend(canonical_bytes(row))
        canonical.extend(b"\n")
        if len(rows) > MAX_CANDIDATES:
            raise FrontierMaterializationError(
                "frontier candidate count exceeded the bounded maximum"
            )
    if not rows:
        raise FrontierMaterializationError("frontier candidate snapshot is empty")
    if int(state.get("candidate_count") or -1) != len(rows):
        raise FrontierMaterializationError("frontier candidate count mismatch")
    measured_set = sha256_bytes(bytes(canonical))
    if state.get("candidate_set_sha256") != measured_set:
        raise FrontierMaterializationError(
            "frontier candidate-set digest does not replay"
        )

    kinds: dict[str, int] = {}
    domains: dict[str, int] = {}
    for row in rows:
        kind = str(row.get("source_kind") or "unknown")
        kinds[kind] = kinds.get(kind, 0) + 1
        if row.get("quant_domain"):
            domain = str(row["quant_domain"])
            domains[domain] = domains.get(domain, 0) + 1
    return {
        "candidate_count": len(rows),
        "candidate_set_sha256": measured_set,
        "state_sha256": sha256_bytes(state_raw),
        "candidate_bytes_sha256": sha256_bytes(candidate_raw),
        "source_count": int(state["source_count"]),
        "source_kind_counts": dict(sorted(kinds.items())),
        "quant_domain_counts": dict(sorted(domains.items())),
        "training_authority": "NONE",
        "promotion_authority": "NONE",
        "execution_authority": "NONE",
        "merge_authority": "NONE",
        "private_graph_nodes_loaded": 0,
        "raw_graph_nodes_admitted_to_gradients": 0,
        "lambda": "CONJECTURE_1",
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


def validate_existing_brain_source(output: Path, revision: str) -> None:
    source_path = output / "source.json"
    if not source_path.is_file():
        return
    source = json.loads(source_path.read_text(encoding="utf-8"))
    if source.get("source_repository") != DEFAULT_REPOSITORY:
        raise FrontierMaterializationError(
            "existing Brain snapshot names an unexpected repository"
        )
    if source.get("source_revision") != revision:
        raise FrontierMaterializationError(
            "Brain corpus and frontier snapshot are not source-revision aligned"
        )
    if source.get("content_access") != "HANDLES_ONLY":
        raise FrontierMaterializationError(
            "existing Brain snapshot is not handles-only"
        )
    if int(source.get("private_graph_nodes_materialized") or 0) != 0:
        raise FrontierMaterializationError(
            "existing Brain snapshot materialized private graph nodes"
        )


def materialize(
    output: Path,
    *,
    repository: str = DEFAULT_REPOSITORY,
    ref: str = DEFAULT_REF,
    token: str | None = None,
    api_url: str = "https://api.github.com",
    raw_url: str = "https://raw.githubusercontent.com",
) -> dict[str, Any]:
    revision = resolve_revision(
        repository,
        ref,
        token=token,
        api_url=api_url,
    )
    immutable_base = f"{raw_url.rstrip('/')}/{repository}/{revision}/data"
    state_raw = request_bytes(
        f"{immutable_base}/frontier-state.v1.json",
        limit=MAX_STATE_BYTES,
    )
    candidate_raw = request_bytes(
        f"{immutable_base}/frontier-candidates.public.jsonl",
        limit=MAX_CANDIDATE_BYTES,
    )
    validation = validate_snapshot(state_raw, candidate_raw)
    validate_existing_brain_source(output, revision)
    receipt = {
        "schema": "szl.anatomy.frontier-snapshot/v1",
        "source_repository": repository,
        "source_ref": ref,
        "source_revision": revision,
        "state_path": STATE_PATH,
        "candidates_path": CANDIDATES_PATH,
        "source_relation": "github-exact-revision-review-candidate-snapshot",
        "materialized_at": utc_now(),
        "candidate_count": validation["candidate_count"],
        "candidate_set_sha256": validation["candidate_set_sha256"],
        "state_sha256": validation["state_sha256"],
        "candidate_bytes_sha256": validation["candidate_bytes_sha256"],
        "source_count": validation["source_count"],
        "source_kind_counts": validation["source_kind_counts"],
        "quant_domain_counts": validation["quant_domain_counts"],
        "candidate_state": "DISCOVERED_REVIEW_REQUIRED",
        "public_content_access": "HANDLES_ONLY",
        "runtime_content_access": "IN_PROCESS_FILTERED",
        "training_authority": "NONE",
        "promotion_authority": "NONE",
        "execution_authority": "NONE",
        "merge_authority": "NONE",
        "private_graph_nodes_materialized": 0,
        "raw_graph_nodes_admitted_to_gradients": 0,
        "lambda": "CONJECTURE_1",
    }
    atomic_write(output / STATE_PATH.rsplit("/", 1)[-1], state_raw)
    atomic_write(output / CANDIDATES_PATH.rsplit("/", 1)[-1], candidate_raw)
    atomic_write(
        output / "frontier-source.json",
        (json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode(
            "utf-8"
        ),
    )
    return receipt


def token_from_environment() -> str | None:
    for key in ("GH_READ_TOKEN", "GH_ADMIN_TOKEN", "GITHUB_TOKEN"):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(".runtime/second-brain"))
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
                "candidate_count": receipt["candidate_count"],
                "candidate_set_sha256": receipt["candidate_set_sha256"],
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
