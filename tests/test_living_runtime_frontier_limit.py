from __future__ import annotations

import json
import threading
from urllib.request import urlopen

import living_runtime


class _FrontierProbe:
    def __init__(self) -> None:
        self.limits: list[int] = []

    def search(self, _query: str, *, k: int, **_filters: object) -> dict[str, object]:
        self.limits.append(k)
        return {
            "schema": "szl.anatomy.frontier-handles/v1",
            "ready": True,
            "matched_count": 61,
            "returned_count": k,
            "handles": [],
            "content_access": "HANDLES_ONLY",
        }


def test_living_transport_honors_frontier_formula_limit(monkeypatch) -> None:
    probe = _FrontierProbe()
    monkeypatch.setattr(living_runtime, "FRONTIER_ATLAS", probe)
    server = living_runtime.make_server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        with urlopen(
            f"http://{host}:{port}/api/anatomy/v1/frontier/formulas?k=48",
            timeout=5,
        ) as response:
            payload = json.load(response)
        assert response.status == 200
        assert payload["returned_count"] == 48
        assert probe.limits == [48]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_non_frontier_limits_remain_bounded_to_24() -> None:
    assert living_runtime.LivingAnatomyHandler._bounded_k(48) == 24
    assert (
        living_runtime.LivingAnatomyHandler._bounded_k(48, maximum=48)
        == 48
    )
