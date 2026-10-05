# Alloy Refinement Observatory

Living Anatomy adds a read-only observability layer for the public Second Brain
projection of Alloy Refinement Fabric receipts.

## Runtime contracts

```text
GET /api/anatomy/v1/refinement/status
GET /api/anatomy/v1/refinement/patterns?error_code=ARITHMETIC_ERROR&limit=50
GET /refinement-lab
```

The `lib/refinement_living_runtime.py` wrapper subclasses the existing hardened
Living Anatomy handler. Existing health, Brain, formula, quant, Ouroboros, and
frontier routes remain authoritative and unchanged.

`lib/refinement_contract.py` independently verifies:

- state and source receipt SHA-256 values;
- exact Second Brain source identity when available;
- handles-only content and zero private graph/raw reasoning;
- pattern IDs, error codes, pair digests, and bounded metrics;
- `NONE` training, promotion, and execution authority.

Direct reads of the internal JSON/source files are blocked by the wrapper. The
public HTML uses safe DOM `textContent`, no third-party CDN, responsive layouts,
and no action or provider controls.

## Canonical publication

The existing GitHub-owned Anatomy publisher remains the sole Hugging Face writer.
It first materializes the exact public Second Brain snapshot, then attempts to
materialize `data/refinement-patterns.public.json` from that same protected-main
revision. Until the upstream file is admitted, the projection remains
`UNAVAILABLE_SOURCE_NOT_ADMITTED`; the rest of Living Anatomy remains reachable.

After publication, `scripts/verify_refinement_observatory.py` reads the live
status, pattern route, and observatory page and requires the exact local source
revision and state digest. A running Space without this readback is not treated
as aligned.
