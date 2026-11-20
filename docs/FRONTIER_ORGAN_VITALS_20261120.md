# Proof-conditioned Living Anatomy: organ-by-organ frontier plan (research pass 1)

**Read-only research observation:** 2026-11-20 UTC. **Source owner:** `szl-holdings/anatomy`. **Disposition:** SOURCE-ONLY / REVIEW REQUIRED; not a production acceptance claim. **Owner instruction:** Study public leaders, reuse lawful techniques, evolve SZL organs with real evidence, retain the existing trusted controllers and release gates.

This document accompanies a narrow, executable source improvement in `v5_organs.js` and `tests/test_v5_evidence_liveness.cjs`. It is a **candidate engineering plan**, not a claim to have built all of the integrations described below. No upstream code, model weights, full-text corpus, secrets, or proprietary assets were copied. Upstream documentation and ideas remain their owners' work.

## Exact SZL ownership at study baseline

The following protected-main SHA values were read directly from the GitHub branch API on authorized BETTERWITHAGE on 2026-11-20 UTC. They describe **source**, not deployed runtime or attested model bytes.

| Owner | Protected main SHA | Existing truth boundary |
| --- | --- | --- |
| [Anatomy](https://github.com/szl-holdings/anatomy) | `0ca96e524ee9c7ff15e13eee40feeb56ae9e4476` | Holo v11 uses paired source status and a handles-only renderer; #135 merged, #136 WebGL-disabled live-body fix in draft; exact browser release proof still required. |
| [A11oy](https://github.com/szl-holdings/a11oy) | `262d45bb94d1d1e37e1abb2e2172dfaa701838ce` | Canonical runtime and admission owner; [#3776](https://github.com/szl-holdings/a11oy/issues/3776) holds exact hosted Khipu binding and signed inference. |
| [Second Brain](https://github.com/szl-holdings/szl-second-brain) | `1736afff14ff3fd2202b701873cc01a719462dae` | Source-bound public handles, rights-gated review memory, controlled hydration; [research PR #102](https://github.com/szl-holdings/szl-second-brain/pull/102) covers temporal-memory and retrieval candidates. |
| [SZL Router](https://github.com/szl-holdings/szl-router) | `7d5503f71dd1dc2f94ee413e141a68e27e813b53` | Default-deny inference gateway; status 503 until provider, egress, caller auth and registry are configured. |
| [Vertical Services](https://github.com/szl-holdings/vertical-services) | `5824dd49c9aa5b8956f9c424049b67f1af7b5029` | Six-vertical, source-bound read-only frontier APIs; hologram PR #142 and source-only forward publisher #143 merged. |
| [SZL Khipu](https://github.com/szl-holdings/szl-khipu) | `e146cc32756ea9dbb9973a84ea667ec9880d172e` | Organ integrity reference; computed pass is not a signed proof of operational cross-system inference. |
| [SZL OTel Mesh](https://github.com/szl-holdings/szl-otel-mesh) | `172f52ecfc2cc7babac78bffde79517b38fcdb42` | Canonical existing observability lane; do not introduce another parallel telemetry authority. |
| [Platform](https://github.com/szl-holdings/platform) | `8c1fc5b9b06385c3639bcf0bd297e944c14cd797` | Existing release/admission controls. |
| [Killinchu](https://github.com/szl-holdings/killinchu) | `c753836384b560ac81eb76ca618f2e304618a326` | Canonical defense/maritime product; never promote simulation to actuation. |

**Observed before this proposal:** Read-only GET `https://a-11-oy.com/api/a11oy/v1/ayllu/second-brain` returned built retrieval memory but `ready_for_grounded_navigation=false`, `served_model=null`, `exact_tag_observed=false`, `artifact_binding=UNBOUND`. `https://szlholdings-szl-router-control.hf.space/readyz/inference` returned 503 (not configured). `https://szlholdings-anatomy.hf.space/api/anatomy/v1/holographic-v7` and `/api/anatomy/v1/frontier/status` exposed coherent read-only source/review handles, not browser WebGL or signed inference. Statuses may change after observation and must be rechecked before release.

## Organ zoom-in: public leader pattern → SZL-owned adaptation

| Organ/system | Relevant upstream primary sources | Already present | Missing qualification and smallest next test | Source owner |
| --- | --- | --- | --- | --- |
| **YACHAY / memory and research** | [Graphiti temporal context](https://github.com/getzep/graphiti), [Mem0 memory layer](https://github.com/mem0ai/mem0), [GraphRAG](https://microsoft.github.io/graphrag/) | Second Brain public handles and content digests, frontier candidates review-gated | Expiring/superseded source versions, tenant/citation rights, historical fact replay; compare current lexical/RRF baseline to one temporal-filter ablation with held-out stale-source and citation tests. No private graph hydration. | `szl-second-brain` |
| **WILLAY / conscience and policy** | [OPA policies](https://www.openpolicyagent.org/docs), [Cedar authorization](https://docs.aws.amazon.com/verifiedpermissions/) | Declared classifier catalog and A11oy deny-by-default gates | A catalog GET does **not** show an executed refusal, evaluated tenant context, or cryptographic signature. Exercise existing policy-owner negative cases; keep human approval, not a second authorization engine. | `a11oy`, Hatun |
| **YAWAR / sovereign circulation** | [vLLM](https://github.com/vllm-project/vllm), [SGLang](https://github.com/sgl-project/sglang), [llama.cpp](https://github.com/ggml-org/llama.cpp) | Mesh inventory, default-deny router, local open-weight models | Hosted `khipu:latest` identity, immutable manifest + weight hashes, authenticated 443 ingress, scoped model license, real completion and independently verified signed turn. Compare engines only after model/hardware/rights qualification; never expose raw daemon listeners. | `szl-router` + `a11oy`, #3776 |
| **Khipu / receipts and provenance** | [SLSA Verifier](https://github.com/slsa-framework/verifier), [Sigstore](https://www.sigstore.dev/) | Hash-chain metadata and offline receipt-verifier UI | Count, digest, or HTTP 200 cannot certify a signed outcome. Establish source/artifact/signer identity, DSSE PAE verification, key provenance, chain continuity, freshness and negative replay before status becomes VERIFIED. | `a11oy-net`, `szl-router`, A11oy receipt owner |
| **Heart / formal invariants** | [Lean4](https://lean-lang.org/), [Mathlib](https://leanprover-community.github.io/mathlib4_docs/) | Eight locked-proven formulas and explicit `Conjecture 1` | Per-symbol runtime refinement with exact Lean statement + premises + counterexamples; no success if remaining `sorry`, assumed axiom or conditional result is presented as general proof. | `lutar-lean`, `szl-formulas` |
| **OTel / nervous system** | [OpenTelemetry service conventions](https://opentelemetry.io/docs/specs/semconv/resource/service/), [Grafana Tempo service graphs](https://grafana.com/docs/grafana/latest/datasources/tempo/service-graph/), [Google SRE golden signals](https://sre.google/sre-book/monitoring-distributed-systems/) | OTel/mesh source owner and various service health endpoints | Real source-attributed trace spans, latency/errors/traffic/saturation, sample ratio and incident correlation; distinguish in-process-only observations from cross-Space tracing. Preserve privacy, do not pretend missing spans are zero-error traffic. | `szl-otel-mesh` + Platform |
| **Sense + normalize / vertical connectors** | [OpenTelemetry semantic conventions](https://opentelemetry.io/docs/concepts/semantic-conventions/), official government public APIs | Six verticals with bounded official-source connector contracts | Capture source URL, rights, time, normalization identity, source code revision and absent denominator per reading. Missing, paid, stale or AUTH_REQUIRED source stays UNAVAILABLE, never estimated as measured. | `vertical-services` per connector |
| **Decision / hands and replay** | [Temporal durable execution](https://docs.temporal.io/durable-execution) | A11oy/Hatun human-gated action admission and receipt review | Idempotency and resume-after-crash backed by a durable event history; replay must not rerun effects or bypass source/tenant approval. Do not install Temporal as a second control plane just because it is a leader. | A11oy/Hatun, `platform` |
| **Visual cortex / 3D body** | [Three.js WebGPU fallback](https://threejs.org/manual/pages/webgpurenderer), [Three.js WebGL renderer](https://threejs.org/docs/pages/WebGLRenderer), [W3C status role](https://www.w3.org/WAI/WCAG22/Techniques/aria/ARIA22) | Native Anatomy Holo, current source coherence #135, accessible optional-feed fallback #133 | Distinct feed/renderer/runtime states; repeatable desktop + narrow + keyboard + screen-reader + WebGL off/context lost tests. Existing [Anatomy #136](https://github.com/szl-holdings/anatomy/pull/136) owns live-body WebGL-denied repair; do not duplicate or merge over it. | `anatomy` |
| **Release immune system / delivery** | [SLSA verifier](https://github.com/slsa-framework/verifier), [Google SRE release monitoring](https://sre.google/workbook/canarying-releases/) | Protected GitHub main, workflow checks, guarded HF publisher | Verify per-file GH/HF/runtime byte parity, signer/expiry, auth-access and real browser probe; canary and rollback in approved window. No self-approval or silent security policy changes. | `platform` and each product owner |

## Vertical zoom-out: the body must not confuse domains with execution authority

| Vertical | Established external reference | Evidence-qualified next capability | Non-negotiable restriction |
| --- | --- | --- | --- |
| **PURIQ Finance** | [QuantConnect LEAN research/backtest engine](https://www.quantconnect.com/docs/v2/lean-engine/getting-started), [SEC EDGAR](https://www.sec.gov/edgar/sec-api-documentation) | Exact dated filing → formula → paper-only result → inspectable assumption and backtest receipt | No live trade or broker credentials from an Anatomy visualization |
| **Terra / real estate** | [PostGIS](https://postgis.net/docs/), [NYC PLUTO](https://www.nyc.gov/site/planning/data-maps/open-data/dwn-pluto-mappluto.page) | Public parcel geometry linked to versioned source/coverage and modeled estimates | MLS/property rights, real occupancy and appraisals remain unavailable without sources |
| **PRISM Counsel** | [Federal Register API](https://www.federalregister.gov/developers/documentation/api/v1), [CourtListener](https://www.courtlistener.com/api/) | Explain a citation with source, date, jurisdiction and uncertainty | No fake docket coverage or claim to provide legal representation |
| **Lyte / observability** | [OpenTelemetry](https://opentelemetry.io/), [Grafana Tempo](https://grafana.com/docs/tempo/latest/) | Trace-to-incident/owner repair map with sampled-data declarations | A health 200 does not establish customer SLO or cross-Space tracing |
| **Killinchu / maritime and defense** | [CISA KEV](https://www.cisa.gov/known-exploited-vulnerabilities-catalog), official maritime metadata | Read-only risk and simulation provenance with human-control boundary | No physical actuation, targeting, or simulated-to-live promotion |
| **Sentra / governance** | [OPA](https://www.openpolicyagent.org/docs), [Cedar](https://www.cedarpolicy.com/) | Auditable deny cases and contextual policy tests per tenant | No public inspector can grant execution authority |

## Implementation in this PR: one actual source-only repair

**Before:** `v5_organs.js` showed "LIVE" in three organ panels after successful JSON fetches even when meaningful inference evidence was missing, painted a continuing animated receipt pulse, treated truthy strings as node `live`, and labeled an unverified hash-chain count as a signed receipt. The sovereign-stack overlay similarly used a reported count as a green inference/receipt badge. The existing Holo #133 / #135 and live-body #136 changes do not own this separate v5 panel.

**After (candidate):** Pure, bounded `meshObservation` and `ledgerObservation` classifiers require typed counts and consistent node booleans; invalid/conflicting reports fail closed. Valid observations remain **SOURCE-REPORTED**, never inference-ready or signature-verified. The WILLAY catalog is labeled a catalog, not an executed signed refusal. The ledger source count uses `textContent` and an accessible status region rather than HTML injection; its unverified red pulse is disabled. The stack layers explicitly state SCHEMATIC / SOURCE-REPORTED. No new endpoint, network origin, credential, SDK, model, daemon, training job, publisher, scheduler or security exception.

### Falsifiable acceptance sequence

1. **Local unit:** non-object, missing, negative, booleans-as-counts, count > total, contradictory node states, oversized mesh, invalid hash-label, zero-denominator ledger and empty data must never produce green or verified status. Content from upstream is inert text in the new ledger HUD.
2. **Local regression:** all existing Node contract suites pass; Python transport/security suites run when declared dependencies are available. A failed environment setup is UNTESTED, not a passed suite.
3. **CI / review:** exact PR-head CodeQL, Trivy, Container and Doctrine required contexts must be green; independent source-owner review is required. No self-merge.
4. **Production admission separate:** authorized Anatomy publisher, immutable HF source/image and changed asset hash, browser enabled/disabled/context-lost 3D plus text alternative, non-browser API readback and source staleness. A11oy hosted Khipu #3776 must be separately closed on an independently signed real turn.
5. **Next original SZL experiment — proof-conditioned pulse:** a visual pulse corresponds to an authorized, source-identified, fresh, independently verified *specific event*, never an aggregate count. An absent proof makes a static amber handle. Compare false-positive/false-negative admissions, stale-source leakage, citation integrity and p95 browser rendering with explicit denominators; only claim improvement after paired held-out measurement.

State dimensions should be represented as a vector, **not one green badge**:
`(source_reachability, source_readiness, source_revision, observation_freshness, model_artifact_identity, signing_verification, runtime_admission, browser_renderer)`.
A position without evidence is `UNAVAILABLE` or `UNVERIFIED`; "LIVE" is reserved for a verified claim **of that precise scope**. The presence of an independent proof receipt for one event cannot certify an entire organ or product.

## Peer-review disclosure

Two local models were independently invoked with public-only facts on authorized BETTERWITHAGE: `kimi-estate-ops:latest` and `mistral-nemo:12b`. Kimi's returned text was repetitive and unusable, so it is **not counted as a valid design review**. Mistral suggested conditional source checks, but its draft compared a claimed signer object to another supplied field—this is **not independent cryptographic verification** and was rejected. The actual implementation above is the source-owned synthesis with deterministic tests, **not model-generated evidence of correctness**. Independent human review remains mandatory.

## Next eight unperformed engineering passes

- **P0:** A11oy/Router #3776 exact owned model/artifact/DSSE admission, approved secure ingress, immutable source parity. No inference in this PR.
- **P0:** Finish review of draft Anatomy #136 and separately prove authorized WebGL-disabled fallback and main-to-HF publication, preserving its ownership.
- **P1:** Convert source-reported v5 source timestamps into typed freshness observations only where the upstream contract supplies authentic observed/expiry basis; do not invent client-time freshness.
- **P1:** Add a read-only operational exemplar link from an actually recorded span/receipt to a renderer organ; no new broker or fake real-time stream.
- **P1:** Pre-register memory/retrieval temporal supersession experiment in Second Brain #102 against a rights-cleared held-out corpus.
- **P2:** Offline OPA/Cedar comparison for existing WILLAY rules with adversarial tenancy/decision fixtures; preserve SZL admission owner.
- **P2:** Equal hardware/weights inference-serving benchmarks after owner GPU/model/license/spend approval; no model generation in this pass.
- **P2:** Per-vertical official-source freshness and rights scorecards, measured SLOs and accessibility/browser acceptance.

**Audit honesty:** this is a bounded survey plus one tested v5 implementation proposal. It is *not* ten completed loops, complete upstream licensing due diligence, a real signed inference recovery, a production renderer proof, an authorization to train, or a production deployment.
