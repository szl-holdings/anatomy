# Living Anatomy + YACHAY Second Brain + Neural Quant v7

## Production contract

The public Living Anatomy surface is the creator-profile Hugging Face Space
`betterwithage/anatomy`, served at `https://betterwithage-anatomy.hf.space`.
GitHub `szl-holdings/anatomy` is the runtime source of truth. The Space is a
source-bound deployment mirror, not an independent source tree and not a second
command plane.

The Docker entry point is `living_runtime.py`. It extends the existing hardened
`server.py` in-process and preserves every static, evidence, receipt,
organ-integrity, and security-header route. The extension adds two read-only
YACHAY memory planes:

1. the exact 575-chunk public Second Brain retrieval projection; and
2. the review-gated frontier candidate set built by `szl-second-brain` from a
   source manifest containing at least seven bound public source contracts.

Neural Quant v7 projects those planes into the 3D Anatomy experience together
with the attributed formula/quant atlas and bounded Ouroboros observations.

## Public interfaces

| Interface | Purpose |
|---|---|
| `GET /api/anatomy/v1/living-health` | Combined Anatomy + Brain + Neural Quant readiness |
| `GET /api/anatomy/v1/brain/health` | Snapshot integrity, source SHA, counts, formula/quant authority |
| `GET /api/anatomy/v1/brain/manifest` | Machine-readable source, receipt, and interface contract |
| `GET/POST /api/anatomy/v1/brain/search` | 575-chunk handles-only lexical retrieval |
| `GET/POST /api/anatomy/v1/brain/context` | Model-safe retrieval handles and evidence pointers |
| `GET/POST /api/anatomy/v1/brain/frontier` | Review-candidate handles filtered by query, kind, domain, or source |
| `GET /api/anatomy/v1/brain/formulas` | Attributed and executable formula handles plus proof boundary |
| `GET /api/anatomy/v1/brain/quant` | Nine-domain quant lattice and evidence handles |
| `GET /api/anatomy/v1/brain/ouroboros` | Bounded-loop source and receipt-closure observation |
| `GET /api/anatomy/v1/brain/neural-quant-v7` | Combined source-bound payload for the v7 holographic instrument |

All interfaces return handles, counts, source revisions, and SHA-256 digests.
They do not return corpus or candidate content.

## Exact source binding

`scripts/materialize_second_brain.py` resolves the exact protected-main revision
of `szl-holdings/szl-second-brain` and downloads only these public files from
that immutable commit:

- `data/manifest.json`
- `data/brain-corpus.public.jsonl`
- `data/frontier-state.v1.json`
- `data/frontier-candidates.public.jsonl`

It validates:

1. exactly 575 public retrieval chunks;
2. the declared retrieval source histogram;
3. every retrieval-row SHA-256;
4. `secretScan: PASS`;
5. unique public retrieval node IDs;
6. at least 70 content-addressed frontier candidates;
7. at least seven frontier source receipts, with unique repository/revision/path
   bindings and matching per-source candidate counts;
8. every frontier ID, source revision, content digest, and candidate-set digest;
9. 30 attributed formulas, 21 executable formulas, and nine quant domains;
10. the locked-proven set count remains exactly eight;
11. the F-number-to-executable mapping remains `UNKNOWN_NOT_INFERRED`;
12. Lambda remains `CONJECTURE_1_OPEN_ADVISORY_ONLY`;
13. zero private graph, training, promotion, execution, or merge authority.

The operator writes `.runtime/second-brain/source.json` with the exact Git SHA,
retrieval digests, frontier digests, candidate-set digest, formula/quant counts,
and authority constraints. The creator-profile publisher bundles that immutable
snapshot and records the dependency in `hf-deploy-manifest.json`.
The serving runtime also checks that the receipt's frontier source count equals
the validated manifest count. Additional sources are accepted only when these
bindings and the existing formula, digest, and authority checks remain valid.

## Neural Quant v7 holographic instrument

`neural-quant-v7.js` and `neural-quant-v7.css` add a local, zero-CDN visual
instrument to the existing Anatomy scene. It is a desktop overlay and mobile
bottom sheet with:

- a brain-shaped SVG nervous-system map;
- nine quant-domain nodes;
- public-memory, frontier, formula, and domain counts;
- formula authority and locked-eight readback;
- source-linked formula and quant handles;
- bounded Ouroboros and Codex-advisory observations;
- exact source, candidate-set, and view digests;
- keyboard focus trapping, Escape close, 44-pixel controls, safe areas,
  reduced-motion, high-contrast, and forced-color behavior.

The UI fetches only the same-origin
`/api/anatomy/v1/brain/neural-quant-v7` contract. Network payload values are
rendered with DOM `textContent`; remote HTML is never injected. A source failure
shows `UNAVAILABLE` and never synthesizes green state.

## Continuous learning and production

The Second Brain discovery workflow runs every two hours. It can create one
content-addressed review pull request when its fixed public source set changes.
That is the operational meaning of continuous learning here: public evidence is
continually re-indexed for governed review. It is not silent model retraining or
automatic truth promotion.

Living Anatomy republishes from protected main and also performs scheduled
reconciliation. The publisher verifies the exact creator-profile Space revision,
Anatomy source revision, Second Brain source revision, frontier candidate-set
digest, live formula/quant/Ouroboros routes, and runtime-file access block before
calling the deployment current.

## Non-negotiable boundary

The public Space:

- returns handles only;
- does not expose raw `.runtime` files;
- does not expose corpus or candidate content through APIs;
- does not load the owner's private 9,464-node graph;
- does not train or alter model weights;
- does not promote frontier candidates;
- does not execute tools or consequential actions;
- does not merge pull requests or mutate providers;
- does not upgrade empirical or conjectural material into proof.

Lexical ranking is relevance, never correctness. The locked-proven formula set
remains exactly eight. Lambda remains Conjecture 1.

The richer product-side living-brain loop in `szl-holdings/a11oy` remains a
separate governed execution surface. Living Anatomy is its inspectable,
read-only anatomical instrument—not a duplicate mutation authority.

## Reproduce locally

```bash
python scripts/materialize_second_brain.py --output .runtime/second-brain
python -m unittest discover -s tests -v
node --check neural-quant-v7.js
python living_runtime.py
```

Then inspect:

```text
http://127.0.0.1:7860/api/anatomy/v1/living-health
http://127.0.0.1:7860/api/anatomy/v1/brain/health
http://127.0.0.1:7860/api/anatomy/v1/brain/frontier?q=formula%20quant&k=12
http://127.0.0.1:7860/api/anatomy/v1/brain/neural-quant-v7?k=12
```

Direct access to the following internal path must return HTTP 404:

```text
http://127.0.0.1:7860/.runtime/second-brain/frontier-candidates.public.jsonl
```

## Lifecycle

`.github/workflows/hf-sync.yml` runs on protected-main changes, manual dispatch,
and scheduled reconciliation. It:

1. validates the exact Second Brain retrieval and frontier snapshots;
2. refuses a stale GitHub source revision;
3. creates or maintains the public creator-profile Space
   `betterwithage/anatomy`;
4. restarts paused, sleeping, stopped, or failed runtime states;
5. avoids an unnecessary rebuild when the exact Anatomy, Brain, and frontier
   revisions are already deployed;
6. verifies the live Anatomy, Brain, formula, quant, Ouroboros, Neural Quant v7,
   version, evidence, source, and manifest contracts.

## Holographic v7 companion instrument

Holographic v7 is an additive, read-only surface served by `frontier_runtime.py` at the same origin as the existing Neural Quant v7 experience. The runtime accepts the protected flat receipt emitted by current `main` while retaining read compatibility with the earlier nested frontier receipt shape. It does not create a second authority plane.

The canonical public surface is `betterwithage/anatomy`. Its source-bound snapshot remains 575 public chunks, 30 attributed formulas, 21 executable formulas, and nine quant domains. Identity is `HANDLES_ONLY`; lambda remains `Conjecture 1`; frontier candidates remain review-gated and cannot be promoted by this instrument.

The container starts `frontier_runtime.py`, which imports the existing living runtime and adds the Holographic v7 routes. Publishing includes the runtime and both local assets. No CDN, browser persistence, telemetry, credential material, or cross-origin data authority is introduced.
