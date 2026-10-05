#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Materialize the exact Second Brain refinement-memory public projection."""
from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT))
from lib.refinement_contract import (  # noqa: E402
    SOURCE_SCHEMA,
    canonical_bytes,
    sha256_hex,
    validate_projection,
)

REPOSITORY = "szl-holdings/szl-second-brain"
SOURCE_PATH = "data/refinement-patterns.public.json"
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
MAX_BYTES = 2 * 1024 * 1024
USER_AGENT = "szl-anatomy-refinement-materializer/1.0"


def _request(url: str, *, token: str | None = None) -> bytes:
    headers = {
        "Accept": "application/vnd.github+json, application/json, text/plain",
        "User-Agent": USER_AGENT,
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=45) as response:
        body = response.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError("source projection exceeds bounded size")
    return body


def resolve_revision(repository: str, ref: str, token: str | None) -> str:
    encoded = urllib.parse.quote(ref, safe="")
    url = f"https://api.github.com/repos/{repository}/commits/{encoded}"
    try:
        raw = _request(url, token=token)
    except urllib.error.HTTPError:
        if not token:
            raise
        raw = _request(url, token=None)
    payload = json.loads(raw)
    revision = str(payload.get("sha") or "").lower()
    if not HEX_40.fullmatch(revision):
        raise ValueError("source revision is not exact")
    return revision


def empty_state() -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema": "szl.second-brain.refinement-memory/v1",
        "state": "EMPTY_REVIEW_REQUIRED",
        "ready": True,
        "receipt_count": 0,
        "pattern_count": 0,
        "handles": [],
        "content_access": "HANDLES_ONLY",
        "private_graph_present": False,
        "raw_reasoning_present": False,
        "training_authority": "NONE",
        "promotion_authority": "NONE",
        "execution_authority": "NONE",
        "merge_authority": "NONE",
    }
    body["state_sha256"] = sha256_hex(canonical_bytes(body))
    return body


def source_receipt(
    state: dict[str, Any], *, revision: str | None, available: bool
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "schema": SOURCE_SCHEMA,
        "source_repository": REPOSITORY,
        "source_revision": revision,
        "source_path": SOURCE_PATH,
        "available": available,
        "state_sha256": state["state_sha256"],
        "source_content_sha256": sha256_hex(canonical_bytes(state)),
        "content_access": "HANDLES_ONLY",
        "training_authority": "NONE",
        "promotion_authority": "NONE",
        "execution_authority": "NONE",
    }
    body["receipt_sha256"] = sha256_hex(canonical_bytes(body))
    return body


def atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, delete=False
    ) as handle:
        handle.write(encoded)
        temporary = Path(handle.name)
    temporary.replace(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", default=REPOSITORY)
    parser.add_argument("--ref", default="main")
    parser.add_argument(
        "--state-output", default="lib/refinement_patterns.public.json"
    )
    parser.add_argument("--source-output", default="lib/refinement_source.json")
    parser.add_argument("--allow-unavailable", action="store_true")
    args = parser.parse_args()
    if args.repository != REPOSITORY:
        raise SystemExit("refinement source repository is fixed")
    token = os.environ.get("GITHUB_TOKEN") or None
    revision = resolve_revision(args.repository, args.ref, token)
    raw_url = (
        f"https://raw.githubusercontent.com/{args.repository}/{revision}/{SOURCE_PATH}"
    )
    available = True
    try:
        raw = _request(raw_url, token=None)
        state = json.loads(raw)
        if not isinstance(state, dict):
            raise ValueError("source projection must be an object")
    except urllib.error.HTTPError as exc:
        if exc.code != 404 or not args.allow_unavailable:
            raise
        state = empty_state()
        available = False
    source = source_receipt(state, revision=revision, available=available)
    validate_projection(state, source)
    atomic_write(Path(args.state_output), state)
    atomic_write(Path(args.source_output), source)
    print(
        json.dumps(
            {
                "source_revision": revision,
                "available": available,
                "state_sha256": state["state_sha256"],
                "pattern_count": state["pattern_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
