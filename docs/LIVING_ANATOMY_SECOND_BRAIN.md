# Living Anatomy + YACHAY Second Brain

## Production contract

`SZLHOLDINGS/anatomy` is a **KEEP / public / running** Hugging Face flagship. GitHub
`szl-holdings/anatomy` is the runtime source of truth. The Space is a deployment
mirror, not an independent source tree.

The Docker entry point is `living_runtime.py`. It extends the existing hardened
`server.py` in-process and preserves every static, evidence, receipt, organ-integrity,
and security-header route. The extension adds a read-only YACHAY Brain organ:

| Interface | Purpose |
|---|---|
| `GET /api/anatomy/v1/living-health` | Combined Anatomy + Brain readiness |
| `GET /api/anatomy/v1/brain/health` | Snapshot integrity, source SHA, counts, authority |
| `GET /api/anatomy/v1/brain/manifest` | Machine-readable source and interface contract |
| `GET/POST /api/anatomy/v1/brain/search` | BM25-like public-handle retrieval |
| `GET/POST /api/anatomy/v1/brain/context` | Model-safe handles plus evidence pointers |

## Source binding

`scripts/materialize_second_brain.py` resolves the exact protected-main revision of
`szl-holdings/szl-second-brain`, downloads only:

- `data/manifest.json`
- `data/brain-corpus.public.jsonl`

It validates:

1. exactly 575 public chunks;
2. the declared source histogram;
3. every row's SHA-256;
4. `secretScan: PASS`;
5. unique public node IDs.

The operator writes `.runtime/second-brain/source.json` with the exact Git SHA,
manifest digest, corpus digest, count, and authority constraints. The HF sync workflow
bundles that immutable snapshot and records the dependency in
`hf-deploy-manifest.json`.

## Non-negotiable boundary

The public Space returns **handles only**. It does not expose corpus text through the
API, load the owner's private 9,464-node graph, train weights, execute tools, or hold
write authority. Lexical ranking is relevance, never correctness. Lambda remains
Conjecture 1.

The richer product-side living-brain loop in `szl-holdings/a11oy` remains a separate
governed execution surface. The public HF Anatomy is its inspectable, read-only
anatomical instrument—not a duplicate mutation authority.

## Reproduce locally

```bash
python scripts/materialize_second_brain.py --output .runtime/second-brain
python -m unittest discover -s tests -v
python living_runtime.py
```

Then inspect:

```text
http://127.0.0.1:7860/api/anatomy/v1/living-health
http://127.0.0.1:7860/api/anatomy/v1/brain/health
http://127.0.0.1:7860/api/anatomy/v1/brain/search?q=governed%20receipts&k=6
```

## Lifecycle

`.github/workflows/hf-sync.yml` runs on protected-main changes, manual dispatch, and
a six-hour reconciliation cadence. It:

1. validates the exact Second Brain projection;
2. refuses a stale GitHub source revision;
3. makes `SZLHOLDINGS/anatomy` public;
4. restarts paused, sleeping, stopped, or failed runtime states;
5. avoids a rebuild when both source revisions are already deployed;
6. verifies the live Anatomy, Brain, version, evidence, source, and manifest contracts.

A separate estate keep policy in `szl-holdings/a11oy` must include
`SZLHOLDINGS/anatomy`; otherwise the fleet consolidator will correctly treat it as a
fold. That policy is part of the same coordinated repair.
