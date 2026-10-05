#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Verify live readback of the source-bound refinement observatory."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

BASE = "https://betterwithage-anatomy.hf.space"


def get_json(path: str) -> dict[str, Any]:
    request = urllib.request.Request(
        BASE + path,
        headers={"Accept": "application/json", "User-Agent": "szl-refinement-readback/1.0"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise AssertionError("live endpoint did not return an object")
    return payload


def main() -> int:
    local_source = json.loads(
        Path("lib/refinement_source.json").read_text(encoding="utf-8")
    )
    last: Exception | None = None
    for _ in range(30):
        try:
            status = get_json("/api/anatomy/v1/refinement/status")
            patterns = get_json("/api/anatomy/v1/refinement/patterns?limit=20")
            with urllib.request.urlopen(BASE + "/refinement-lab", timeout=20) as response:
                html = response.read(2 * 1024 * 1024).decode("utf-8")
            assert status["content_access"] == "HANDLES_ONLY"
            assert status["authority"] == "READ_ONLY"
            assert status["state_sha256"] == local_source["state_sha256"]
            assert status["source_revision"] == local_source["source_revision"]
            assert patterns["content_access"] == "HANDLES_ONLY"
            encoded = json.dumps(patterns, sort_keys=True).lower()
            for forbidden in ('"content"', '"text"', "chain_of_thought", "raw_prompt"):
                assert forbidden not in encoded
            assert "Alloy Refinement Observatory" in html
            print(
                json.dumps(
                    {
                        "live": True,
                        "source_revision": status["source_revision"],
                        "state_sha256": status["state_sha256"],
                        "pattern_count": status["pattern_count"],
                    },
                    sort_keys=True,
                )
            )
            return 0
        except (AssertionError, KeyError, OSError, urllib.error.URLError) as exc:
            last = exc
            time.sleep(10)
    raise SystemExit(f"refinement observatory readback failed: {type(last).__name__}: {last}")


if __name__ == "__main__":
    raise SystemExit(main())
