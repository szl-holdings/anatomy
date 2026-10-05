# SPDX-License-Identifier: Apache-2.0
"""Read-only Alloy Refinement observatory layered onto Living Anatomy."""
from __future__ import annotations

import functools
import json
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import server as anatomy_server  # noqa: E402
from lib.refinement_contract import (  # noqa: E402
    RefinementProjectionError,
    filter_handles,
    load_projection,
)
from living_runtime import LivingAnatomyHandler  # noqa: E402

STATE_PATH = ROOT / "lib" / "refinement_patterns.public.json"
SOURCE_PATH = ROOT / "lib" / "refinement_source.json"

anatomy_server.ARTIFACT_PATHS = tuple(
    dict.fromkeys(
        (
            *anatomy_server.ARTIFACT_PATHS,
            "lib/refinement_contract.py",
            "lib/refinement_living_runtime.py",
            "lib/refinement_patterns.public.json",
            "lib/refinement_source.json",
            "refinement-lab.html",
            "refinement-lab.js",
            "refinement-lab.css",
        )
    )
)


def projection_status() -> dict[str, Any]:
    try:
        state, source = load_projection(STATE_PATH, SOURCE_PATH)
    except (OSError, ValueError, RefinementProjectionError) as exc:
        return {
            "schema": "szl.anatomy.refinement-status/v1",
            "state": "UNAVAILABLE",
            "ready": False,
            "reason": type(exc).__name__,
            "handles": [],
            "content_access": "HANDLES_ONLY",
            "authority": "READ_ONLY",
            "training_authority": "NONE",
            "promotion_authority": "NONE",
            "execution_authority": "NONE",
        }
    source_available = bool(source["available"])
    return {
        "schema": "szl.anatomy.refinement-status/v1",
        "state": state["state"] if source_available else "UNAVAILABLE_SOURCE_NOT_ADMITTED",
        "ready": source_available,
        "source_repository": source["source_repository"],
        "source_revision": source.get("source_revision"),
        "source_path": source["source_path"],
        "source_available": source_available,
        "state_sha256": state["state_sha256"],
        "receipt_count": state["receipt_count"],
        "pattern_count": state["pattern_count"],
        "content_access": "HANDLES_ONLY",
        "private_graph_present": False,
        "raw_reasoning_present": False,
        "authority": "READ_ONLY",
        "training_authority": "NONE",
        "promotion_authority": "NONE",
        "execution_authority": "NONE",
        "honesty": (
            "Repair-pattern rates are diagnostic observations, not proof that a "
            "future answer is correct and not authority to run a model or action."
        ),
    }


def pattern_payload(error_code: str | None, limit: int) -> dict[str, Any]:
    status = projection_status()
    if not status["ready"]:
        return {**status, "handles": [], "returned_count": 0}
    state, _ = load_projection(STATE_PATH, SOURCE_PATH)
    handles = filter_handles(state, error_code=error_code, limit=limit)
    return {
        **status,
        "schema": "szl.anatomy.refinement-patterns/v1",
        "handles": handles,
        "returned_count": len(handles),
    }


class RefinementLivingAnatomyHandler(LivingAnatomyHandler):
    """Add read-only refinement APIs without adding provider or write authority."""

    @staticmethod
    def _bounded_limit(value: Any) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            parsed = 50
        return max(1, min(parsed, 200))

    def _send_refinement(self, payload: dict[str, Any]) -> None:
        ready = bool(payload.get("ready"))
        self._send_json(
            payload,
            status=200 if ready else 503,
            evidence_state="MEASURED" if ready else "UNAVAILABLE",
            extra_headers={
                "Cache-Control": "no-store",
                "X-SZL-Surface": "ALLOY_REFINEMENT_OBSERVATORY",
                "X-SZL-Authority": "READ_ONLY",
                "X-SZL-Content-Access": "HANDLES_ONLY",
            },
        )

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        path = parsed.path
        if path in {
            "/lib/refinement_patterns.public.json",
            "/lib/refinement_source.json",
            "/lib/refinement_living_runtime.py",
            "/lib/refinement_contract.py",
        }:
            self._send_json(
                {"error": "not_found", "state": "BLOCKED_INTERNAL_RUNTIME_PATH"},
                status=404,
                evidence_state="UNAVAILABLE",
            )
            return
        if path == "/refinement-lab":
            self.path = "/refinement-lab.html"
            super().do_GET()
            return
        if path == "/api/anatomy/v1/refinement/status":
            self._send_refinement(projection_status())
            return
        if path == "/api/anatomy/v1/refinement/patterns":
            query = parse_qs(parsed.query)
            error_code = str((query.get("error_code") or [""])[0])[:64] or None
            limit = self._bounded_limit((query.get("limit") or [50])[0])
            try:
                payload = pattern_payload(error_code, limit)
            except RefinementProjectionError as exc:
                payload = {
                    "schema": "szl.anatomy.refinement-patterns/v1",
                    "state": "BLOCKED",
                    "ready": False,
                    "reason": type(exc).__name__,
                    "handles": [],
                    "returned_count": 0,
                    "content_access": "HANDLES_ONLY",
                    "authority": "READ_ONLY",
                }
            self._send_refinement(payload)
            return
        super().do_GET()


def make_server(
    host: str = "0.0.0.0", port: int = anatomy_server.PORT
) -> ThreadingHTTPServer:
    handler = functools.partial(
        RefinementLivingAnatomyHandler,
        directory=str(anatomy_server.DIRECTORY),
    )
    return ThreadingHTTPServer((host, port), handler)


if __name__ == "__main__":
    httpd = make_server()
    print(
        "Serving SZL Living Anatomy with Alloy Refinement Observatory on "
        f"0.0.0.0:{anatomy_server.PORT}; "
        + json.dumps(projection_status(), sort_keys=True),
        flush=True,
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
