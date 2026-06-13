# SCREENSHOT_NOTES — live body view (`live-body.html`)

No headless browser is available in this lane, so the page was verified by
**static parse + a Node functional test of the engine logic** (see "How it was
verified" below) rather than a rendered screenshot. These notes describe the
exact layout a reviewer should see in an HF **deploy preview** of the
`feat/anatomy-live-body-view` branch, so the visual result can be checked
against intent.

## Body layout (top → bottom)

```
┌───────────────────────────────────────────────────────────────────────────┐
│  SZL LIVING ANATOMY · LIVE BODY VIEW                  ┌─ GPU mind · posture ┐│
│  The agentic GPU MIND, inside its proven body         │ sovereign  [false]  ││
│  <one-paragraph intro + "← full 3D atlas" link>       │ backend    hf-router││
│                                                       │ mode       live     ││
│                                                       │ doctrine   v12       ││
│                                                       └─────────────────────┘│
│                                                                             │
│  [ ▶ Run proactive cycle ]  [ ↻ Refresh organ status ]  [ ⚡ energy: SAMPLE ]│
│                                                                             │
│  ┌── IMMUNE ⛨ ─ step 0 ──┐  ┌── BRAIN ✸ ─ step 1 ───┐  ┌── HEART ❤ step 3 ─┐│
│  │ Neyman-Pearson gates  │  │ PAC-Bayes McAllester  │  │ σ-algebra receipts ││
│  │ ● <status detail>     │  │ ● <status detail>     │  │ ● <status detail>  ││
│  │ <endpoint url>        │  │ <endpoint url>        │  │ <endpoint url>     ││
│  └───────────────────────┘  └───────────────────────┘  └────────────────────┘│
│  ┌── BLOOD 🜂 ─ step 4 ──┐  ┌── SKELETON ⊟ spine ──┐  ┌── NERVOUS ⌁ step 5 ┐│
│  │ DSSE Merkle provenance│  │ Lean kernel · Λ=Conj1 │  │ Shannon drift alarm ││
│  │ ● <status detail>     │  │ ● <status detail>     │  │ ● <status detail>  ││
│  └───────────────────────┘  └───────────────────────┘  └────────────────────┘│
│                                                                             │
│  <cycle log line — narrates immune→brain→heart→blood→nervous>               │
│  ┌─ honest by design ───────────────────────────────────────────────────┐  │
│  │ ● Λ = Conjecture 1   ● sovereign only from /code/healthz   ● SAMPLE … │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────┘
```

- **Six organ cards** in a responsive `auto-fit` grid (3-up on desktop, 1-up on
  mobile). Each card carries its colored accent bar, glyph, proven-formula line,
  agentic role, a **status dot + detail line**, and the real endpoint URL.
- The **GPU-mind posture** card sits top-right with the live `sovereign` badge.
- Organ colors reuse the existing `index.html` tokens: HEART `#ff5d8f`, BLOOD
  `#ff3b5c`, BRAIN `#7c5cff`, NERVOUS `#5ad1ff`, SKELETON/IMMUNE `#ffd166`.

## Status-dot states (honest)

- **live** (cyan dot, card border brightens): endpoint answered `2xx` with usable
  JSON; the detail line shows a short summary (e.g. "8 deny-by-default gates
  armed", "pac_bayes_mcallester present").
- **pending** (amber, breathing): mid-probe.
- **unreachable** (grey dot, dimmed text): network/CORS/timeout/non-JSON →
  reads `unreachable — <why> · honest empty-state`. **No green light is ever
  shown for an organ that did not answer.**

## What the proactive-cycle button does

Pressing **▶ Run proactive cycle** pulses the organs in the canonical order
**IMMUNE → BRAIN → HEART → BLOOD → NERVOUS** (SKELETON is the always-on spine and
is excluded from the cycle). Each pulse is a ~1s color flash + lift; the cycle
log narrates each phase and ends with *"reactive turns were never gated (they
always preempt)."* Respects `prefers-reduced-motion` (border highlight instead of
motion).

## Expected live state TODAY (honest)

At the time this was built:
- **GPU mind** (`/api/a11oy/code/healthz`): reachable → `sovereign: false`
  (router-served, `backend: hf-router`, `mode: live`, `doctrine: v12`). This is
  the **correct, honest** reading — it is NOT sovereign while a router serves,
  and the view says so plainly.
- **Honesty strip** (`/api/a11oy/v1/honest`): reachable → Λ = Conjecture 1,
  8 locked-proven, 749/14/163 @ `c7c0ba17`.
- **amaru / sentra organ endpoints**: their HF spaces currently return non-JSON
  (unrouted) → BRAIN/HEART/BLOOD/IMMUNE/SKELETON/NERVOUS honestly read
  **unreachable · honest empty-state**. When those spaces are routed the same
  page lights them green with no code change.

So a reviewer opening the deploy preview should expect: **mind posture + honesty
strip live; organ cards in honest unreachable states until amaru/sentra route.**
That is the doctrine floor working as intended, not a bug.

## How it was verified (no headless browser)

- `node --check live-body.js` → PASS.
- Inline `<script type="module">` extracted from `live-body.html` →
  `node --check` PASS.
- HTML tag-balance lint (html/head/body/style/script/main/header/section/footer)
  → all balanced; DOCTYPE present.
- **Engine functional test** (mocked `fetch`, 14 assertions, all pass):
  - proactive cycle order is exactly `immune→brain→heart→blood→nervous`;
    skeleton excluded.
  - `summarize` tolerates real + empty/odd JSON shapes without throwing.
  - `probeOrgan` degrades to `unreachable` on network error and on non-JSON
    (HF 404 HTML), and reads `live` on real JSON.
  - `probeMind` sets `sovereign:true` **only** on the literal `true`, never on a
    truthy string, and reports `sovereign:false` when the mind is unreachable
    (the half-state is unrepresentable).

A rendered screenshot still requires an HF **deploy preview** of the branch —
flagged here for the reviewer.
