# Unified Python runtime for SZL Living Anatomy + YACHAY Second Brain.
# The 3D bundle stays vendored and zero-CDN. living_runtime.py extends the
# existing hardened server in-process with a source-bound, handles-only Brain
# organ; no private graph, model weights, or write authority enter the image.
FROM mirror.gcr.io/library/python:3.12-slim@sha256:57cd7c3a7a273101a6485ba99423ee568157882804b1124b4dd04266317710de
WORKDIR /app
COPY . /app
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/api/anatomy/v1/living-health', timeout=2).read()"
CMD ["python", "frontier_runtime.py"]
