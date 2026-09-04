# Living Anatomy + YACHAY Second Brain

## Production contract

`betterwithage/anatomy` is the source-bound creator-profile Hugging Face Space for
**SZL Living Anatomy**. GitHub `szl-holdings/anatomy` is the runtime source of truth;
the Space is a deployment mirror, not an independent source tree.

The Docker entry point is `frontier_runtime.py`. It extends the existing hardened
`living_runtime.py` application in process and preserves every static, evidence,
receipt, organ-integrity, security-header, and original Second Brain route. The v7
extension adds the review-gated frontier tissue described below.

## Original public Second Brain projection

`scripts/materialize_second_brain.py` resolves the exact protected-main revision of
`szl-holdings/szl-second-brain` and downloads only the committed public projection:

- `data/manifest.json`
- `data/brain-corpus.public.jsonl`

The materializer verifies:

1. exactly 575 public chunks;
2. the declared source histogram;
3. every row's SHA-256 digest;
4. `secretScan: PASS`;
5. unique public node identifiers.

These interfaces remain available:

| Interface | Purpose |
|---|---|
| `GET /api/anatomy/v1/living-health` | Combined Anatomy + Brain readiness |
| `GET /api/anatomy/v1/brain/health` | Snapshot integrity, source SHA, counts, and authority |
| `GET /api/anatomy/v1/brain/manifest` | Machine-readable source and interface contract |
| `GET/POST /api/anatomy/v1/brain/search` | BM25-like public-handle retrieval |
| `GET/POST /api/anatomy/v1/brain/context` | Model-safe handles plus evidence pointers |

## Holographic v7 frontier tissue

The same exact Second Brain revision also supplies:

- `data/frontier-state.v1.json`
- `data/frontier-candidates.public.jsonl`

Those files are a **review memory**, not automatically accepted knowledge. They are
built from six fixed public source contracts and contain content-addressed candidates
for Second Brain, Living Anatomy, A11oy, governed inference, Nemo, Ouroboros, and the
source-owned formula/quant atlas.

Before bundling the snapshot, the materializer verifies every candidate identifier,
source revision, content digest, candidate-set digest, and authority field. It also
requires the formula tissue to expose exactly:

- 30 attributed formula records;
- 21 executable formula functions;
- nine quant domains;
- a locked-proven formula count of exactly eight;
- an explicit `UNKNOWN_NOT_INFERRED` mapping between F-number identities and the
  executable registry;
- Lambda as **Conjecture 1**, advisory only.

The public v7 endpoints are:

| Interface | Purpose |
|---|---|
| `GET /api/anatomy/v1/frontier/status` | Exact Second Brain source, candidate-set digest, counts, and authority |
| `GET /api/anatomy/v1/frontier/handles` | Handles-only review-candidate retrieval |
| `GET /api/anatomy/v1/frontier/formulas` | Attributed, executable, and quant-domain formula handles |
| `GET /api/anatomy/v1/frontier/ouroboros` | Ouroboros source handles and bounded-loop evidence |
| `GET /api/anatomy/v1/holographic-v7` | Combined read-only Brain, formula, quant, and loop organ contract |

`holographic-v7.js` renders those same-origin endpoints as a compact responsive HUD
over the existing 3D organism. It introduces no second global navigation, CDN,
telemetry, browser persistence, cross-origin fetch, candidate-content route, or
execution control. Keyboard, focus containment, safe-area, reduced-motion, and
forced-color behavior are part of the checked interface.

## Non-negotiable authority boundary

The public Space returns **handles, digests, revisions, counts, and receipts only**.
It does not expose candidate or corpus content through the v7 API, load the owner's
private 9,464-node graph, admit raw graph nodes to gradients, train weights, promote a
claim, execute tools, merge code, or mutate a provider.

The continuous Second Brain workflow may discover source changes and open a
content-addressed pull request for human review. The continuous Ouroboros/Codex loop
may analyze the exact candidate set in a read-only sandbox and open a review issue.
Neither loop can silently convert discovery into truth or action.

Lexical ranking is relevance, never correctness. A running Space proves reachability,
not source revision, model quality, scientific truth, safety, or authorization.
Lambda remains Conjecture 1.

## Source receipt

The materializer writes `.runtime/second-brain/source.json` with:

- the exact Second Brain Git revision;
- corpus, manifest, state, and candidate-file digests;
- the candidate-set digest and candidate count;
- source-kind and quant-domain counts;
- handles-only, read-only, no-training, no-promotion, no-execution, no-private-graph,
  and no-gradient authority declarations.

The creator-profile publisher records that snapshot in `hf-deploy-manifest.json` and
verifies the live Space against the exact deployment commit before calling it
source-bound.

## Reproduce locally

```bash
python scripts/materialize_second_brain.py --output .runtime/second-brain
python -m pytest -q
node --check holographic-v7.js
python frontier_runtime.py
```

Then inspect:

```text
http://127.0.0.1:7860/api/anatomy/v1/living-health
http://127.0.0.1:7860/api/anatomy/v1/brain/health
http://127.0.0.1:7860/api/anatomy/v1/frontier/status
http://127.0.0.1:7860/api/anatomy/v1/frontier/formulas?k=48
http://127.0.0.1:7860/api/anatomy/v1/holographic-v7
```

## Lifecycle

`.github/workflows/hf-sync.yml` runs on protected-main changes, manual dispatch, and
a six-hour reconciliation cadence. It:

1. materializes and validates the exact Second Brain projection and frontier memory;
2. refuses stale GitHub source revisions;
3. publishes only to `betterwithage/anatomy`;
4. restarts paused, sleeping, stopped, or failed runtime states;
5. avoids a rebuild when both source revisions are already deployed;
6. verifies the live Anatomy, Brain, frontier, formula, v7, version, evidence, source,
   and manifest contracts against the exact published revision.
