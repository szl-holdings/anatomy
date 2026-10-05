# SPDX-License-Identifier: Apache-2.0
"""Fail-closed handles-only contract for the refinement observatory."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

STATE_SCHEMA = "szl.second-brain.refinement-memory/v1"
HANDLE_SCHEMA = "szl.second-brain.refinement-pattern-handle/v1"
SOURCE_SCHEMA = "szl.anatomy.refinement-source/v1"
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
ERROR_CODE = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
FORBIDDEN_KEYS = frozenset(
    {
        "chain_of_thought",
        "hidden_reasoning",
        "private_reasoning",
        "raw_prompt",
        "system_prompt",
        "raw_completion",
        "transcript",
        "credentials",
        "credential",
        "token",
        "secret",
        "private_graph",
        "content",
        "text",
    }
)


class RefinementProjectionError(ValueError):
    """The source-bound projection violated the public observatory contract."""


def canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise RefinementProjectionError("projection is not strict JSON") from exc


def sha256_hex(value: bytes | str) -> str:
    data = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(data).hexdigest()


def _scan(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key).strip().casefold() in FORBIDDEN_KEYS:
                raise RefinementProjectionError(
                    f"forbidden public field at {path}.{key}"
                )
            _scan(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan(item, f"{path}[{index}]")


def validate_projection(
    state: Mapping[str, Any], source: Mapping[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    state_payload = dict(state)
    source_payload = dict(source)
    _scan(state_payload)
    _scan(source_payload)
    if state_payload.get("schema") != STATE_SCHEMA:
        raise RefinementProjectionError("unsupported refinement state schema")
    state_digest = str(state_payload.get("state_sha256") or "")
    if not HEX_64.fullmatch(state_digest):
        raise RefinementProjectionError("state digest is missing")
    state_body = dict(state_payload)
    state_body.pop("state_sha256", None)
    if sha256_hex(canonical_bytes(state_body)) != state_digest:
        raise RefinementProjectionError("state digest mismatch")
    expected_state = {
        "ready": True,
        "content_access": "HANDLES_ONLY",
        "private_graph_present": False,
        "raw_reasoning_present": False,
        "training_authority": "NONE",
        "promotion_authority": "NONE",
        "execution_authority": "NONE",
        "merge_authority": "NONE",
    }
    for key, expected in expected_state.items():
        if state_payload.get(key) != expected:
            raise RefinementProjectionError(f"state boundary mismatch: {key}")
    handles = state_payload.get("handles")
    if not isinstance(handles, list):
        raise RefinementProjectionError("handles are missing")
    if state_payload.get("pattern_count") != len(handles):
        raise RefinementProjectionError("pattern count mismatch")
    seen: set[str] = set()
    for handle in handles:
        if not isinstance(handle, dict) or handle.get("schema") != HANDLE_SCHEMA:
            raise RefinementProjectionError("invalid pattern handle")
        handle_id = str(handle.get("id") or "")
        digest = str(handle.get("sha256") or "")
        pair = str(handle.get("model_pair_sha256") or "")
        code = str(handle.get("error_code") or "")
        if not handle_id.startswith("refinement:") or handle_id in seen:
            raise RefinementProjectionError("pattern handle identity is invalid")
        if not HEX_64.fullmatch(digest) or not HEX_64.fullmatch(pair):
            raise RefinementProjectionError("pattern handle digest is invalid")
        if not ERROR_CODE.fullmatch(code):
            raise RefinementProjectionError("pattern error code is invalid")
        for key in ("verified_repair_rate", "regression_rate", "mean_audit_confidence"):
            number = float(handle.get(key, -1.0))
            if not 0.0 <= number <= 1.0:
                raise RefinementProjectionError(f"pattern metric is invalid: {key}")
        seen.add(handle_id)

    if source_payload.get("schema") != SOURCE_SCHEMA:
        raise RefinementProjectionError("unsupported source receipt schema")
    receipt_digest = str(source_payload.get("receipt_sha256") or "")
    if not HEX_64.fullmatch(receipt_digest):
        raise RefinementProjectionError("source receipt digest is missing")
    source_body = dict(source_payload)
    source_body.pop("receipt_sha256", None)
    if sha256_hex(canonical_bytes(source_body)) != receipt_digest:
        raise RefinementProjectionError("source receipt digest mismatch")
    if source_payload.get("source_repository") != "szl-holdings/szl-second-brain":
        raise RefinementProjectionError("source repository drifted")
    if source_payload.get("source_path") != "data/refinement-patterns.public.json":
        raise RefinementProjectionError("source path drifted")
    if source_payload.get("state_sha256") != state_digest:
        raise RefinementProjectionError("source/state digest mismatch")
    available = source_payload.get("available")
    revision = source_payload.get("source_revision")
    if available is True:
        if not HEX_40.fullmatch(str(revision or "")):
            raise RefinementProjectionError("available source revision is not exact")
    elif available is False:
        if revision not in (None, "") and not HEX_40.fullmatch(str(revision)):
            raise RefinementProjectionError("unavailable source revision is invalid")
    else:
        raise RefinementProjectionError("source availability is invalid")
    for key in ("training_authority", "promotion_authority", "execution_authority"):
        if source_payload.get(key) != "NONE":
            raise RefinementProjectionError(f"source carries forbidden {key}")
    return state_payload, source_payload


def load_projection(
    state_path: str | Path, source_path: str | Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    state = json.loads(Path(state_path).read_text(encoding="utf-8"))
    source = json.loads(Path(source_path).read_text(encoding="utf-8"))
    if not isinstance(state, dict) or not isinstance(source, dict):
        raise RefinementProjectionError("projection files must contain objects")
    return validate_projection(state, source)


def filter_handles(
    state: Mapping[str, Any], *, error_code: str | None = None, limit: int = 50
) -> list[dict[str, Any]]:
    if not 1 <= int(limit) <= 200:
        raise RefinementProjectionError("limit must be in [1, 200]")
    normalized = None
    if error_code is not None and str(error_code).strip():
        normalized = str(error_code).strip().upper()
        if not ERROR_CODE.fullmatch(normalized):
            raise RefinementProjectionError("error_code filter is invalid")
    handles = state.get("handles")
    if not isinstance(handles, list):
        raise RefinementProjectionError("handles are missing")
    return [
        dict(handle)
        for handle in handles
        if normalized is None or handle.get("error_code") == normalized
    ][: int(limit)]
