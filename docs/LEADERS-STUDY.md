# Domain Leader Study — anatomy (3D estate visualization)

OUROBOROS phase-3, cohort-01 tranche-2. PROPOSE-ONLY study card: documentation only, no production change in this PR.

## Domain leaders studied
| Leader | What they have | Key sources |
| --- | --- | --- |
| deck.gl (visgl) | Large-scale GPU layers, per-layer GPU parameter control, typed attribute management for massive datasets; official tips-and-tricks on perf | deck.gl docs tips-and-tricks; attribute-management guide |
| deck.gl-community three module | First-class three.js integration path for mixing 3D meshes with deck.gl layers | github.com/visgl/deck.gl-community |
| three.js ecosystem | Best-practice corpus for WebGL perf (instancing, draw-call budgeting, dispose discipline) | community three.js best-practice notes |

## What the leaders do better
- Per-layer GPU control: leaders separate layer granularity (update a layer without rebuilding the scene) — key for live estate data without frame drops.
- Attribute management: typed arrays reused across frames with explicit invalidation, the difference between 60fps and 2fps at 100k+ points.
- An official three.js bridge exists in deck.gl-community, so 3D organ models and graph layers can share one camera/pick model instead of two engines.

## Absorb actions (proposed, NOT implemented in this PR)
- [ ] Move large-graph rendering to deck.gl layers with per-layer updatePaths instead of full-scene rebuilds on data refresh.
- [ ] Adopt typed attribute buffers with explicit invalidation for receipt-DAG nodes and live frontier telemetry.
- [ ] Route 3D organ meshes through the deck.gl-community three module so holo/graph share one scene graph and picking pipeline.
- [ ] Add a frame-budget receipt (measured fps at N nodes) so viz performance is honest, not asserted.

## Sources
- deck.gl tips & tricks: https://deck.gl/docs/developer-guide/tips-and-tricks
- deck.gl attribute management: https://deck.gl/docs/developer-guide/custom-layers/attribute-management
- three integration: https://github.com/visgl/deck.gl-community
