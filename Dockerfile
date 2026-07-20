# Thin static server for the SZL Living Anatomy bundle.
# This Space was migrated Docker->static by deleting this Dockerfile, which wedged
# the HF runtime (404 on every path, and a static Space cannot be restarted).
# Restoring the Docker wrapper serves the SAME vendored-free static bundle
# (index.html + app.js + lib/three.min.js, zero runtime CDN) on the HF app_port.
# server.py sets COOP/CORP on every response (PRESERVED unchanged), because under
# sdk:docker HF does NOT apply the README custom_headers block (that lever is
# static-SDK only), and ADDS the previously-missing CSP/HSTS/nosniff/Referrer
# headers plus a clean "szl" Server banner. Same files, same port 7860.
FROM mirror.gcr.io/library/python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de
WORKDIR /app
COPY . /app
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/healthz', timeout=2).read()"
CMD ["python", "server.py"]
