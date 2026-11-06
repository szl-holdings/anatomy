# Security Policy

## Supported Versions

This repository has no versioned releases yet (no GitHub Releases or tags). The
supported line is the default branch `main`, which is what the Hugging Face
Space deploys; security fixes land there.

| Version                  | Supported          |
| ------------------------ | ------------------ |
| `main` (deployed Space)  | :white_check_mark: |
| older commits            | :x:                |

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for security vulnerabilities.**

Please report security vulnerabilities via email to **security@szlholdings.ai** with:

1. Description of the vulnerability
2. Steps to reproduce
3. Potential impact assessment
4. Any suggested mitigations

### Response SLA

| Severity | Initial Response | Resolution Target |
|---|---|---|
| Critical | 24 hours | 7 days |
| High | 48 hours | 30 days |
| Medium | 5 business days | 90 days |
| Low | 10 business days | 180 days |

We follow a **90-day responsible disclosure** policy. After 90 days from initial report, details may be published regardless of patch status (with appropriate notice to reporter).

## Supply-Chain Security

What this repository does today:

- **Space image** — Hugging Face builds the Space from this repository's
  `Dockerfile` (base image pinned by digest; Python dependencies pinned in
  `requirements.txt`). This repository does **not** publish or sign a container
  image of its own: there is no GHCR image, no cosign signature and no
  build-provenance attestation.
- **SLSA** — presented as **L1 honest (static viz)**; no provenance attestation
  is generated for this repository.
- **SBOM** — the `SBOM` workflow generates CycloneDX and SPDX SBOMs on every
  push to `main` (kept as workflow artifacts) and is also wired to run when a
  release is published.
- **Scanning and pinning** — CodeQL (JavaScript/TypeScript and Python), Trivy and
  OpenSSF Scorecard run through SHA-pinned org reusable workflows; GitHub Actions
  are pinned by SHA and checked by `Pin Check`; Dependabot proposes Actions and
  Python dependency updates.
- **Deployment binding** — each publish writes `hf-deploy-manifest.json`, binding
  the served runtime whitelist to the exact protected-main commit, and the live
  `/.well-known/szl-source.json` reports it. That is a source-binding claim, not
  a signature.

The product images this atlas depicts (a11oy, killinchu) carry their own
provenance; see those repositories.

## Section 889 Attestation

SZL Holdings attests that no covered telecommunications equipment or services from the following vendors are used in this software:

1. Huawei Technologies Company
2. ZTE Corporation
3. Hytera Communications Corporation
4. Hangzhou Hikvision Digital Technology Company
5. Dahua Technology Company

Per NDAA Section 889, 41 U.S.C. § 4713.

## Doctrine

- Doctrine v11 LOCKED — kernel commit `c7c0ba17` (749 declarations / 14 axioms / 163 sorries)
- Λ = Conjecture 1 (never a theorem)
- No Iron Bank, FedRAMP, CMMC, or SWFT claims

## Contact

- **Security disclosures:** security@szlholdings.ai
- **General:** hello@szlholdings.ai
- **Website:** https://szlholdings.ai

*This policy follows [OpenSSF Vulnerability Disclosure Guide](https://github.com/ossf/oss-vulnerability-guide).*
