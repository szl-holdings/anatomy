#!/usr/bin/env python3
"""Hardened static file server for the SZL Cosmos Space.

Serves the vendored 3D hologram (same directory, same port as
`python -m http.server 7860`) but adds security response headers on every
response:
  - Content-Security-Policy   (sane static policy, tuned to this page's assets)
  - Strict-Transport-Security (max-age=31536000; includeSubDomains)
  - X-Content-Type-Options    (nosniff)
  - Referrer-Policy           (strict-origin-when-cross-origin)

Additive / non-breaking. The CSP permits every resource this Space actually
uses (inline scripts incl. the ES-module importmap, inline styles, vendored
Three.js + postprocessing modules, the data: favicon, the local
data/org_nodes.json fetch, and the live /healthz + /lambda + /khipu/ledger +
verify fetches to a11oy / killinchu / a-11-oy.com), so the hologram and the live
HUD keep working. Everything else is 'self' â€” zero CDN.
"""
import functools
import json
import os
import urllib.parse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from szl_source_attestation import build_attestation
from catalog import CATALOG
from source_binding import bound_source

PORT = int(os.environ.get("PORT", "7860"))
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
SPACE_ID = "betterwithage/cosmos"
SOURCE_OBSERVATION = {
    "repository": None,
    "commit": None,
    "path": None,
    "relation": "no-verifiable-direct-source-observed",
    "state": "UNKNOWN",
    "evidence_url": None,
}

CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "base-uri 'self'; "
    "object-src 'none'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob:; "
    "font-src 'self'; "
    "connect-src 'self' https://szlholdings-a11oy.hf.space "
    "https://szlholdings-killinchu.hf.space https://a-11-oy.com; "
    "frame-ancestors 'self' https://huggingface.co https://*.hf.space https://*.huggingface.co"
)


class HardenedHandler(SimpleHTTPRequestHandler):
    def _private_static_path(self):
        path = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path)
        return any(part.startswith('.') or part == '__pycache__' or part.endswith('.pyc')
                   for part in path.replace('\\', '/').split('/') if part)

    def do_HEAD(self):
        # The explicit source route is public; HEAD returns its headers only.
        if urllib.parse.urlsplit(self.path).path == '/.well-known/szl-source.json':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            return
        if self._private_static_path():
            self.send_error(404)
            return
        super().do_HEAD()

    def _send_json(self, payload):
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-SZL-Transport-State", str(payload["transport_state"]))
        self.send_header("X-SZL-Evidence-State", str(payload["evidence_state"]))
        self.send_header("X-SZL-Verification-State", str(payload["verification_state"]))
        self.send_header("X-SZL-Authority-State", str(payload["authority_state"]))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path == "/api/catalog":
            body = json.dumps(CATALOG.snapshot(), separators=(",", ":")).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path in ("/health", "/healthz"):
            body = json.dumps(
                {
                    "ok": True,
                    "service": "cosmos",
                    "lambda_status": "Conjecture 1",
                    "energy": None,
                    "signer": "UNSIGNED-honest",
                },
                separators=(",", ":"),
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        if parsed.path == "/.well-known/szl-source.json":
            force = urllib.parse.parse_qs(parsed.query).get("refresh") == ["1"]
            bound, alignment = bound_source(DIRECTORY)
            self._send_json(
                build_attestation(
                    SPACE_ID,
                    bound or SOURCE_OBSERVATION,
                    alignment,
                    force=force,
                )
            )
            return
        if self._private_static_path():
            self.send_error(404)
            return
        super().do_GET()

    def end_headers(self):
        self.send_header("Content-Security-Policy", CONTENT_SECURITY_POLICY)
        self.send_header(
            "Strict-Transport-Security", "max-age=31536000; includeSubDomains"
        )
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        super().end_headers()


if __name__ == "__main__":
    handler = functools.partial(HardenedHandler, directory=DIRECTORY)
    httpd = ThreadingHTTPServer(("0.0.0.0", PORT), handler)
    print(f"Serving hardened static site from {DIRECTORY} on 0.0.0.0:{PORT}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
