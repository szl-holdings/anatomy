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

from hf_space_origin import hub_reported_origin

SPACE_ID = "betterwithage/anatomy"
# Declared creator-profile origin. main() reads back on the exact hf.space host
# the Hub reports for SPACE_ID instead, and prints both.
DECLARED_BASE = "https://betterwithage-anatomy.hf.space"


def get_json(base: str, path: str) -> dict[str, Any]:
    request = urllib.request.Request(
        base + path,
        headers={"Accept": "application/json", "User-Agent": "szl-refinement-readback/1.0"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise AssertionError("live endpoint did not return an object")
    return payload


def main() -> int:
    # Fails closed (raises) before any readback unless the Hub reports an exact
    # https://<label>.hf.space origin for the declared Space id.
    base = hub_reported_origin(SPACE_ID)
    if base != DECLARED_BASE:
        print(
            f"NOTE: Hub reports {SPACE_ID} on {base}; declared origin is "
            f"{DECLARED_BASE}. Reading back on the Hub-reported host.",
            flush=True,
        )
    local_source = json.loads(
        Path("lib/refinement_source.json").read_text(encoding="utf-8")
    )
    last: Exception | None = None
    for _ in range(30):
        try:
            status = get_json(base, "/api/anatomy/v1/refinement/status")
            patterns = get_json(base, "/api/anatomy/v1/refinement/patterns?limit=20")
            with urllib.request.urlopen(base + "/refinement-lab", timeout=20) as response:
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
                        "origin": base,
                        "declared_origin": DECLARED_BASE,
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
