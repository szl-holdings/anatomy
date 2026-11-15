# SPDX-License-Identifier: Apache-2.0
"""Contract for the v11 holo3d front-door mount (3D holographic constellation)."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class HolographicV11Holo3dContract(unittest.TestCase):
    def test_front_door_mounts_exactly_one_v11_asset_pair_and_keeps_v7(self) -> None:
        html = read("index.html")
        self.assertEqual(html.count('data-szl-holographic-v11="style"'), 1)
        self.assertEqual(html.count('data-szl-holographic-v11="script"'), 1)
        self.assertIn('href="/v11_holo3d.css"', html)
        self.assertIn('src="/v11_holo3d.js"', html)
        self.assertIn('role="dialog"', html)
        self.assertIn('aria-modal="true"', html)
        self.assertEqual(html.count('data-szl-holographic-v7="style"'), 1)
        self.assertEqual(html.count('data-szl-holographic-v7="script"'), 1)

    def test_dock_yields_to_the_v11_panel(self) -> None:
        html = read("index.html")
        rule = re.search(
            r"body:has(#panel.open,[^{]*{s*visibility:s*hidden;s*}", html
        )
        self.assertIsNotNone(rule)
        self.assertIn("#v11-holo.open", rule.group(0))
        pre_dock = html[: html.index("#anatomy-instruments {")]
        self.assertIn("#v11-holo.open{display:flex}", pre_dock)

    def test_holo3d_client_is_same_origin_handles_only_and_fails_closed(self) -> None:
        source = read("v11_holo3d.js")
        for endpoint in (
            "/api/anatomy/v1/holographic-v7",
            "/api/anatomy/v1/frontier/handles",
            "/api/anatomy/v1/frontier/formulas",
            "/api/anatomy/v1/frontier/ouroboros",
        ):
            self.assertIn(endpoint, source)
        self.assertIn("window.location.origin", source)
        self.assertIn("CROSS_ORIGIN_REJECTED", source)
        self.assertIn('redirect: "error"', source)
        self.assertIn('credentials: "same-origin"', source)
        self.assertIn('cache: "no-store"', source)
        self.assertIn("HANDLES_ONLY", source)
        self.assertIn("failing closed", source)
        self.assertIn("prefers-reduced-motion", source)
        self.assertIn("ResizeObserver", source)
        self.assertIn('e.key === "Escape"', source)
        self.assertIn("PROCEDURAL LAYOUT", source)
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
            "http://",
            "https://",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIsNone(re.search(r".content", source))

    def test_holo3d_module_is_syntax_valid(self) -> None:
        node = shutil.which("node")
        if node is None:
            self.skipTest("node unavailable for syntax check")
        result = subprocess.run(
            [node, "--check", str(ROOT / "v11_holo3d.js")],
            capture_output=True, text=True, timeout=30, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_assets_are_bounded_and_add_no_nav_or_tracking_layer(self) -> None:
        js = ROOT / "v11_holo3d.js"
        css = ROOT / "v11_holo3d.css"
        self.assertTrue(5_000 < js.stat().st_size < 80_000)
        self.assertTrue(1_500 < css.stat().st_size < 40_000)
        css_text = css.read_text(encoding="utf-8")
        self.assertNotIn("@import", css_text)
        self.assertNotIn("url(http", css_text)
        combined = read("v11_holo3d.js") + chr(10) + css_text
        for marker in ("global-nav", "primary-nav", "GoogleAnalytics", "gtag(", "segment.com", "mixpanel"):
            self.assertNotIn(marker, combined)
            self.assertNotIn(marker, combined.lower() if marker.islower() else combined)

    def test_receipt_is_valid(self) -> None:
        receipt = json.loads(read("docs/v11_holo3d.receipt.json"))
        self.assertEqual(receipt["schema"], "szl.holo3d/v1")
        self.assertIn("files_changed", receipt)
        self.assertIn("HANDLES_ONLY", receipt["doctrine"])


if __name__ == "__main__":
    unittest.main()
