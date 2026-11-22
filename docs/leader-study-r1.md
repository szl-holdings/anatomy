# anatomy domain leader study r1 (propose-only)

Date: 2026-11-22. Method: web-verified 2026 leaders for 3D live-visualization surfaces. Documentation only; no code/CI/config changes; all absorb actions are FUTURE PROPOSALS (non-authorizing); merges remain gated.

## Domain: 3D holo live-visualization with evidence gates (organ vitals, live witnesses)

## Leaders studied (web-verified 2026-11-22)

1. **OHIF Viewer v3.13** (July 2026 release notes). Moat pattern: Smart Scrollbar - highlights which images in a series have finished loading, so the viewer always knows how much is ready. v3.11 docs: multimodality fusion with viewport overlays, dedicated modes.
2. **Cornerstone3D** (OHIF's render/data layer). Moat: modular medical web rendering primitives.
3. **deck.gl** (WebGL large-scale viz). Moat: scale + layer composition.

## Absorb actions (FUTURE PROPOSALS, non-authorizing)

1. (OHIF) Load-state honesty: render only what is loaded; display explicit loaded/unloaded/unknown states for every vital. Never present a pulse as live from reachability alone (align with existing #137/#138 evidence-gating themes, referenced read-only).
2. (OHIF fusion overlays) Multi-source vital fusion in one viewport, each source carrying its own evidence gate and freshness label.
3. (deck.gl) WebGL layering for large vitals series with windowed rendering at scale.
