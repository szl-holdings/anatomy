# V11 Holo: paired-source coherence (unsigned)

Scope: source-only, no deployment or model execution. Initial protected-main parent:
`szl-holdings/anatomy@5cbe43e614334a58b17f2b6e16fdf878e6223999`.

## Design

A Holographic v11 browser may visualize **read-only handle IDs** only after its
same-origin responses satisfy two independent, structural gates:

1. **Required source pair:** `/api/anatomy/v1/holographic-v7` embeds
   `frontier`; `/api/anatomy/v1/frontier/status` reports a separate read.
   Both must be ready, in the expected schemas and read-only states, have
   no execution/promotion/training authority, identify the canonical
   Second Brain repository, and agree exactly on source revision (40-hex
   SHA), candidate-set digest (64-hex SHA-256), candidate count and the
   other enumerated identity/authority fields. No live revision/count is
   hardcoded.
2. **Per-feed dataset binding:** Each optional handles/formulas/Ouroboros
   response must share that candidate-set digest and a bounded,
   handles-only envelope. Valid handle IDs use `frontier:` plus 32
   lowercase hexadecimal characters; rows must have distinct IDs,
   valid content-access labels and an exact returned count.
   The browser retains **only** an ID and safe access label per accepted
   row, not other fields from the response.

## Explicit failure precedence

| Condition | What users see | Data admitted |
| --- | --- | --- |
| Holographic source status unavailable | SOURCE FEEDS UNAVAILABLE | No handles |
| Source status unready | SOURCE STATUS HOLD | No handles |
| Paired status unavailable, invalid or inconsistent | SOURCE COHERENCE HOLD | No handles |
| One optional feed unavailable, malformed, stale or mismatched | DEGRADED SOURCE FEEDS | Only independently valid feeds |
| Paired source coherent, WebGL missing | Renderer-unavailable handle-list fallback | Safe handle IDs only |
| Paired source coherent, WebGL available | Procedural 3D review constellation | Safe handle IDs only |

The client uses same-origin requests, error redirects, no-store caching and
per-request bounds. Retrying rechecks **both** required sources and optional
feeds; a previous success cannot authorize a new stale snapshot.

## Not proven by this source-only change

Matching API metadata is **not independent verification** of candidate
content, publisher provenance, GitHub protected-main alignment, signing keys,
source authenticity, served Khipu weights, authenticated inference,
grounded navigation, or actual browser GPU/WebGL rendering. A compromised
origin can supply mutually consistent lies. Do not display a production-green
or cryptographic-attestation badge from this consistency test.

## Local deterministic replay

```text
node --check v11_holo3d.js
node --test tests/test_v11_holo3d_runtime.cjs
python -B -m unittest discover -s tests -p test_v11_holo3d_contract.py -q
git diff --check
```

Negative fixtures exercise mismatch in source revision, candidate digest,
count, schema and authority; unready/missing/HTTP-503 witnesses; invalid
and duplicate handle envelopes; optional-feed isolation; private-text
non-disclosure; and WebGL-off fallback followed by a renderer retry.
Human review, protected branch checks and separate deployment admission
remain required.
