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
with the attributed formula/quant atlas, modeled review DAG, and explicitly
qualified Ouroboros observations.

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
| `GET /api/anatomy/v1/brain/ouroboros` | Exact loop-source handles and explicit runtime-evidence availability |
| `GET /api/anatomy/v1/brain/pipeline` | Source-bound RAG, modeled DAG, and freshness-checked review observation |
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
- a Pipeline tab linking RAG counts, modeled review stages, and recorded review evidence;
- nullable Ouroboros measurements with consumer-clock expiry;
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
digest, admitted A11oy snapshot identity, live formula/quant/Ouroboros/pipeline
routes, and runtime-file access block before
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
http://127.0.0.1:7860/api/anatomy/v1/brain/pipeline
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
5. avoids an unnecessary rebuild when the exact Anatomy, Brain, frontier, and
   admitted A11oy snapshot dependencies are already deployed;
6. verifies the live Anatomy, Brain, formula, quant, Ouroboros, pipeline, Neural Quant v7,
   version, evidence, source, and manifest contracts.

## Holographic v7 companion instrument

Holographic v7 is an additive, read-only surface served by `frontier_runtime.py` at the same origin as the existing Neural Quant v7 experience. The runtime accepts the protected flat receipt emitted by current `main` while retaining read compatibility with the earlier nested frontier receipt shape. It does not create a second authority plane.

The canonical public surface is `betterwithage/anatomy`. Its source-bound snapshot remains 575 public chunks, 30 attributed formulas, 21 executable formulas, and nine quant domains. Identity is `HANDLES_ONLY`; lambda remains `Conjecture 1`; frontier candidates remain review-gated and cannot be promoted by this instrument.

The container starts `frontier_runtime.py`, which imports the existing living runtime and adds the Holographic v7 routes. Publishing includes the runtime and both local assets. No CDN, browser persistence, telemetry, credential material, or cross-origin data authority is introduced.

## Ouroboros source and runtime evidence

The `szl.living-anatomy.ouroboros-observation/v2` response selects handles using
the validated `ouroboros_runtime` source receipt. The maintained Python
`szl-holdings/szl-ouroboros` package and archived TypeScript
`szl-holdings/ouroboros` lineage remain separate source identities. A missing
source receipt yields `UNAVAILABLE`; the reader never substitutes unrelated
frontier handles.

A public source snapshot proves which documents were indexed. It does not
prove that a loop ran or terminated within budget. Those properties remain
`null` in `loop_contract` until a fresh, source-bound producer report is
available. `contract_requirements` records the required properties without
presenting them as measured outcomes. A reported `receipt_closed` means the
reviewer's recorded receipt accounting; it is not an acknowledgement from a
durable external ledger. Signature verification and accepted-truth claims
remain false. The v7 instrument shows `UNKNOWN` for absent or expired runtime
measurements and keeps every execution, training, promotion, merge, and provider
authority at `NONE`.

## RAG, DAG, and review observation binding

The materializer also resolves an exact `szl-holdings/a11oy` protected-main
revision and captures `console/assets/brain-frontier-v7.json` from that commit.
Its immutable bytes, file SHA-256, Git revision, path, and wrapper digest are
stored in the internal `pipeline-source.json`. The existing Second Brain
`source.json` binds that file. No browser request reaches GitHub or a remote
executor; the reader uses the locally packaged snapshot.

The admitted A11oy snapshot may carry two additional fields:

| Field | Interpretation in Anatomy |
|---|---|
| `advisory_dag` | The governed graph analyzer's `MODELED`, `PLAN_ONLY` result, with zero effectors, provider calls, writes, or execution authority. Anatomy rechecks its contract hash and acyclic dependencies, then exposes only bounded stage labels and dependencies. |
| `ouroboros_observation` | The source-bound review-attempt report produced from the maintained Ouroboros workflow artifact. Anatomy checks its hash, source identities, artifact/run identity, measurement domains, authority, and freshness. |

An observation is bound to the exact maintained controller revision, the
Second Brain revision, the **raw** state-file and candidate-file SHA-256 values,
the canonical candidate-set digest, and its candidate count. The raw state-file
digest is distinct from a digest of parsed canonical state. A source mismatch
produces `STALE`; a bad digest or authority claim produces `REJECTED`. Missing
data or a snapshot predating the bridge produces `UNAVAILABLE`. The reader
never replaces those states with an older successful observation.

Only a fresh `OBSERVED` report exposes measurement values. Its validity ends
21,600 seconds after the recorded workflow update time. The API rechecks this
on its own clock, and the UI rechecks cached responses on the browser clock.
Expiry yields `STALE` and null current measurements while preserving the
original recorded state and observation hash. Hashes identify a producer
report; they do not verify a signature, accept a recommendation, establish
production readiness, or load the private graph.

The Pipeline tab connects the existing RAG source/counts to the modeled review
stages and the qualified recorded review attempt. It provides no execution
control. `READY_TO_ORCHESTRATE` in the analyzed graph describes its structure;
it does not authorize or attest to stage execution.

The A11oy refresh workflow proposes a review pull request for its snapshot.
This reader consumes only the admitted main revision. Producer code, its
reviewed snapshot, and this consumer therefore each need their existing source
review and publication path. A current workflow artifact alone does not admit
a new snapshot. An admitted observation can age past six hours while awaiting
its next reviewed snapshot, in which case the honest display is `STALE`.

The deployment manifest records Anatomy, Second Brain, and A11oy revisions as
separate identities. It does not require Anatomy and A11oy to reference each
other's future commit. The no-op predicate includes A11oy's revision and raw
snapshot digest, so a newly admitted observation can trigger reconciliation
even when the Brain revision is unchanged. Capture timestamps alone do not
force a rebuild. Live readback verifies this same dependency before a
deployment can be reported current.
