from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_runtime_entrypoint_and_creator_publisher_include_v7() -> None:
    dockerfile = read("Dockerfile")
    publisher = read("scripts/sync_hf_creator_profile.py")
    assert '"frontier_runtime.py"' in publisher
    assert '"*.js"' in publisher
    assert '"*.css"' in publisher
    assert "frontier_runtime:app" in dockerfile
    assert "living_runtime:app" not in dockerfile
    assert "second_brain_runtime:app" not in dockerfile


def test_front_door_mounts_exactly_one_v7_asset_pair() -> None:
    html = read("index.html")
    assert html.count('data-szl-holographic-v7="style"') == 1
    assert html.count('data-szl-holographic-v7="script"') == 1
    assert 'href="/holographic-v7.css"' in html
    assert 'src="/holographic-v7.js"' in html
    assert "http://" not in read("holographic-v7.js")
    assert "https://" not in read("holographic-v7.js")


def test_v7_client_is_same_origin_handles_only_and_non_persistent() -> None:
    source = read("holographic-v7.js")
    for endpoint in (
        "/api/anatomy/v1/holographic-v7",
        "/api/anatomy/v1/frontier/handles",
        "/api/anatomy/v1/frontier/formulas",
        "/api/anatomy/v1/frontier/ouroboros",
    ):
        assert endpoint in source
    assert "window.location.origin" in source
    assert "CROSS_ORIGIN_REJECTED" in source
    assert 'redirect: "error"' in source
    assert 'credentials: "same-origin"' in source
    assert 'cache: "no-store"' in source
    assert "HANDLES_ONLY" in source
    assert "DISCOVERED_REVIEW_REQUIRED" in source
    assert "handle.content" not in source
    assert "payload.content" not in source
    for forbidden in (
        "localStorage",
        "sessionStorage",
        "indexedDB",
        "WebSocket",
        "EventSource",
        "sendBeacon",
        "document.cookie",
        "eval(",
        "new Function",
    ):
        assert forbidden not in source


def test_v7_is_accessible_mobile_safe_and_motion_aware() -> None:
    source = read("holographic-v7.js")
    css = read("holographic-v7.css")
    assert 'role", "dialog"' in source
    assert 'aria-modal", "true"' in source
    assert 'role="tablist"' in source
    assert 'role="tabpanel"' in source
    assert 'event.key === "Escape"' in source
    assert 'event.key === "Tab"' in source
    assert "ArrowLeft" in source and "ArrowRight" in source
    assert "ResizeObserver" in source
    assert "prefers-reduced-motion: reduce" in css
    assert "forced-colors: active" in css
    assert "env(safe-area-inset-right)" in css
    assert "env(safe-area-inset-bottom)" in css
    assert "@media (max-width: 860px)" in css
    assert "@media (max-width: 520px)" in css
    assert "min-height: 44px" in css or "height: 44px" in css


def test_v7_does_not_add_another_global_navigation_or_tracking_layer() -> None:
    source = read("holographic-v7.js")
    css = read("holographic-v7.css")
    combined = source + "\n" + css
    assert "szl-v7__tabs" in combined
    assert "global-nav" not in combined
    assert "primary-nav" not in combined
    assert "GoogleAnalytics" not in combined
    assert "gtag(" not in combined
    assert "segment.com" not in combined
    assert "mixpanel" not in combined.lower()


def test_creator_profile_and_v7_truth_are_documented() -> None:
    readme = read("README.md")
    contract = read("docs/LIVING_ANATOMY_SECOND_BRAIN.md")
    for document in (readme, contract):
        assert "betterwithage/anatomy" in document
        assert "SZLHOLDINGS/anatomy" not in document
        assert "575" in document
        assert "HANDLES_ONLY" in document
        assert "Conjecture 1" in document
    assert "Holographic v7" in readme
    assert "30 attributed" in readme
    assert "21 executable" in readme
    assert "nine quant domains" in readme
    assert "review" in readme.lower()


def test_assets_are_bounded_and_syntax_inputs_are_local() -> None:
    js = ROOT / "holographic-v7.js"
    css = ROOT / "holographic-v7.css"
    assert 5_000 < js.stat().st_size < 80_000
    assert 3_000 < css.stat().st_size < 40_000
    assert "@import" not in css.read_text(encoding="utf-8")
    assert "url(http" not in css.read_text(encoding="utf-8")
