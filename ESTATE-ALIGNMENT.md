# SZL Holdings — Estate Alignment Registry

> Governed-AI estate, owner Stephen Lutar. This registry aligns the GitHub org szl-holdings with the HuggingFace org SZLHOLDINGS, Cloudflare deployments, SaladCompute training infrastructure, and the PyPI publication pipeline.
> Updated: 2026-11-19 (rev 2, post zero-private sweep). Maintained by the estate CTO lane (receipt-linked; see Integrity below).

## Surfaces

| Surface | Identifier | State |
| --- | --- | --- |
| GitHub org | https://github.com/szl-holdings | 176+ public production repos with curated descriptions |
| HuggingFace org | https://huggingface.co/SZLHOLDINGS | ZERO-PRIVATE: 405 models / 169 datasets / 78 spaces, all public (secret-scan-gated publicization sweeps 2026-11-19) |
| Cloudflare | https://puzzle-frontier.stephenlutar2.workers.dev + https://puzzle-frontier-api.stephenlutar2.workers.dev | Live Workers. Front-end proxies /api to the API worker; 436 certified items across 6 constraint-satisfaction banks |
| Cloudflare DNS/proxy | https://a-11-oy.com + https://a11oy.net | Both domains confirmed behind Cloudflare proxy |
| Inference gateway | inference.a-11-oy.com | Estate model-serving mirror |
| SaladCompute | organization alloyscape, 118 container groups | Training/eval fleet with rotation doctrine |
| PyPI | pypi.org | Live: szl-khipu, szl-kernels, szl-substrate, hatun-mcp; 6 more staged (below) |

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

Already live (author Lutar): szl-khipu, szl-kernels, szl-substrate, hatun-mcp.

Staged with release-gated trusted-publishing workflows (OIDC, no tokens in CI; fail closed until each is registered as a PyPI Trusted Publisher, owner-gated on pypi.org):

- szl-specdecode - speculative decoding
- khipu-sda-core - System of Double Accounting core
- szl-energy-mcp - energy attestation MCP
- szl-gov - governance primitives
- szl-abstention-frontier - abstention calibration
- szl-cram - constraint-reasoning augmentation

## GitHub to HuggingFace alignment

- Naming convention: GitHub holds sources and tooling (szl-*); HuggingFace holds artifacts (models salad-* / SZL-*, datasets). Model cards cross-link their GitHub training repo; GitHub product READMEs cross-link their HF artifact.
- Artifacts without a MEASURE receipt ship as productions with explicit "MEASURE pending" markers, never as verdicts.

## Publicity doctrine (honest markers)

The owner directed the estate public. Publicization executed to ZERO-PRIVATE via secret-scan-gated sweeps: every repo's text was scanned for credential patterns (tokens, bearer literals, API-key headers) before or immediately after flipping; two false-positive spaces were manually verified before flipping.

Two honest caveats, recorded rather than hidden:

1. Eval/heldout pools (frontier-54-runs, frontier-55-runs, proving-ground-54h-mesh, VGL probe pools) are now public by the same directive. Contamination discipline shifts from obscurity to construction: fresh-seed eval banks (never published in any training corpus) remain the estate's integrity instrument, and MEASURE receipts remain the only published-performance claims.
2. The wave-logs receipts fabric went public mid-sweep before its deep scan completed; a full post-exposure credential scan ran the same hour. Chain of custody is preserved by content hashes and readbacks recorded in the estate ledger, not by access control alone.

## Chain of custody

Every lane operation lands a receipt in the estate receipts fabric and a dated entry in the estate decision ledger before it is reported. No exceptions. This file itself landed via squash-merged PRs (#129 rev 1, rev 2) with the estate's repository rulesets honored.
