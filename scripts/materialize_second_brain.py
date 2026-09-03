#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Materialize the public Second Brain projection for Living Anatomy.

The source repository remains authoritative. This operator resolves an exact
Git commit, downloads the public manifest and JSONL corpus from that immutable
revision, validates every row digest and the declared chunk count, then writes a
source receipt beside the snapshot. It never reads or exports the private
Second Brain graph.
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
MAX_MANIFEST_BYTES = 256 * 1024
MAX_CORPUS_BYTES = 4 * 1024 * 1024
USER_AGENT = "szl-living-anatomy-second-brain-materializer/1.0"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


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
        raise RuntimeError(f"fetch failed for {url}: {type(exc).__name__}: {exc}") from exc
    if len(body) > limit:
        raise RuntimeError(f"response exceeded {limit} bytes: {url}")
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
    except RuntimeError:
        # A repository-scoped Actions token can lack cross-repo read permission
        # even when the source repository is public. Retry the immutable public
        # read without credentials; never broaden token scope.
        if not token:
            raise
        raw = request_bytes(url, token=None, limit=MAX_MANIFEST_BYTES)
    payload = json.loads(raw)
    revision = str(payload.get("sha") or "").lower() if isinstance(payload, dict) else ""
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise RuntimeError("GitHub did not return an exact source revision")
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
    for line_number, line in enumerate(corpus_raw.decode("utf-8").splitlines(), start=1):
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
            f"public chunk count mismatch: loaded={rows}, manifest={declared_count}, expected={expected_chunks}"
        )
    declared_by_source = manifest.get("bySource")
    if isinstance(declared_by_source, dict):
        normalized = {str(key): int(value) for key, value in declared_by_source.items()}
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
    validation = validate_snapshot(manifest_raw, corpus_raw)
    receipt = {
        "schema": "szl.second-brain.snapshot/v1",
        "source_repository": repository,
        "source_ref": ref,
        "source_revision": revision,
        "source_relation": "github-exact-revision-public-projection",
        "canonical_dataset": "SZLHOLDINGS/szl-second-brain-inrepo",
        "manifest_path": "data/manifest.json",
        "corpus_path": "data/brain-corpus.public.jsonl",
        "manifest_sha256": validation["manifest_sha256"],
        "corpus_sha256": validation["corpus_sha256"],
        "manifest_projection_sha256": validation["manifest_projection_sha256"],
        "public_chunk_count": validation["public_chunk_count"],
        "by_source": validation["by_source"],
        "secret_scan": validation["secret_scan"],
        "materialized_at": utc_now(),
        "authority_state": "READ_ONLY",
        "content_access": "HANDLES_ONLY",
        "private_graph_nodes_materialized": 0,
        "raw_graph_nodes_admitted_to_gradients": 0,
        "lambda_state": "CONJECTURE_1",
    }
    atomic_write(output / "manifest.json", manifest_raw)
    atomic_write(output / "brain-corpus.public.jsonl", corpus_raw)
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
    parser.add_argument("--output", type=Path, default=Path(".runtime/second-brain"))
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    parser.add_argument("--ref", default=DEFAULT_REF)
    parser.add_argument("--api-url", default=os.environ.get("GITHUB_API_URL", "https://api.github.com"))
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
                "output": str(args.output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
