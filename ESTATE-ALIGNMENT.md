# SZL Holdings — Estate Alignment Registry

> Governed-AI estate, owner Stephen Lutar. This registry aligns the GitHub org szl-holdings with the HuggingFace org SZLHOLDINGS, Cloudflare Workers deployments, SaladCompute training infrastructure, and the PyPI publication pipeline.
> Updated: 2026-11-19. Maintained by the estate CTO lane (receipt-linked; see Integrity Doctrine below).

## Surfaces

| Surface | Identifier | State |
| --- | --- | --- |
| GitHub org | https://github.com/szl-holdings | 176+ public production repos with curated descriptions |
| HuggingFace org | https://huggingface.co/SZLHOLDINGS | ~415 public repos: models + datasets (publicization sweep 2026-11-19: 234 models + 5 datasets flipped public, 0 failures) |
| Cloudflare Workers | https://puzzle-frontier.stephenlutar2.workers.dev + https://puzzle-frontier-api.stephenlutar2.workers.dev | Live. Front-end proxies /api to the API worker; 436 certified items across 6 constraint-satisfaction banks |
| Inference gateway | inference.a-11-oy.com | Estate model-serving mirror |
| SaladCompute | organization alloyscape, 118 container groups | Training/eval fleet with rotation doctrine |
| PyPI | pipeline (trusted publishing) | Workflows staged; see Publications |

## Product families (public productions)

- **Constraint-satisfaction frontier**: certified puzzle banks (zebra, futoshiki, sudoku 12x12, killer 9x9) with fresh-seed contamination-free eval sizes; served live via puzzle-frontier.
- **The RING ladder**: salad-ring-ouro-l1..l134, a 134-repo continuous-improvement ladder with ring-bench certification receipts.
- **Flagship models**: salad-flagship54-v1/v2, flagship55-v1, pg54-* vertical variants (khipu, yachay, codex, hatun, lutar).
- **Khipu SDA (System of Double Accounting)**: governed-evidence math; khipu-sda-core package, heritage/scholar/structure corpora.
- **Verticals**: physics-tutor, world-science, clinical-abstention, quant, ancient-math, acoustic-governance, muhu-methodology, x402-protocol.
- **Nano / GGUF**: SZL-Khipu-1.5B-GGUF (5,500+ downloads).
- **Infrastructure**: szl-evidence-core, nexus, a11oy, hatun-mcp, szl-khipu, evidence-studio, szl-guardrail-receipt, szl-serve, szl-govsign, anatomy.

## Monetization

- x402 v2 payment challenges on /api/premium routes: network eip155:8453 (Base), USDC contract 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913.
- Default price X402_PRICE = 20000 (base units) = 0.02 USDC per premium call; payee set via worker secret X402_PAY_TO (estate USDC/Base address).
- The inference gateway mirrors the same payment protocol at inference.a-11-oy.com.
- Payee address confirmation and fund-flow reconciliation are owner-gated.

## Publications (PyPI)

Trusted-publishing pipeline. Packages pending publisher registration (owner-gated on pypi.org):

- szl-specdecode - speculative decoding
- khipu-sda-core - System of Double Accounting core
- szl-energy-mcp - energy attestation MCP
- szl-gov - governance primitives
- szl-abstention-frontier - abstention calibration
- szl-cram - constraint-reasoning augmentation

Publish workflows land per-repo once the owner registers each project as an OIDC trusted publisher (no tokens in CI).

## GitHub to HuggingFace alignment

- Naming convention: GitHub holds sources and tooling (szl-*); HuggingFace holds artifacts (models salad-* / SZL-*, datasets). Model cards cross-link their GitHub training repo; GitHub product READMEs cross-link their HF artifact.
- Artifacts without a MEASURE receipt ship as productions with explicit "MEASURE pending" markers, never as verdicts.

## Integrity Doctrine (what stays private and why)

Public by default, except where publication would contaminate measurement or leak operational secrets:

- Eval/heldout pools and measurement fabric: frontier-54-runs, frontier-55-runs, wave-logs receipts fabric, proving-ground-54h-mesh, model-eval-receipts, VGL probe pools.
- Unreceipted candidates and backups (*-candidate) - no MEASURE yet; publishing invites benchmark contamination.
- Raw telemetry, vault artifacts, state dirs.

That is ~29 of ~440 HF repos; every other repository is a public production. Contamination discipline trumps showcase; the showcase deliberately points at it.

## Chain of custody

Every lane operation lands a receipt in the estate receipts fabric and a dated entry in the estate decision ledger before it is reported. No exceptions.
