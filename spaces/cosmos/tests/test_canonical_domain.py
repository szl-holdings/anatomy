import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
RUNTIME_FILES = (
    ROOT / "server.py",
    ROOT / "index.html",
    ROOT / "vendor" / "szl_verify_widget.js",
)


class CanonicalDomainContractTests(unittest.TestCase):
    def test_runtime_has_no_retired_domain(self):
        for path in RUNTIME_FILES:
            with self.subTest(path=path.name):
                self.assertNotIn("a11oy.net", path.read_text(encoding="utf-8"))

    def test_widget_targets_live_receipt_verifier(self):
        widget = RUNTIME_FILES[-1].read_text(encoding="utf-8")
        self.assertIn("https://a-11-oy.com", widget)
        self.assertIn("/api/a11oy/v1/verify/receipt", widget)
        self.assertIn("JSON.stringify({envelope: envelope})", widget)

    def test_csp_allows_only_canonical_a11oy_origin(self):
        server = RUNTIME_FILES[0].read_text(encoding="utf-8")
        self.assertIn("connect-src 'self'", server)
        self.assertIn("https://a-11-oy.com", server)


if __name__ == "__main__":
    unittest.main()
