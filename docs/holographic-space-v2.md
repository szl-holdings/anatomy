# Anatomy Holo-Constellation v2

The Anatomy Space keeps its existing interactive organ map, evidence APIs, receipt verifier, and fail-closed runtime semantics. Holo-Constellation v2 adds a local visual instrument and shared estate navigation without changing those product contracts.

## Runtime-integrity boundary

Both new browser assets are included in `server.ARTIFACT_PATHS`:

- `szl-holo-v2.css`
- `szl-holo-v2.js`

They therefore participate in the Anatomy runtime manifest and structural receipt rather than being served as untracked presentation files.

## Accessibility boundary

The shared layer provides keyboard focus, 44-pixel controls, reduced-motion behavior, increased-contrast behavior, forced-color behavior, responsive navigation, and print handling. Decorative animation is presentation only and is not reported as telemetry or operational evidence.
