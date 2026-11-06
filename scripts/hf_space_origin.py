#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Resolve the exact hf.space origin the Hub reports for a declared Space id.

The creator-profile Space id ``betterwithage/anatomy`` stays the declared
publication target. The Hub can serve that id from another ``hf.space`` label:
after a namespace transfer the Hub API 307-redirects the declared id, and the
declared ``<owner>-<space>.hf.space`` alias answers 404. Live readback therefore
follows the host the Hub reports for the declared id and refuses anything that
is not an exact ``https://<label>.hf.space`` origin, the rule
szl-holdings/a11oy#3239 applies in the creator-profile lifecycle guardian.

Standard library only, so the publisher, the refinement readback and the
Holographic v7 live witness share one validator.

Usage: ``python scripts/hf_space_origin.py <owner>/<space>`` prints the origin,
or exits 1 with a one-line reason on stderr.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
import urllib.request

HUB_API_HOST = "huggingface.co"
HUB_SPACES_PATH = "/api/spaces/"
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
# One DNS label: lowercase ASCII letters and digits joined by single hyphens.
SPACE_LABEL = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
SPACE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*")


def exact_space_host(value: object) -> str:
    """Return ``value`` as an exact ``https://<label>.hf.space`` origin, or raise."""
    host = str(value or "").strip().rstrip("/")
    if (
        not host.startswith("https://")
        or "@" in host
        or "\\" in host
        or "/" in host[8:]
        or "?" in host
        or "#" in host
    ):
        raise RuntimeError("Space host is not an exact https hf.space origin")
    label = host.removeprefix("https://").removesuffix(".hf.space")
    if (
        not host.endswith(".hf.space")
        or len(label) > 63
        or not SPACE_LABEL.fullmatch(label)
    ):
        raise RuntimeError("Space host is not an exact https hf.space origin")
    return host


def hub_reported_origin(space_id: str, timeout: float = 20) -> str:
    """Ask the Hub API which exact hf.space origin serves ``space_id`` now.

    urllib follows the Hub's 307 for a transferred id. A lookup that ends
    anywhere but ``https://huggingface.co/api/spaces/`` is refused.
    """
    if not SPACE_ID.fullmatch(space_id or "") or ".." in space_id:
        raise RuntimeError(f"not a Hub Space id: {space_id!r}")
    request = urllib.request.Request(
        f"https://{HUB_API_HOST}{HUB_SPACES_PATH}{space_id}",
        headers={
            "Accept": "application/json",
            "User-Agent": "szl-anatomy-space-origin/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        final = urllib.parse.urlsplit(response.geturl())
        if (
            final.scheme != "https"
            or final.netloc != HUB_API_HOST
            or not final.path.startswith(HUB_SPACES_PATH)
        ):
            raise RuntimeError(
                "Hub Space lookup was redirected off https://huggingface.co/api/spaces/"
            )
        raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise RuntimeError("Hub Space lookup exceeded its response byte budget")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise RuntimeError("Hub Space lookup did not return a JSON object")
    return exact_space_host(payload.get("host"))


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: hf_space_origin.py <owner>/<space>", file=sys.stderr)
        return 2
    try:
        origin = hub_reported_origin(args[0])
    except (OSError, ValueError, RuntimeError) as error:
        # OSError covers urllib's URLError/HTTPError and timeouts; ValueError
        # covers a non-JSON body. The caller records this line as its reason.
        print(f"hf_space_origin: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    print(origin)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
