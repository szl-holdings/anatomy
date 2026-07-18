# Thin static server for the SZL Living Anatomy bundle.
# This Space was migrated Docker->static by deleting this Dockerfile, which wedged
# the HF runtime (404 on every path, and a static Space cannot be restarted).
# Restoring the Docker wrapper serves the SAME vendored-free static bundle
# (index.html + app.js + lib/three.min.js, zero runtime CDN) on the HF app_port.
# server.py sets COOP/CORP on every response (PRESERVED unchanged), because under
# sdk:docker HF does NOT apply the README custom_headers block (that lever is
# static-SDK only), and ADDS the previously-missing CSP/HSTS/nosniff/Referrer
# headers plus a clean "szl" Server banner. Same files, same port 7860.
FROM public.ecr.aws/docker/library/python:3.12-slim
WORKDIR /app
COPY . /app
EXPOSE 7860
CMD ["python", "server.py"]
