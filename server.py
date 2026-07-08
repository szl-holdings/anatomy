#!/usr/bin/env python3
"""Hardened static file server for the SZL Living Anatomy Space.

Serves exactly the same files as the previous inline `http.server` (same /app
directory, same port 7860) but adds security response headers on every response,
while PRESERVING the Cross-Origin-Opener-Policy / Cross-Origin-Resource-Policy
this Space already emitted (do not regress the embed posture).

Additive / non-breaking:
  - Cross-Origin-Opener-Policy   same-origin-allow-popups   (PRESERVED, unchanged)
  - Cross-Origin-Resource-Policy cross-origin               (PRESERVED, unchanged)
  - Content-Security-Policy      (the exact origin allow-list the page already
                                  enforces via its own <meta http-equiv> CSP, now
                                  also as an HTTP header, plus frame-ancestors)
  - Strict-Transport-Security    max-age=31536000; includeSubDomains
  - X-Content-Type-Options       nosniff
  - Referrer-Policy              strict-origin-when-cross-origin
  - Server                       clean "szl" banner (suppresses SimpleHTTP/Python
                                  version disclosure)

The CSP mirrors the page's own vetted meta CSP: it keeps 'unsafe-inline' for
script/style (the 3D atlas ships heavy inline JS + inline styles + a WebGL
canvas), allows data:/blob: images, and an explicit connect-src allow-list for
the live read-only fetches to a11oy / killinchu / amaru / sentra HF spaces, so
the anatomy scene and live HUD keep working.

Health contract:
  - GET /healthz  -> 200 application/json health payload matching the fleet
                     monitor contract (up{job="szl-flagship"} scrape target).
                     Additive; all other paths fall through to static serving
                     unchanged.
"""
import functools
import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PORT = 7860
DIRECTORY = "/app"

# Doctrine v11 — LOCKED: 749 / 14 / 163 · locked_at c7c0ba17.
HEALTHZ_PAYLOAD = {
    "status": "ok",
    "organ": "anatomy",
    "service": "anatomy-space",
    "doctrine": "v11",
    "lock": "749/14/163",
    "commit": "c7c0ba17",
    "role": "visualization",  # embeddable 3D scene, not a governance console
    "note": "static bundle; live HUD fetches a11oy/killinchu read-only",
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
    "https://szlholdings-killinchu.hf.space https://szlholdings-amaru.hf.space "
    "https://szlholdings-sentra.hf.space; "
    "form-action 'self'; "
    "frame-ancestors 'self' https://huggingface.co https://*.hf.space https://*.huggingface.co"
)


class HardenedHandler(SimpleHTTPRequestHandler):
    server_version = "szl"
    sys_version = ""

    def version_string(self):
        return "szl"

    def do_GET(self):
        # Additive health route for the fleet monitor. Everything else falls
        # through to normal static file serving, unchanged.
        if self.path.split("?", 1)[0] == "/healthz":
            body = json.dumps(HEALTHZ_PAYLOAD).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def end_headers(self):
        # PRESERVE the COOP/CORP this Space already sent (unchanged embed posture).
        self.send_header("Cross-Origin-Opener-Policy", "same-origin-allow-popups")
        self.send_header("Cross-Origin-Resource-Policy", "cross-origin")
        # ADD the previously-missing security headers.
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
