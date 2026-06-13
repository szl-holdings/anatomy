---
title: SZL Living Anatomy
emoji: 🫀
colorFrom: indigo
colorTo: pink
sdk: static
app_file: index.html
pinned: false
license: apache-2.0
---

# SZL Living Anatomy 🫀

> **Governed AI you can prove — as a living body.**
> A 3D, navigable map of the governed organism: its organs, how a single decision
> flows through them, and where each proof and conjecture honestly sits.

> **The living substrate · 5 systems · Λ heart · DSSE Khipu receipt bus · honest by design**

[![SLSA L1 honest (static viz)](https://img.shields.io/badge/SLSA-L1%20honest%20(static%20viz)-c9b787?style=flat-square)](https://github.com/szl-holdings/szl-uds-deployment)
[![doctrine-v11](https://img.shields.io/badge/doctrine-v11%20LOCKED-0B1F3A?style=flat-square)](https://github.com/szl-holdings/.github/tree/main/doctrine)
[![License](https://img.shields.io/badge/license-Apache--2.0-5fb3a3?style=flat-square)](https://github.com/szl-holdings/anatomy)
[![Λ Conjecture 1](https://img.shields.io/badge/%CE%9B-Conjecture%201-B79BD6?style=flat-square)](https://github.com/szl-holdings/lutar-lean/blob/main/BOUNTY.md)
[![Khipu Conjecture 2](https://img.shields.io/badge/Khipu%20BFT-Conjecture%202-B79BD6?style=flat-square)](https://github.com/szl-holdings/khipu-consensus)

The governed-AI organ substrate shared by **a11oy** (governed-AI command body) and
**killinchu** (maritime / drone C2 body): two bodies, one circulatory + nervous mesh,
with the Λ heart at the center.

## What's new in v4 — dissection tools

v4 **evolves** v3 (it does not replace it): the entire v3 engine, organs, formulas,
YAWAR receipt bus, GPD lens, and text fallback are preserved. Layered on top are
bench-grade dissection controls so the body is *easier to dissect*:

- **Dissection layer stack** — toggle + opacity-slide the conceptual layers
  (circulatory · nervous · organs · skeleton/Khipu · halos/glow); choices persist in `localStorage`.
- **Clip-plane scalpel** — a sliding X/Y/Z cross-section (`renderer.localClippingEnabled`)
  cuts the organism so you can see the interior, with a reset.
- **Explode view** — an eased 0→1 slider separates the organ groups radially for inspection.
- **Search / jump** — filter organs + formulas by name/id; selecting one flies the camera and opens its panel.
- **Always-on visibility HUD** — a compact overlay reading **honest** counts straight from
  `data.js` (`D.KERNEL`): locked-proven = 8, experimental tier, axioms 14, sorries 163,
  kernel `c7c0ba17`, Λ = Conjecture 1, Khipu BFT = Conjecture 2. Never hardcoded.
- **Focus mode** — fade the other organs when one is selected, to isolate it.
- **yarqa flow compartments (CFD) — additive, off by default** — an *engineering-method*
  layer in the dissection dock that runs a clean-room plug-flow compartmentalization
  (`yarqa`) over the **existing** circulatory / YAWAR flow sampled from `data.js`, draws
  the compartments as a toggleable read-only overlay, and emits a reproducible integrity
  receipt digest. It is **labeled CFD, not a locked theorem, and is never counted among
  the locked 8** — `data.js` stays the single source of truth and the locked-proven count
  is unchanged at 8.
- **Accessibility + mobile** — every new control is keyboard-reachable and ARIA-labeled,
  laid out so it never overlaps the existing HUD/panel, and it respects `prefers-reduced-motion`.

Still sovereign: ONLY the vendored `lib/three.min.js` (THREE r160 global) — zero runtime
CDN, no npm, no build step. The site stays a static, offline-capable bundle.

## What you'll see

Walk the organism in 3D and watch a real decision propagate: a request enters, the
**YUYAY** gate scores it on 13 conjunctive axes (deny-by-default), the verdict is sealed
into a **DSSE Khipu receipt** on the **YAWAR** append-only bus, and the **YACHAY** read-only
cortex supplies reasoning without ever holding write authority. Each organ is labeled with
its honest proof state — proven, conditional, or open conjecture — so nothing is dressed up
as more certain than it is.

**Five systems:** HEART · YUYAY (13-axis conjunctive critique gate, emits Λ-signed receipt) ·
CIRCULATORY/BLOOD · YAWAR (append-only SHA-256 receipt bus) ·
BRAIN · YACHAY (read-only reasoning cortex) ·
NERVOUS · OTel/VSP · SKELETON · 12 service repos.

**Honest doctrine:** locked-proven = 8 {F1, F4, F7, F11, F12, F18, F19, F22} @ kernel `c7c0ba17`
(the no-axiom theorem `locked_count_eight`; F4 Khipu DAG acyclicity, F7 Chaski FIFO ordering,
F22 Khipu emit append-only monotonicity) ·
Λ unconditional uniqueness = Conjecture 1 (machine-checked FALSE); conditional Λ axiom-free PROVEN ·
Khipu BFT safety = Conjecture 2, with the Wave23 conditional agreement theorem
(`khipu_quorum_safety_conditional`, n≥3f+1 + honest non-equivocation, axiom-clean) ·
~185 experimental CI-green · trust never 100% · no AGI.

**Supply-chain posture:** this Space is a static visualization (`sdk: static`) — SLSA L1 honest.
The product images it depicts (**a11oy**, **killinchu**) are **SLSA L1 honest · L2 build-attested**
(container provenance via attest-build-provenance, Sigstore keyless, Rekor-anchored; L3 roadmap) —
see [szl-uds-deployment](https://github.com/szl-holdings/szl-uds-deployment).

> **Non-affiliation.** SZL Holdings' use of "UDS" references Defense Unicorns' Unified Defense
> Stack (USPTO Serial 99831122); SZL Holdings is not affiliated with Defense Unicorns. No
> production ATO is claimed.

## Live body view — `live-body.html`

A new, **additive** page (`live-body.html` + `live-body.js`, linked from the
title bar of the 3D atlas) turns the anatomy into the **LIVE BODY VIEW of the
agentic GPU mind**. It is a standalone static page — same vendored-free,
no-build, no-CDN posture as `index.html` — reachable directly at
`…static.hf.space/live-body.html`. It does **not** modify the 3D engine (`app.js`,
`data.js`), so there are no breaking changes.

Each of the six organs reads its **real endpoint** and lights up with its honest
live status; press **Run proactive cycle** to watch the GPU mind act
(IMMUNE → BRAIN → run → HEART/BLOOD → NERVOUS), pulsing each organ in turn:

| Organ | Proven formula (round9) | Live endpoint read |
|---|---|---|
| BRAIN | BrainBeliefUpdate (PAC-Bayes McAllester) | amaru `/api/amaru/v1/formulas` |
| HEART | HeartReceiptSigma (σ-algebra receipt bus) | amaru `/api/amaru/receipts` |
| BLOOD | BloodDSSEMerkle (Cardano-anchored DSSE) | sentra `/api/sentra/khipu/ledger` |
| IMMUNE | ImmuneNeymanPearson (deny-by-default gates) | sentra `/api/sentra/v1/gates` |
| SKELETON | SkeletonLambdaSpine (Lean kernel; Λ=Conj 1) | amaru `/api/amaru/v1/math/lean/theorems` |
| NERVOUS | NervousShannonAlarm (Λ-signed OTEL drift) | amaru `/api/amaru/overwatch/snapshot` |

The **GPU-mind posture** card reads a11oy `/api/a11oy/code/healthz`
(`sovereign` / `backend` / `mode`); the honesty strip reads the doctrine lock
live from a11oy `/api/a11oy/v1/honest`.

**Honest by design (doctrine v11/v12):**
- `sovereign:true` is shown **only** when `/code/healthz` reports the literal
  `true` — never synthesized from a truthy value. If the mind is unreachable the
  card shows `sovereign: false`. The half-state (banner sovereign while a router
  serves) is the one outcome the view will never render.
- Energy / joules are labeled **SAMPLE** until a real meter is wired.
- **Λ is shown as Conjecture 1** (the skeleton's killer formula is intentionally
  a conjecture), pulled live, never hardcoded as proven.
- An unreachable endpoint degrades to an honest `unreachable — … · honest
  empty-state`; no green light is ever fabricated for an organ that did not
  answer. (Today amaru/sentra spaces may be unrouted → those organs honestly
  read unreachable; a11oy + the mind posture read live.)
- Read-only, sends no key, open-weight only.

See `SCREENSHOT_NOTES.md` for the body layout and what a reviewer should see in a
deploy preview.

## Verify it yourself

The organism is a map, not the source of truth — every claim it draws is checkable against the
live products it depicts:

```bash
# Confirm the live doctrine posture the heart reports
curl -s https://szlholdings-a11oy.hf.space/api/a11oy/v1/honest | jq .kernel_commit   # => "c7c0ba17"
# Pull a signed receipt from the edge organ and verify it offline
curl -s https://szlholdings-killinchu.hf.space/cosign.pub -o cosign.pub
```

Read the thesis → [szl-papers](https://github.com/szl-holdings/szl-papers) ·
run the kernel → [lutar-lean](https://github.com/szl-holdings/lutar-lean).

---

Canonical source mirror: `szl-holdings/anatomy` (GitHub) ↔ `SZLHOLDINGS/anatomy` (HF Space) · **[a11oy.net](https://a11oy.net)**

<sub>v4 dissection tools (evolves v3) · Doctrine v11 LOCKED · 749/14/163 · kernel `c7c0ba17` · 8 locked-proven + experimental CI-green tier · Λ = Conjecture 1 · Khipu Conjecture 2 open · SLSA L1 honest (static viz) · Apache-2.0</sub>
