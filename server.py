#!/usr/bin/env python3
"""SZL Living Anatomy server and evidence contract.

The visual bundle remains static and read-only.  This thin server adds an honest
machine-readable boundary around it:

* ``/healthz`` reports transport health only.
* ``/version`` exposes the exact source and deployed Space revisions using the
  shared vertical-conformance identity contract.
* ``/evidence`` indexes the source binding, local bundle receipt, and measured
  dependency posture without upgrading structural checks to signed proof.
* ``/.well-known/szl-source.json`` identifies the GitHub source and live HF
  revision without pretending that the two revisions are identical.
* ``/api/anatomy/v1/manifest`` describes the contract and status vocabulary.
* ``/api/anatomy/v1/capabilities`` exposes Purpose / Try / Evidence / Limits /
  Reproduce for each major surface.
* ``/api/anatomy/v1/evidence`` separately probes the live dependencies.
* ``/api/anatomy/v1/receipt`` hashes the files that make up the bundle.
* ``POST /api/anatomy/v1/verify/receipt`` recomputes that local integrity
  receipt.  The result is deliberately ``STRUCTURAL-ONLY`` because this Space
  has no signing key; it never upgrades an unsigned receipt to cryptographically
  VERIFIED.

No endpoint mutates state, signs data, runs a model, or claims that reachability
proves model quality.  Lambda remains Conjecture 1 and the Space does not execute
Lean; formal claims are presented as a declared, linked snapshot.
"""

from __future__ import annotations

import functools
import hashlib
import json
import os
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


PORT = int(os.environ.get("PORT", "7860"))
# Resolve from this file, not from a generic /app existence check.  The Docker
# image places server.py in /app already; local verification must never
# accidentally serve an unrelated host-level /app directory.
DIRECTORY = Path(os.environ.get("ANATOMY_ROOT", str(Path(__file__).resolve().parent))).resolve()
SPACE_ID = "SZLHOLDINGS/anatomy"
SOURCE_REPOSITORY = "szl-holdings/anatomy"
SOURCE_BASE_COMMIT = "9847b3031c1aacdcee9aa8e37ae33d573737a5c4"
DEPLOY_MANIFEST_PATH = DIRECTORY / "hf-deploy-manifest.json"
DOCTRINE = "v11"
LOCK = "749/14/163"
KERNEL_COMMIT = "c7c0ba17"
LOCKED_FORMULAS = ["F1", "F4", "F7", "F11", "F12", "F18", "F19", "F22"]

ARTIFACT_PATHS = (
    "index.html",
    "favicon.svg",
    "app.js",
    "data.js",
    "v5_organs.js",
    "frontier_anatomy.js",
    "live-body.html",
    "live-body.js",
    "lib/three.min.js",
    "lib/szl_verify_widget.js",
    "v6_alive.js",
    "server.py",
    "hf-deploy-manifest.json",
)

FORMULA_LINKS = {
    "locked_spine": "https://github.com/szl-holdings/lutar-lean/tree/main/Lutar/Puriq/Formulas",
    "proved_formulas": "https://github.com/szl-holdings/lutar-lean/blob/main/Lutar/Puriq/Formulas/ProvedFormulas.lean",
    "puriq_formula": "https://github.com/szl-holdings/lutar-lean/blob/main/Lutar/Puriq/Formulas/PuriqFormulaLean.lean",
    "quorum_safety": "https://github.com/szl-holdings/lutar-lean/blob/main/Lutar/Wave23/QuorumSafety.lean",
    "hash_chain": "https://github.com/szl-holdings/lutar-lean/blob/main/Lutar/Wave8/HashChain.lean",
}

CAPABILITIES = [
    {
        "id": "anatomy.atlas",
        "name": "Living governed-system atlas",
        "purpose": "Make system ownership, authority boundaries, and receipt flow spatially inspectable.",
        "try": {"method": "GET", "path": "/", "action": "Open an organ or run the guided tour."},
        "evidence": {
            "state": "COMPUTED",
            "basis": "The self-contained WebGL bundle and its local data model are hashed into the anatomy integrity receipt.",
        },
        "limits": [
            "A visual map is not proof that every depicted remote service is healthy.",
            "The atlas is read-only and has no actuation authority.",
        ],
        "reproduce": {
            "steps": [
                "GET /api/anatomy/v1/receipt",
                "POST its JSON body to /api/anatomy/v1/verify/receipt",
                "Compare the artifact_set_sha256 and per-file hashes.",
            ]
        },
        "authority_state": "READ_ONLY",
        "formula_refs": [],
        "provenance": ["https://github.com/szl-holdings/anatomy"],
    },
    {
        "id": "anatomy.formula-spine",
        "name": "Formula-to-organ spine",
        "purpose": "Trace declared formal and experimental formulas to the organs they inform.",
        "try": {"method": "UI", "path": "/", "action": "Open Formula Atlas or Proofs to organs."},
        "evidence": {
            "state": "SNAPSHOT",
            "basis": "The Space presents source-linked declarations; it does not run the Lean kernel in this container.",
            "locked_declared": LOCKED_FORMULAS,
            "kernel_reference": KERNEL_COMMIT,
        },
        "limits": [
            "Exactly eight formulas are declared locked in this snapshot.",
            "Lambda is Conjecture 1, not a theorem.",
            "Current source links and the historical kernel reference are shown separately to avoid false revision equivalence.",
        ],
        "reproduce": {
            "steps": [
                "Open the linked Lean files.",
                "Pin the intended toolchain and commit in lutar-lean.",
                "Run lake build and inspect #print axioms before promoting a claim.",
            ]
        },
        "authority_state": "READ_ONLY",
        "formula_refs": LOCKED_FORMULAS,
        "provenance": list(FORMULA_LINKS.values()),
    },
    {
        "id": "anatomy.live-lens",
        "name": "Live organ posture lens",
        "purpose": "Project current reachability and contract responses from A11OY, Killinchu, and the verifier estate into the body.",
        "try": {"method": "GET", "path": "/api/anatomy/v1/evidence?refresh=1", "action": "Refresh measured dependencies."},
        "evidence": {
            "state": "MIXED",
            "basis": "Dependency states are measured at request time and kept separate from the static anatomy snapshot.",
        },
        "limits": [
            "HTTP reachability does not certify correctness, freshness, safety, or business performance.",
            "A dependency can change after observed_at.",
        ],
        "reproduce": {"steps": ["GET /api/anatomy/v1/evidence?refresh=1", "Probe each declared URL independently."]},
        "authority_state": "READ_ONLY",
        "formula_refs": ["F1", "F7", "F22"],
        "provenance": [
            "https://huggingface.co/spaces/SZLHOLDINGS/a11oy",
            "https://huggingface.co/spaces/SZLHOLDINGS/killinchu",
            "https://huggingface.co/spaces/SZLHOLDINGS/governed-receipt-verifier",
        ],
    },
    {
        "id": "anatomy.integrity-receipt",
        "name": "Local bundle integrity receipt",
        "purpose": "Turn the deployed anatomy bundle into a replayable, byte-level evidence object.",
        "try": {"method": "GET", "path": "/api/anatomy/v1/receipt", "action": "Generate the current deterministic receipt."},
        "evidence": {
            "state": "COMPUTED",
            "verification_state": "STRUCTURAL_ONLY",
            "basis": "SHA-256 is recomputed over every declared artifact and over the canonical receipt body.",
        },
        "limits": [
            "The local receipt is unsigned because the Space has no private signing key.",
            "STRUCTURAL-ONLY is not a cryptographic identity attestation.",
        ],
        "reproduce": {
            "steps": [
                "GET /api/anatomy/v1/receipt",
                "POST the response to /api/anatomy/v1/verify/receipt",
                "Expect STRUCTURAL-ONLY unless an artifact or digest was changed, in which case expect FAIL.",
            ]
        },
        "authority_state": "READ_ONLY",
        "formula_refs": ["F1", "F22"],
        "provenance": [FORMULA_LINKS["hash_chain"]],
    },
    {
        "id": "anatomy.physics-overlays",
        "name": "Physics and quantum-bio overlays",
        "purpose": "Expose bounded exploratory models beside operational and formal layers without confusing them with measurements or locked theorems.",
        "try": {"method": "UI", "path": "/", "action": "Open Physics, Quantum-bio, or Yarqa layers."},
        "evidence": {
            "state": "MODELED",
            "basis": "The overlays run deterministic local equations and simulations from data.js; they do not ingest calibrated laboratory measurements.",
        },
        "limits": [
            "Modeled is not measured.",
            "Narrative and proposed claims remain labeled separately from verified formulas.",
            "No clinical, biological, or quantum-computing performance claim is made.",
        ],
        "reproduce": {
            "steps": [
                "Inspect the formula card and its evidence label.",
                "Record the input parameters.",
                "Re-run the same local overlay and compare its integrity digest.",
            ]
        },
        "authority_state": "READ_ONLY",
        "formula_refs": ["QB-COH", "QB-PMF", "QB-COMPASS", "QB-Lambda-v5", "AG-LANDAUER"],
        "provenance": ["https://github.com/szl-holdings/anatomy/blob/main/data.js"],
    },
]

DEPENDENCIES = (
    {
        "id": "a11oy.honesty",
        "url": "https://szlholdings-a11oy.hf.space/api/a11oy/v1/honest",
        "method": "GET",
        "purpose": "Doctrine and runtime honesty posture",
        "critical": True,
    },
    {
        "id": "a11oy.public-verifier",
        "url": "https://szlholdings-a11oy.hf.space/api/a11oy/v1/verify/receipt",
        "method": "POST",
        "purpose": "Canonical public DSSE/Khipu receipt-verifier contract",
        "critical": True,
    },
    {
        "id": "killinchu.experience-manifest",
        "url": "https://szlholdings-killinchu.hf.space/api/killinchu/v1/experience/manifest",
        "method": "GET",
        "purpose": "Killinchu surface and evidence inventory",
        "critical": False,
    },
    {
        "id": "receipt-verifier.space",
        "url": "https://szlholdings-governed-receipt-verifier.static.hf.space/",
        "method": "GET",
        "purpose": "Standalone browser verifier",
        "critical": False,
    },
)

CONTENT_SECURITY_POLICY = (
    "default-src 'self'; "
    "base-uri 'self'; "
    "object-src 'none'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob:; "
    "font-src 'self'; "
    "connect-src 'self' https://szlholdings-a11oy.hf.space "
    "https://szlholdings-killinchu.hf.space https://szlholdings-amaru.hf.space "
    "https://szlholdings-sentra.hf.space; "
    "form-action 'self'; "
    "frame-ancestors 'self' https://huggingface.co https://*.hf.space https://*.huggingface.co "
    "https://a-11-oy.com https://*.a-11-oy.com https://a11oy.net https://*.a11oy.net"
)

_probe_lock = threading.Lock()
_probe_cache: dict[str, object] = {"at": 0.0, "value": None}
_revision_lock = threading.Lock()
_revision_cache: dict[str, object] = {"at": 0.0, "value": None}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _artifact_manifest() -> dict[str, object]:
    artifacts: list[dict[str, object]] = []
    for rel in ARTIFACT_PATHS:
        path = DIRECTORY / rel
        if path.is_file():
            content = path.read_bytes()
            artifacts.append({"path": rel, "bytes": len(content), "sha256": _sha256(content)})
        else:
            artifacts.append({"path": rel, "state": "MISSING"})
    artifact_set_sha256 = _sha256(_canonical(artifacts))
    return {
        "algorithm": "sha256",
        "artifact_count": len(artifacts),
        "artifact_set_sha256": artifact_set_sha256,
        "artifacts": artifacts,
    }


def _artifact_set_complete(manifest: object) -> bool:
    if not isinstance(manifest, dict):
        return False
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, list) or len(artifacts) != len(ARTIFACT_PATHS):
        return False
    paths: list[str] = []
    for item in artifacts:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("path"), str)
            or not isinstance(item.get("bytes"), int)
            or int(item["bytes"]) < 0
            or not _is_sha256(item.get("sha256"))
        ):
            return False
        paths.append(str(item["path"]))
    return len(set(paths)) == len(paths) and set(paths) == set(ARTIFACT_PATHS)


def _local_receipt() -> dict[str, object]:
    manifest = _artifact_manifest()
    body: dict[str, object] = {
        "schema": "szl.anatomy-integrity-receipt/v1",
        "subject": {
            "space": SPACE_ID,
            "artifact_set_sha256": manifest["artifact_set_sha256"],
        },
        "claim": {
            "purpose": "Byte-level integrity of the deployed Living Anatomy bundle",
            "authority_state": "READ_ONLY",
            "evidence_state": "COMPUTED",
            "doctrine": DOCTRINE,
            "kernel_reference": KERNEL_COMMIT,
            "locked_proven_declared": len(LOCKED_FORMULAS),
            "lambda_state": "CONJECTURE_1",
        },
        "evidence": manifest,
        "signature": {
            "state": "UNAVAILABLE",
            "reason": "No private signing key is present in this public visualization Space.",
        },
        "limits": [
            "Artifact integrity does not certify remote-service health or model quality.",
            "Unsigned local receipt; verification is STRUCTURAL-ONLY.",
        ],
    }
    return {
        "receipt": body,
        "receipt_id": _sha256(_canonical(body)),
        "verification_state": "STRUCTURAL_ONLY",
    }


def _check_local_receipt(candidate: object) -> tuple[int, dict[str, object]]:
    wrapper = candidate if isinstance(candidate, dict) else {}
    receipt = wrapper.get("receipt", wrapper) if isinstance(wrapper, dict) else {}
    supplied_id = wrapper.get("receipt_id") if isinstance(wrapper, dict) else None
    if not isinstance(receipt, dict):
        receipt = {}

    current = _artifact_manifest()
    recomputed_id = _sha256(_canonical(receipt))
    subject = receipt.get("subject") if isinstance(receipt.get("subject"), dict) else {}
    evidence = receipt.get("evidence") if isinstance(receipt.get("evidence"), dict) else {}
    current_complete = _artifact_set_complete(current)
    candidate_complete = _artifact_set_complete(evidence)
    candidate_artifact_set_sha256 = (
        _sha256(_canonical(evidence["artifacts"])) if candidate_complete else None
    )
    checks = [
        {
            "name": "schema",
            "status": "PASS" if receipt.get("schema") == "szl.anatomy-integrity-receipt/v1" else "FAIL",
            "detail": "Expected szl.anatomy-integrity-receipt/v1.",
        },
        {
            "name": "subject",
            "status": "PASS" if subject.get("space") == SPACE_ID else "FAIL",
            "detail": f"Expected {SPACE_ID}.",
        },
        {
            "name": "receipt_digest",
            "status": "PASS" if supplied_id and supplied_id == recomputed_id else "FAIL",
            "detail": "SHA-256 over the canonical receipt body.",
        },
        {
            "name": "artifact_set",
            "status": "PASS"
            if current_complete
            and candidate_complete
            and candidate_artifact_set_sha256 == current["artifact_set_sha256"]
            and evidence.get("artifact_set_sha256") == candidate_artifact_set_sha256
            and subject.get("artifact_set_sha256") == candidate_artifact_set_sha256
            else "FAIL",
            "detail": "Recomputed from both the submitted evidence and files currently served by this Space.",
        },
        {
            "name": "artifact_completeness",
            "status": "PASS" if current_complete and candidate_complete else "FAIL",
            "detail": "Every current and submitted runtime artifact must be present with bytes and SHA-256.",
        },
        {
            "name": "signature",
            "status": "UNAVAILABLE",
            "detail": "This local integrity receipt is unsigned; no cryptographic identity green is asserted.",
        },
    ]
    failed = any(item["status"] == "FAIL" for item in checks)
    verdict = "FAIL" if failed else "STRUCTURAL-ONLY"
    return (400 if failed else 200), {
        "schema": "szl.receipt-verification/v1",
        "ok": not failed,
        "verdict": verdict,
        "verification_state": "FAILED" if failed else "STRUCTURAL_ONLY",
        "checks": checks,
        "recomputed_receipt_id": recomputed_id,
        "observed_at": _utc_now(),
        "limits": "STRUCTURAL-ONLY is advisory and is not a signature verification.",
    }


def _probe_dependency(dep: dict[str, object]) -> dict[str, object]:
    method = str(dep["method"])
    data = b"{}" if method == "POST" else None
    headers = {
        "User-Agent": "szl-anatomy-evidence/1.0",
        "Accept": "application/json,text/html;q=0.8",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(str(dep["url"]), data=data, headers=headers, method=method)
    status: int | None = None
    error: str | None = None
    try:
        with urllib.request.urlopen(req, timeout=4) as response:
            status = response.status
            response.read(256)
    except urllib.error.HTTPError as exc:
        status = exc.code
        error = f"HTTP {exc.code}"
    except Exception as exc:  # network state is evidence, not a server failure
        error = type(exc).__name__

    reachable = status is not None
    if method == "POST":
        contract_available = status in (200, 201, 400, 422, 429)
    else:
        contract_available = status is not None and 200 <= status < 400
    if contract_available:
        contract_state = "AVAILABLE"
        evidence_state = "LIVE"
    elif status == 404:
        contract_state = "MISSING"
        evidence_state = "UNAVAILABLE"
    elif reachable:
        contract_state = "DEGRADED"
        evidence_state = "UNAVAILABLE"
    else:
        contract_state = "UNREACHABLE"
        evidence_state = "UNAVAILABLE"
    return {
        **dep,
        "transport_state": "REACHABLE" if reachable else "UNREACHABLE",
        "contract_state": contract_state,
        "evidence_state": evidence_state,
        "http_status": status,
        "error": error,
    }


def _dependency_evidence(force: bool = False) -> dict[str, object]:
    now = time.monotonic()
    with _probe_lock:
        cached = _probe_cache.get("value")
        if not force and cached is not None and now - float(_probe_cache["at"]) < 30:
            return cached  # type: ignore[return-value]
    with ThreadPoolExecutor(max_workers=len(DEPENDENCIES)) as pool:
        rows = list(pool.map(_probe_dependency, DEPENDENCIES))
    live_count = sum(row["evidence_state"] == "LIVE" for row in rows)
    evidence_state = "LIVE" if live_count == len(rows) else ("MIXED" if live_count else "UNAVAILABLE")
    verifier = next(row for row in rows if row["id"] == "a11oy.public-verifier")
    value: dict[str, object] = {
        "schema": "szl.anatomy-evidence/v1",
        "observed_at": _utc_now(),
        "scope": "Endpoint reachability and declared contract presence only.",
        "transport_state": "REACHABLE",
        "evidence_state": evidence_state,
        "verification_state": "AVAILABLE" if verifier["contract_state"] == "AVAILABLE" else "UNAVAILABLE",
        "authority_state": "READ_ONLY",
        "summary": {"live": live_count, "total": len(rows)},
        "dependencies": rows,
        "limits": [
            "Reachability does not certify quality, safety, freshness, or business performance.",
            "The local anatomy integrity verifier remains STRUCTURAL_ONLY because it is unsigned.",
        ],
    }
    with _probe_lock:
        _probe_cache.update({"at": time.monotonic(), "value": value})
    return value


def _is_full_revision(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 40
        and all(character in "0123456789abcdef" for character in value.lower())
    )


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value.lower())
    )


def _hf_revision(force: bool = False) -> str | None:
    env_revision = os.environ.get("SPACE_REPOSITORY_COMMIT")
    if _is_full_revision(env_revision):
        return str(env_revision).lower()
    now = time.monotonic()
    with _revision_lock:
        cached = _revision_cache.get("value")
        if not force and cached and now - float(_revision_cache["at"]) < 60:
            return str(cached)
    req = urllib.request.Request(
        "https://huggingface.co/api/spaces/SZLHOLDINGS/anatomy?expand[]=sha",
        headers={"User-Agent": "szl-anatomy-source-attestation/1.0", "Accept": "application/json"},
    )
    revision: str | None = None
    try:
        with urllib.request.urlopen(req, timeout=4) as response:
            data = json.load(response)
            candidate = data.get("sha")
            if _is_full_revision(candidate):
                revision = str(candidate).lower()
    except Exception:
        revision = None
    with _revision_lock:
        _revision_cache.update({"at": time.monotonic(), "value": revision})
    return revision


def _deployment_commit_title(source_revision: str, workflow_run_id: str) -> str:
    return f"hf-sync: source {source_revision[:12]} run {workflow_run_id}"


def _hf_commit_matches_binding(
    hf_revision: str | None,
    source_revision: str,
    workflow_run_id: str,
) -> bool:
    if (
        not isinstance(hf_revision, str)
        or len(hf_revision) != 40
        or any(character not in "0123456789abcdef" for character in hf_revision.lower())
        or not workflow_run_id.isdigit()
    ):
        return False
    request = urllib.request.Request(
        f"https://huggingface.co/api/spaces/{SPACE_ID}/commits/{hf_revision.lower()}",
        headers={
            "User-Agent": "szl-anatomy-source-attestation/1.1",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=4) as response:
            commits = json.load(response)
    except Exception:
        return False
    if not isinstance(commits, list) or not commits or not isinstance(commits[0], dict):
        return False
    current = commits[0]
    return (
        str(current.get("id") or "").lower() == hf_revision.lower()
        and current.get("title")
        == _deployment_commit_title(source_revision, workflow_run_id)
    )


def _source_binding(hf_revision: str | None) -> dict[str, object]:
    fallback: dict[str, object] = {
        "repository": SOURCE_REPOSITORY,
        "commit": SOURCE_BASE_COMMIT,
        "path": "",
        "relation": "base-plus-hf-overlay",
        "alignment_state": "PENDING_GITHUB_SYNC",
        "built_at": None,
        "limits": [
            "source.commit is the declared GitHub base; deployment.hf_revision is measured separately.",
            "No workflow manifest bound to the measured Hugging Face revision was observed.",
        ],
    }
    try:
        payload = json.loads(DEPLOY_MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return fallback
    repository = payload.get("source_repository")
    revision = payload.get("source_revision")
    workflow_run_id = payload.get("workflow_run_id")
    if (
        payload.get("schema") != "szl.hf-deploy-manifest/v1"
        or repository != SOURCE_REPOSITORY
        or not _is_full_revision(revision)
        or not isinstance(workflow_run_id, str)
        or not _hf_commit_matches_binding(
            hf_revision,
            revision.lower(),
            workflow_run_id,
        )
    ):
        return fallback
    return {
        "repository": repository,
        "commit": revision.lower(),
        "path": str(payload.get("source_path") or ""),
        "relation": "github-actions-source-bound-deployment",
        "alignment_state": "SOURCE_BOUND_DEPLOYMENT",
        "built_at": payload.get("built_at"),
        "limits": [
            "The measured Hugging Face commit metadata binds this revision to the manifest's GitHub source and workflow run.",
            "The deployment uploads a declared runtime whitelist; it does not claim whole-repository byte parity.",
        ],
    }


def _source_attestation(force: bool = False) -> dict[str, object]:
    revision = _hf_revision(force=force)
    manifest = _artifact_manifest()
    source_binding = _source_binding(revision)
    return {
        "schema": "szl.deployment-source/v1",
        "source": {
            key: source_binding[key]
            for key in ("repository", "commit", "path", "relation")
        },
        "deployment": {
            "hf_space": SPACE_ID,
            "hf_revision": revision,
            "artifact_set_sha256": manifest["artifact_set_sha256"],
        },
        "built_at": source_binding["built_at"],
        "observed_at": _utc_now(),
        "alignment_state": source_binding["alignment_state"],
        "limits": source_binding["limits"],
    }


def _version_contract(force: bool = False) -> dict[str, object]:
    source = _source_attestation(force=force)
    source_identity = source["source"]
    deployment = source["deployment"]
    identity_measured = (
        source["alignment_state"] == "SOURCE_BOUND_DEPLOYMENT"
        and isinstance(source_identity, dict)
        and _is_full_revision(source_identity.get("commit"))
        and isinstance(deployment, dict)
        and _is_full_revision(deployment.get("hf_revision"))
    )
    return {
        "schemaVersion": "szl.vertical-conformance.version.v1",
        "service": "anatomy",
        "surface": "anatomy",
        "gitSha": source_identity.get("commit") if identity_measured else None,
        "evidenceState": "MEASURED" if identity_measured else "UNAVAILABLE",
        "deploymentRevision": deployment.get("hf_revision") if isinstance(deployment, dict) else None,
        "contractVersion": "1.1.0",
    }


def _evidence_contract(force: bool = False) -> dict[str, object]:
    source = _source_attestation(force=force)
    dependency_evidence = _dependency_evidence(force=force)
    local_receipt = _local_receipt()
    source_identity = source["source"]
    deployment = source["deployment"]
    source_bound = (
        source["alignment_state"] == "SOURCE_BOUND_DEPLOYMENT"
        and isinstance(source_identity, dict)
        and _is_full_revision(source_identity.get("commit"))
        and isinstance(deployment, dict)
        and _is_full_revision(deployment.get("hf_revision"))
    )
    receipt_body = local_receipt["receipt"]
    receipt_evidence = receipt_body["evidence"] if isinstance(receipt_body, dict) else {}
    artifact_complete = _artifact_set_complete(receipt_evidence)
    evidence_available = source_bound and artifact_complete
    return {
        "schemaVersion": "szl.vertical-conformance.evidence.v1",
        "service": "anatomy",
        "surface": "anatomy",
        "gitSha": source_identity.get("commit") if evidence_available else None,
        "evidenceState": "PARTIAL" if evidence_available else "UNAVAILABLE",
        "runtime": {
            "status": "RUNNING" if artifact_complete else "DEGRADED",
            "ready": artifact_complete,
            "transportState": "REACHABLE",
            "authorityState": "READ_ONLY",
        },
        "source": source,
        "receipts": [
            {
                "kind": "bundle-integrity",
                "status": "STRUCTURAL_ONLY" if artifact_complete else "FAILED",
                "receiptId": local_receipt["receipt_id"],
                "artifactSetSha256": (
                    receipt_evidence.get("artifact_set_sha256")
                    if isinstance(receipt_evidence, dict)
                    else None
                ),
                "scope": "deployed runtime whitelist; unsigned local recomputation",
                "verify": "/api/anatomy/v1/verify/receipt",
            }
        ],
        "dependencies": {
            "evidenceState": dependency_evidence["evidence_state"],
            "observedAt": dependency_evidence["observed_at"],
            "live": dependency_evidence["summary"]["live"],
            "total": dependency_evidence["summary"]["total"],
            "details": "/api/anatomy/v1/evidence?refresh=1",
        },
        "outputProvenance": {
            "signatureStatus": "UNSIGNED",
            "authenticityEstablished": False,
            "record": "content-addressed bundle receipt; no runtime signing key",
        },
        "limitations": [
            "The bundle receipt is STRUCTURAL_ONLY and does not establish publisher identity.",
            "Dependency reachability does not certify quality, safety, freshness, or business performance.",
            "The Space is read-only and does not execute or authorize agent actions.",
        ],
    }


def _manifest() -> dict[str, object]:
    return {
        "schema": "szl.anatomy-manifest/v1",
        "service": "anatomy-space",
        "space": SPACE_ID,
        "purpose": "Read-only spatial evidence map of the governed-agent substrate.",
        "contract_version": "1.1.0",
        "state_dimensions": {
            "transport_state": "REACHABLE",
            "evidence_state": "MIXED",
            "verification_state": "STRUCTURAL_ONLY",
            "authority_state": "READ_ONLY",
        },
        "status_vocabulary": {
            "transport_state": ["REACHABLE", "UNREACHABLE"],
            "evidence_state": ["LIVE", "COMPUTED", "SNAPSHOT", "MODELED", "MIXED", "UNAVAILABLE"],
            "verification_state": ["VERIFIED", "STRUCTURAL_ONLY", "UNAVAILABLE", "FAILED"],
            "authority_state": ["READ_ONLY", "PROPOSAL_ONLY", "MUTATING"],
        },
        "endpoints": {
            "version": "/version",
            "evidence_index": "/evidence",
            "manifest": "/api/anatomy/v1/manifest",
            "capabilities": "/api/anatomy/v1/capabilities",
            "evidence": "/api/anatomy/v1/evidence?refresh=1",
            "receipt": "/api/anatomy/v1/receipt",
            "verify_receipt": "/api/anatomy/v1/verify/receipt",
            "source": "/.well-known/szl-source.json",
        },
        "doctrine": {
            "version": DOCTRINE,
            "lock": LOCK,
            "kernel_reference": KERNEL_COMMIT,
            "locked_proven_declared": LOCKED_FORMULAS,
            "lambda": "CONJECTURE_1",
        },
        "limits": [
            "RUNNING or REACHABLE describes transport, not model quality.",
            "This Space is a visualization and evidence reader, not an autonomous actuator.",
        ],
    }


class HardenedHandler(SimpleHTTPRequestHandler):
    server_version = "szl"
    sys_version = ""

    def version_string(self) -> str:
        return "szl"

    def _send_json(
        self,
        payload: object,
        *,
        status: int = 200,
        evidence_state: str = "SNAPSHOT",
        extra_headers: dict[str, str] | None = None,
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("X-SZL-Transport-State", "REACHABLE")
        self.send_header("X-SZL-Evidence-State", evidence_state)
        if extra_headers:
            for key, value in extra_headers.items():
                self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlsplit(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)
        force = query.get("refresh") == ["1"]
        if path == "/healthz":
            self._send_json(
                {
                    "status": "ok",
                    "organ": "anatomy",
                    "service": "anatomy-space",
                    "transport_state": "REACHABLE",
                    "evidence_state": "SNAPSHOT",
                    "verification_state": "STRUCTURAL_ONLY",
                    "authority_state": "READ_ONLY",
                    "contracts": {"version": "/version", "evidence": "/evidence"},
                    "note": "Transport health only; quality and upstream freshness are not inferred.",
                },
                evidence_state="SNAPSHOT",
            )
            return
        if path == "/version":
            payload = _version_contract(force=force)
            self._send_json(
                payload,
                status=200 if payload["evidenceState"] == "MEASURED" else 503,
                evidence_state=str(payload["evidenceState"]),
            )
            return
        if path == "/evidence":
            payload = _evidence_contract(force=force)
            receipt_status = str(payload["receipts"][0]["status"])
            self._send_json(
                payload,
                status=200 if payload["evidenceState"] == "PARTIAL" else 503,
                evidence_state=str(payload["evidenceState"]),
                extra_headers={"X-SZL-Verification-State": receipt_status},
            )
            return
        if path == "/.well-known/szl-source.json":
            self._send_json(_source_attestation(force=force), evidence_state="COMPUTED")
            return
        if path == "/api/anatomy/v1/manifest":
            self._send_json(_manifest(), evidence_state="SNAPSHOT")
            return
        if path in ("/api/anatomy/v1/capabilities", "/api/anatomy/v1/capability-matrix"):
            self._send_json(
                {
                    "schema": "szl.anatomy-capabilities/v1",
                    "state_dimensions": _manifest()["state_dimensions"],
                    "count": len(CAPABILITIES),
                    "capabilities": CAPABILITIES,
                },
                evidence_state="MIXED",
            )
            return
        if path == "/api/anatomy/v1/evidence":
            payload = _dependency_evidence(force=force)
            self._send_json(payload, evidence_state=str(payload["evidence_state"]))
            return
        if path == "/api/anatomy/v1/receipt":
            self._send_json(
                _local_receipt(),
                evidence_state="COMPUTED",
                extra_headers={"X-SZL-Verification-State": "STRUCTURAL_ONLY"},
            )
            return
        super().do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        if path != "/api/anatomy/v1/verify/receipt":
            self._send_json({"error": "not_found", "path": path}, status=404, evidence_state="UNAVAILABLE")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0 or length > 1_000_000:
            self._send_json(
                {"error": "invalid_body", "detail": "JSON body required; maximum 1,000,000 bytes."},
                status=400,
                evidence_state="UNAVAILABLE",
            )
            return
        try:
            candidate = json.loads(self.rfile.read(length))
        except Exception:
            self._send_json({"error": "invalid_json"}, status=400, evidence_state="UNAVAILABLE")
            return
        status, payload = _check_local_receipt(candidate)
        self._send_json(
            payload,
            status=status,
            evidence_state="COMPUTED",
            extra_headers={"X-SZL-Verification-State": str(payload["verification_state"])},
        )

    def end_headers(self) -> None:
        self.send_header("Cross-Origin-Opener-Policy", "same-origin-allow-popups")
        self.send_header("Cross-Origin-Resource-Policy", "cross-origin")
        self.send_header("Content-Security-Policy", CONTENT_SECURITY_POLICY)
        self.send_header("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()")
        super().end_headers()


def make_server(host: str = "0.0.0.0", port: int = PORT) -> ThreadingHTTPServer:
    handler = functools.partial(HardenedHandler, directory=str(DIRECTORY))
    return ThreadingHTTPServer((host, port), handler)


if __name__ == "__main__":
    httpd = make_server()
    print(f"Serving SZL Living Anatomy from {DIRECTORY} on 0.0.0.0:{PORT}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
