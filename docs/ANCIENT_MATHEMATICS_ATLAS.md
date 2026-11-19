# Ancient Mathematics in Living Anatomy — source-bound research atlas

**Scope:** read-only, fixed-example scholarship and audited references.
**Admission:** original Python arithmetic code, ten curated metadata records, a
separate neural-quant tab and an independently checked deployment contract.
This is **not** a training corpus, source of mathematical proof authority,
decipherment service, cultural inference engine, or production deploy receipt.

## Primary sources and separately attributable traditions

The following historical methods and numerical conventions are documented by
external reference works. The algebraic notation is **modern** and the fixed
examples use original explanatory text rather than copied manuscript pages.
Record IDs correspond exactly to `ancient_math_atlas.py`.

| Tradition and artifact | Modern notation / exact illustrative result | Historical qualification |
|---|---|---|
| Ancient Egypt — Rhind Mathematical Papyrus, 2/n table | 2/7 = 1/4 + 1/28 | Exact rational arithmetic; not a new transcription of an ancient papyrus |
| Ancient Egypt — Rhind doubling | 41 × 59 = (32+8+1)×59 = 2419 | Doubling is historical; parentheses and binary interpretation are modern |
| Ancient Egypt — Moscow Mathematical Papyrus problem 14 | h(a²+ab+b²)/3; (a,b,h)=(2,4,6) → 56 | Square-pyramid frustum only; finite calculation, not historical proof replay |
| Ancient Greece — Euclid, Elements I.47 | Right angle: a² + b² = c²; 3² + 4² = 5² | One example does not reproduce Euclid's geometrical demonstration |
| Ancient Greece — Euclid, Elements VII.2 | gcd(1071,462)=21 | Modern modulo notation corresponds to greatest-common-measure algorithm |
| Maya codices — Dresden Codex Venus tables | 5×584 = 8×365 = 2920 days | Calendrical approximation; not exact physical orbital periods |
| Maya calendar — Long Count numeration | 144000b + 7200k + 360t + 20u + kin | Mixed radix; specific synthetic 1.2.3.4.5 gives 159565 counted days |
| Andean khipu — known decimal knot registers | N=Σ d_i×10^i; synthetic (units,tens,hundreds)=(5,4,3) → 345 | Unknown/broken physical cords cannot be silently mapped to zero |
| Andean khipu — some documented aggregate relations | T ?= Σ x_i; synthetic 12+5+8=25 | A numeric match does not establish the meaning of an archaeological cord |
| **SZL modern research** — KCRC-v1 | W_r(x)=Σ x_i r^i mod (2^61−1); x=(12,5,8), r=7 → 439 | Polynomial fingerprints are **modern**. Not ancient khipu cryptography |

In particular, **Maya codices and Andean khipus are different traditions and
media**. Neither is a precursor of a modern digital authentication protocol
merely because its structures can be represented mathematically. Research
must preserve the authority of original scholars, stewards and communities.

## Historical scholarship and corpus boundaries

- [Rhind Papyrus and Egyptian mathematical sources — University of St Andrews](https://mathshistory.st-andrews.ac.uk/HistTopics/Egyptian_papyri/)
- [Egyptian mathematics — Open University](https://www.open.edu/openlearn/science-maths-technology/mathematics-statistics/egyptian-mathematics/content-section-1.1.1)
- [Moscow Mathematical Papyrus problem 14 — Wolfram MathWorld](https://mathworld.wolfram.com/MoscowMathematicalPapyrus.html)
- [Elements I.47 — Euclid source translation and diagram](https://www.euclids-elements.org/elements/books/bookI/propositions/propI47/)
- [Elements VII.2 — greatest common measure](https://www.euclids-elements.org/elements/books/bookVII/propositions/)
- [Dresden Maya Codex — Saxon State and University Library Dresden](https://www.slub-dresden.de/en/explore/manuscripts/the-dresden-maya-codex/content)
- [Maya Long Count calendar — Smithsonian National Museum of the American Indian](https://maya.nmai.si.edu/calendar/maya-calendar-converter)
- [Inka khipu numeric records — NIST](https://www.nist.gov/nist-museum/standardizing-empire)
- [Open Khipu Repository — primary corpus and rights](https://github.com/khipulab/open-khipu-repository)
- [SZL KCRC research and explicit synthetic examples](https://github.com/szl-holdings/szl-khipu/blob/5a6a3843008906051e7b3289767078cd04d26ac3/docs/KHIPU_NUMERICAL_INSPIRATION.md)

External references are **bibliographic pointers, not imported datasets**. A
source URL or Open Khipu identifier is not automatic permission to ingest or
train on collection text, photos, archaeological records, or community knowledge.
Any later data integration needs explicit rights review, community consultation,
data-steward approval, a source revision, and an independently reproducible
citation. This change performs no network scrape or new manuscript ingestion.

## SZL proof, paper, and runtime authority — three distinct planes

- [`szl-papers` source matrix](https://github.com/szl-holdings/szl-papers/blob/39c228dc3a29c6cfd831d43be6a8531e718692ac/MATH_RUNTIME_EXECUTION_MATRIX.md)
  records the **existing** eight-locked-formula registry and rules for connecting
  manuscripts, executable tests, Lean proof snapshots and runtime observations.
- [`szl-khipu` modern numerical interpretation](https://github.com/szl-holdings/szl-khipu/blob/5a6a3843008906051e7b3289767078cd04d26ac3/docs/KHIPU_NUMERICAL_INSPIRATION.md)
  describes optional modern KCRC arithmetic. It does not claim an ancient
  probabilistic verifier.
- [`lutar-lean` Theorem U](https://github.com/szl-holdings/lutar-lean/blob/80e35f859801d80fce7cf81e4d9b0c8bdf91cfea/Lutar/Uniqueness/TheoremU.lean)
  is a **conditional** uniqueness theorem; the original unconditional Lambda
  Conjecture 1 is disproved as stated. Unconditional Khipu BFT remains open.
- `szl-holdings/anatomy` is a **read-only presenter**, not a new independent
  theorem registry or a permission-granting agent. The ten arithmetic examples
  do not change `F1,F4,F7,F11,F12,F18,F19,F22`.

## Runtime and publisher contract

`GET /api/anatomy/v1/brain/ancient-math` returns exactly ten curated
metadata entries, each its historical source, original statement of limits,
modern notation, an independently calculated example witness, and a bounded
catalog SHA-256. It performs no provider fetch, external command, training,
executable research notebook, state change, or HTML rendering.

The existing `Neural Quant v7 → Ancient Math` tab fetches only this same-origin
endpoint, renders all fields as text nodes, and links only to explicitly
allowlisted HTTPS research hosts. On missing or mismatched evidence it shows
**UNAVAILABLE**; it never substitutes a claimed proof or ancient decipherment.
No new browser origin, remote dependency, CDNs, or external-script allowance
is required.

The `hf-sync` publisher must include `ancient_math_atlas.py` in the exactly
bound source bundle and independently read back the served endpoint, catalog
digest, pinned references and absence of consequential authority. A successful
source test or GitHub merge **does not** prove that HF has deployed the feature.
Deployment/source parity and maintenance-window admission remain separate.

## Reproducibility and trust boundaries

From the checked-out Anatomy repository:

```bash
python -B -m unittest discover -s tests -p 'test_ancient_math_atlas.py' -v
python -B -m py_compile ancient_math_atlas.py living_runtime.py scripts/sync_hf_creator_profile.py
node --check neural-quant-v7.js
```

A passing suite qualifies only the ten selected calculations and source
packaging. It does not validate the content of historical manuscripts, a live
external citation, the current protected-main status of other repositories,
signature custody, deployed runtime correctness, or production readiness.
All cited SZL Git revisions are **pinned declarations**, not cryptographically
verified current head identities. Unknown data remain **UNAVAILABLE**.
