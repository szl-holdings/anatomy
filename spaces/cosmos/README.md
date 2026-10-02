---
title: SZL Cosmos
emoji: 🌌
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: true
license: mit
short_description: Holographic map of the SZL sovereign substrate
tags:
  - governance
  - visualization
  - threejs
  - receipts
  - honest-by-design
  - szl-holdings
---


<div align="center">
<p>

[![governed](https://img.shields.io/badge/governed-SZL%20Holdings-3af4c8?style=flat-square)](https://huggingface.co/SZLHOLDINGS)
[![Λ](https://img.shields.io/badge/Λ-Conjecture%201%20advisory-d7b96b?style=flat-square)](https://a-11-oy.com)
[![license](https://img.shields.io/badge/license-mit-7e8aa3?style=flat-square)](https://huggingface.co/spaces/betterwithage/cosmos)

</p>
</div>
<!-- SZL-ESTATE-CARD:v2:START -->
<p align="center"><a href="https://a-11-oy.com/"><img src="https://huggingface.co/spaces/SZLHOLDINGS/README/resolve/main/assets/estate-banner-v2.svg" alt="SZL Holdings — governed, receipted, verifiable" width="100%"></a></p>
<p align="center">
  <a href="https://github.com/szl-holdings/.github/tree/main/doctrine"><img src="https://img.shields.io/badge/doctrine-v11%20LOCKED-0B1F3A?style=flat-square" alt="doctrine v11"></a>
  <a href="https://a-11-oy.com/"><img src="https://img.shields.io/badge/evidence%20wall-LIVE%20%C2%B7%20verify%20in%20browser-3AF4C8?style=flat-square" alt="live evidence wall"></a>
  <a href="https://huggingface.co/datasets/SZLHOLDINGS/szl-lake"><img src="https://img.shields.io/badge/szl--lake-offline%20verifiable-C9B787?style=flat-square" alt="szl-lake offline verifiable"></a>
  <a href="https://huggingface.co/spaces/SZLHOLDINGS/holographic"><img src="https://img.shields.io/badge/estate%20map-holographic-5B8DEE?style=flat-square" alt="holographic estate map"></a>
</p>
<p align="center"><sub>Part of the <a href="https://huggingface.co/SZLHOLDINGS">SZL Holdings</a> governed estate — claims are designed to carry checkable receipts. Verification proves integrity &amp; origin, never accuracy or performance.</sub></p>
<!-- SZL-ESTATE-CARD:v2:END -->

# SZL Cosmos · Hanan Pacha

**One holographic destination** for the whole SZL Holdings sovereign governed-AI
substrate. This Space **consolidates three former Spaces into one**:

- **org-map** → the *org constellation* layer (the live SZL Holdings Hugging Face
  Spaces, rendered as holographic nodes governed by the brain-sun);
- **cathedral** → the **a11oy brain-sun**, its three internal capabilities, and
  the **killinchu** field node;
- **khipu-constellation** → the live **Khipu receipt constellation** with Λ-coloured
  cord arcs (the receipt DAG).

*Hanan Pacha* is the celestial upper world of Andean cosmology — a fitting name for
the substrate seen from above, projected as light.

## What you see

- **a11oy brain-sun** (core) — the governance substrate; breathes with live `/healthz`.
- **Reasoning / Policy / Operator** — a11oy-internal capabilities orbiting the core.
- **Org constellation** — every live SZL Space as a holographic node, corded to the
  brain-sun. Click one to fly to it and open the real Space.
- **killinchu** — the deployed field node (drones & vessels; effectors *simulated*).
- **Khipu receipt stars** — the receipt DAG; stars/cords coloured by Λ verdict,
  pulsing when a new receipt streams in.

## Honesty (doctrine v11)

- **Λ = Conjecture 1** (advisory, *not* a theorem, *not* "proven trust").
- **Khipu BFT = Conjecture 2**. **Locked-proven kernel = exactly 8**
  `{F1,F4,F7,F11,F12,F18,F19,F22}` @ `c7c0ba17` (749 decl / 14 axioms / 163 sorries).
- **Trust = conformal** (never 100%, *not* Hoeffding). **SLSA L1 honest / L2 roadmap.**
- The **org constellation is a catalog snapshot** (honest — *not* runtime-live).
  Live health is polled only for the CORS-open endpoints (**a11oy**, **killinchu**).
  Nothing on this page is fabricated.

## Sovereign & cutting-edge

- **Three.js r160 (MIT)** — vendored under `/vendor`, **zero CDN at runtime**,
  including the full **postprocessing bloom chain** (`EffectComposer` +
  `UnrealBloomPass` + `OutputPass`, all MIT, vendored).
- **Holographic shader material**: fresnel edge glow + iridescent hue shift +
  projection scanlines + subtle flicker.
- Robust non-WebGL fallback: if the browser lacks WebGL the page degrades to honest
  live links instead of a dead spinner.

Served by a hardened static server (`server.py`) with CSP / HSTS / nosniff headers.

## Links

- a11oy · command platform — https://szlholdings-a11oy.hf.space
- killinchu · field node — https://szlholdings-killinchu.hf.space
- all SZL Spaces — https://huggingface.co/SZLHOLDINGS
- github · szl-holdings — https://github.com/szl-holdings

---

## SZL Estate

Part of the **SZL Holdings** governed-AI estate — *governed AI you can prove*: every decision carries a signed, checkable receipt.

- **Flagship:** [a11oy command console → a-11-oy.com](https://a-11-oy.com)
- **Orgs:** [GitHub · szl-holdings](https://github.com/szl-holdings) · [Hugging Face · SZLHOLDINGS](https://huggingface.co/SZLHOLDINGS)

## Deployment-source attestation

`GET /.well-known/szl-source.json` reports a Hugging Face revision observation and checks the mounted payload against the publisher-generated `COSMOS_SOURCE_BINDING.json`. Matching bytes report `SOURCE_BOUND_LOCAL_BYTES` and identify the canonical `szl-holdings/anatomy` source commit; missing, malformed, or mismatched bindings remain `UNKNOWN_SOURCE_RELATION`. The binding is unsigned structural evidence: GitHub parity and reproducible builds remain explicitly `NOT_CLAIMED`. The API fallback observes Hub head, which does not establish the running revision. Publication separately requires the provider's RUNNING revision to match the immutable, byte-verified published revision.
- **Related Spaces:** [◇ holographic](https://huggingface.co/spaces/SZLHOLDINGS/holographic) · [🫀 anatomy](https://huggingface.co/spaces/SZLHOLDINGS/anatomy) · [🦅 killinchu](https://huggingface.co/spaces/SZLHOLDINGS/killinchu)

**Status:** responding as of 2026-07-09 (HF Space root probe, this session).

<sub>Doctrine v11 · Λ = Conjecture 1 (advisory — never "green"/theorem; open) · honest by design · public data only.</sub>

---

<div align="center">

**[🛡️ SZLHOLDINGS on Hugging Face →](https://huggingface.co/SZLHOLDINGS)**   ·   **[a-11-oy.com →](https://a-11-oy.com)**   ·   **[Estate hub — live →](https://szlholdings-szl-estate-live.static.hf.space)**

### Governed AI you can prove.

<sub>SLSA: L1 honest · L2 attested · L3 roadmap. Λ = Conjecture 1 (advisory, never a theorem). Trust ceiling 0.97 — never 100%. Labels honest by default: MEASURED / REPORTED / MODELED / HEURISTIC / UNKNOWN / UNAVAILABLE. locked-proven = exactly 8 {F1,F4,F7,F11,F12,F18,F19,F22}.</sub>

</div>


## Public catalog (2026-09-08)

`GET /api/catalog` refreshes anonymous public metadata for SZLHOLDINGS and betterwithage Spaces, models, and datasets. The holographic catalog now uses this endpoint instead of the bundled historical `data/org_nodes.json`. The catalog drawer works independently of WebGL and filters the hologram by search, owner, and repository type. Spaces are selected initially; models and datasets are available through the type selector.

Each of the six source streams reports its observation timestamp, age, source URL, and FRESH / STALE / PARTIAL / UNAVAILABLE state. Nodes include Hub revision and provider runtime revision when reported. RUNNING is a Hugging Face provider stage, not verification of application health, inference, training, or formal proofs. Catalog lines indicate membership only. Historical doctrine/capability text elsewhere on the page is not reverified by this endpoint.

The standard-library backend sends no Authorization header and never reads HF credentials. Only explicitly public records in the two fixed namespaces are included. Refreshes use a shared 120-second cache, six bounded workers, an eight-second upstream socket timeout, a 2 MB response limit, and at most 500 entries per stream. Truncation is labelled PARTIAL. Initial reads return immediately with UNAVAILABLE/refreshing; failed refreshes retain prior observations as STALE with sanitized errors. The cache retries after 120 seconds and is refreshed on demand. No inference or paid compute is invoked.

Run locally with `python server.py` (port 7860; override with `PORT`). Validate with `python -m unittest discover -s tests -v`. Browser catalog polls every 30 seconds, or every two seconds while its initial server refresh is in progress.
