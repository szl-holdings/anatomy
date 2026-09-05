#!/usr/bin/env python3
"""Publish Living Anatomy Neural Quant v7 to the creator-profile Space.

GitHub protected main is authoritative. The workflow materializes the exact
575-chunk Second Brain projection plus its review-gated frontier candidate set,
uploads only the runtime whitelist, keeps the Space public/running, and verifies
live source-bound Brain, formula, quant, Ouroboros, and privacy contracts.
"""
from __future__ import annotations

import glob
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from huggingface_hub import CommitOperationAdd, HfApi

SPACE_ID = "betterwithage/anatomy"
EXPECTED_IDENTITY = "betterwithage"
EXPECTED_REPOSITORY = "szl-holdings/anatomy"
LIVE_BASE = "https://betterwithage-anatomy.hf.space"
EXPECTED_PUBLIC_CHUNKS = 575
MIN_FRONTIER_CANDIDATES = 70
MIN_FRONTIER_SOURCES = 7
EXPECTED_ATTRIBUTED_FORMULAS = 30
EXPECTED_EXECUTABLE_FORMULAS = 21
EXPECTED_QUANT_DOMAINS = 9
EXPECTED_LOCKED_PROVEN = 8


def stage_name(runtime: object) -> str:
    value = getattr(runtime, "stage", None)
    return str(getattr(value, "value", value) or "UNKNOWN").upper()


def get_json(url: str, timeout: int = 20) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "szl-anatomy-creator-sync/2.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise RuntimeError(f"expected JSON object from {url}")
    return payload


def get_text(url: str, timeout: int = 20) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "szl-anatomy-creator-sync/2.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(2 * 1024 * 1024).decode("utf-8", errors="replace")


def get_status(url: str, timeout: int = 20) -> int:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "szl-anatomy-creator-sync/2.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return int(response.status)
    except urllib.error.HTTPError as error:
        return int(error.code)


def current_protected_main(repository: str, token: str) -> str:
    request = urllib.request.Request(
        os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
        + f"/repos/{repository}/commits/main",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "szl-anatomy-creator-sync/2.0",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return str(json.load(response).get("sha") or "").lower()


def runtime_files() -> list[str]:
    patterns = [
        "README.md",
        "Dockerfile",
        ".dockerignore",
        "requirements.txt",
        "server.py",
        "organ_integrity.py",
        "living_runtime.py",
        "frontier_runtime.py",
        "second_brain_runtime.py",
        "scripts/materialize_second_brain.py",
        ".runtime/**/*",
        "*.html",
        "*.js",
        "*.css",
        "lib/**/*",
    ]
    files: set[str] = set()
    for pattern in patterns:
        files.update(
            path
            for path in glob.glob(pattern, recursive=True)
            if os.path.isfile(path)
        )
    required = {
        "README.md",
        "Dockerfile",
        "requirements.txt",
        "server.py",
        "living_runtime.py",
        "frontier_runtime.py",
        "second_brain_runtime.py",
        "neural-quant-v7.js",
        "neural-quant-v7.css",
        "holographic-v7.js",
        "holographic-v7.css",
        ".runtime/second-brain/manifest.json",
        ".runtime/second-brain/brain-corpus.public.jsonl",
        ".runtime/second-brain/frontier-state.v1.json",
        ".runtime/second-brain/frontier-candidates.public.jsonl",
        ".runtime/second-brain/source.json",
    }
    missing = sorted(required - files)
    if missing:
        raise RuntimeError(f"required Living Anatomy v7 artifacts missing: {missing}")
    return sorted(files)


def ensure_destination(api: HfApi) -> None:
    try:
        api.repo_info(repo_id=SPACE_ID, repo_type="space")
    except Exception:
        api.create_repo(
            repo_id=SPACE_ID,
            repo_type="space",
            private=False,
            space_sdk="docker",
            exist_ok=True,
        )
    api.update_repo_settings(
        repo_id=SPACE_ID,
        repo_type="space",
        private=False,
    )


def live_deploy_manifest() -> dict[str, Any] | None:
    """Read the public deployment record without treating absence as success."""

    url = (
        "https://huggingface.co/spaces/"
        + SPACE_ID
        + "/resolve/main/hf-deploy-manifest.json?download=true"
    )
    try:
        return get_json(url)
    except Exception as error:
        print(
            "No reusable live deployment manifest:",
            type(error).__name__,
            flush=True,
        )
        return None


def deployment_inputs_match(
    observed: dict[str, Any] | None,
    desired: dict[str, Any],
) -> bool:
    """Compare only immutable release inputs; workflow-run IDs are observations."""

    if not isinstance(observed, dict):
        return False
    if observed.get("schema") != "szl.hf-deploy-manifest/v1":
        return False
    if observed.get("source_repository") != desired.get("source_repository"):
        return False
    if observed.get("source_revision") != desired.get("source_revision"):
        return False
    observed_destination = observed.get("destination")
    desired_destination = desired.get("destination")
    if not isinstance(observed_destination, dict) or not isinstance(
        desired_destination,
        dict,
    ):
        return False
    for key in ("repo_id", "repo_type", "mode", "visibility", "lifecycle"):
        if observed_destination.get(key) != desired_destination.get(key):
            return False
    observed_dependencies = observed.get("dependencies")
    desired_dependencies = desired.get("dependencies")
    if not isinstance(observed_dependencies, dict) or not isinstance(
        desired_dependencies,
        dict,
    ):
        return False
    observed_brain = observed_dependencies.get("second_brain")
    desired_brain = desired_dependencies.get("second_brain")
    if not isinstance(observed_brain, dict) or not isinstance(desired_brain, dict):
        return False
    immutable_brain_fields = (
        "source_repository",
        "source_revision",
        "public_chunk_count",
        "corpus_sha256",
        "frontier_candidate_count",
        "frontier_source_count",
        "frontier_candidate_set_sha256",
        "frontier_state_sha256",
        "frontier_candidates_sha256",
        "formula_counts",
        "quant_domain_count",
        "lambda_state",
        "candidate_state",
        "authority_state",
        "content_access",
        "training_authority",
        "promotion_authority",
        "execution_authority",
        "merge_authority",
    )
    return all(
        observed_brain.get(key) == desired_brain.get(key)
        for key in immutable_brain_fields
    )

def wait_running(api: HfApi, target_sha: str, timeout_seconds: int = 900) -> None:
    deadline = time.monotonic() + timeout_seconds
    restarted = False
    last: tuple[str, str, bool] | None = None
    while time.monotonic() < deadline:
        info = api.repo_info(repo_id=SPACE_ID, repo_type="space")
        stage = stage_name(api.get_space_runtime(repo_id=SPACE_ID))
        current_sha = str(getattr(info, "sha", "") or "")
        private = bool(getattr(info, "private", False))
        last = (current_sha, stage, private)
        print(
            "Observed creator Space:",
            current_sha,
            stage,
            "private=",
            private,
            flush=True,
        )
        if private:
            api.update_repo_settings(
                repo_id=SPACE_ID,
                repo_type="space",
                private=False,
            )
        if current_sha == target_sha and stage == "RUNNING" and not private:
            return
        if current_sha == target_sha and stage in {
            "PAUSED",
            "SLEEPING",
            "STOPPED",
            "RUNTIME_ERROR",
            "BUILD_ERROR",
            "CONFIG_ERROR",
        } and not restarted:
            api.restart_space(
                repo_id=SPACE_ID,
                factory_reboot=stage
                in {"RUNTIME_ERROR", "BUILD_ERROR", "CONFIG_ERROR"},
            )
            restarted = True
        time.sleep(10)
    raise TimeoutError(
        f"{SPACE_ID} did not settle public/RUNNING at {target_sha}: {last}"
    )


def assert_handles_only(payload: dict[str, Any], key: str = "handles") -> None:
    handles = payload.get(key)
    if not isinstance(handles, list):
        raise AssertionError(f"{key} is not a list")
    encoded = json.dumps(handles, ensure_ascii=False, sort_keys=True).lower()
    assert '"content"' not in encoded
    assert '"text"' not in encoded
    for handle in handles:
        assert isinstance(handle, dict)
        assert len(str(handle.get("sha256") or "")) == 64


def verify_live(
    source_revision: str,
    target_sha: str,
    brain_revision: str,
    workflow_run_id: str,
    candidate_set_sha256: str,
    frontier_candidate_count: int,
    frontier_source_count: int,
) -> None:
    last_error: Exception | None = None
    for attempt in range(24):
        try:
            root = get_text(LIVE_BASE + "/")
            health = get_json(LIVE_BASE + "/healthz")
            living = get_json(
                LIVE_BASE + "/api/anatomy/v1/living-health?refresh=1"
            )
            brain = get_json(
                LIVE_BASE + "/api/anatomy/v1/brain/health?refresh=1"
            )
            search = get_json(
                LIVE_BASE
                + "/api/anatomy/v1/brain/search"
                + "?q=governed%20receipts%20living%20anatomy&k=3"
            )
            frontier = get_json(
                LIVE_BASE
                + "/api/anatomy/v1/brain/frontier"
                + "?q=formula%20quant%20anatomy%20ouroboros&k=12"
            )
            formulas = get_json(
                LIVE_BASE + "/api/anatomy/v1/brain/formulas?k=12"
            )
            quant = get_json(LIVE_BASE + "/api/anatomy/v1/brain/quant?k=12")
            ouroboros = get_json(
                LIVE_BASE + "/api/anatomy/v1/brain/ouroboros?k=12"
            )
            neural = get_json(
                LIVE_BASE + "/api/anatomy/v1/brain/neural-quant-v7?k=12"
            )
            holographic = get_json(
                LIVE_BASE + "/api/anatomy/v1/holographic-v7?refresh=1"
            )
            atlas = get_json(
                LIVE_BASE + "/api/anatomy/v1/frontier/status?refresh=1"
            )
            atlas_formulas = get_json(
                LIVE_BASE + "/api/anatomy/v1/frontier/formulas?k=48&refresh=1"
            )
            version = get_json(LIVE_BASE + "/version?refresh=1")
            evidence = get_json(LIVE_BASE + "/evidence?refresh=1", timeout=25)
            source = get_json(
                LIVE_BASE + "/.well-known/szl-source.json?refresh=1"
            )

            assert "neural-quant-v7.js" in root
            assert "neural-quant-v7.css" in root
            assert health["transport_state"] == "REACHABLE"
            assert living["ready"] is True
            assert living["experience"] == "NEURAL_QUANT_V7"
            assert living["organs"]["brain"]["chunk_count"] == EXPECTED_PUBLIC_CHUNKS
            assert (
                living["organs"]["brain"]["frontier_candidate_count"]
                == frontier_candidate_count
            )
            assert living["organs"]["neural_quant"]["locked_proven_count"] == 8
            assert living["organs"]["neural_quant"]["quant_domain_count"] == 9

            assert brain["ready"] is True
            assert brain["source_revision"] == brain_revision
            assert brain["chunk_count"] == EXPECTED_PUBLIC_CHUNKS
            assert brain["frontier"]["candidate_count"] == frontier_candidate_count
            assert brain["frontier"]["source_count"] == frontier_source_count
            assert brain["frontier"]["candidate_set_sha256"] == candidate_set_sha256
            assert brain["formula_atlas"]["attributed_formula_count"] == EXPECTED_ATTRIBUTED_FORMULAS
            assert brain["formula_atlas"]["executable_formula_count"] == EXPECTED_EXECUTABLE_FORMULAS
            assert brain["formula_atlas"]["locked_proven_count"] == EXPECTED_LOCKED_PROVEN
            assert brain["formula_atlas"]["mapping"] == "UNKNOWN_NOT_INFERRED"
            assert brain["formula_atlas"]["lambda_status"] == "CONJECTURE_1_OPEN_ADVISORY_ONLY"
            assert brain["quant_domain_count"] == EXPECTED_QUANT_DOMAINS
            assert brain["private_graph_nodes_loaded"] == 0
            assert brain["raw_graph_nodes_admitted_to_gradients"] == 0
            assert brain["content_access"] == "HANDLES_ONLY"
            assert brain["training_authority"] == "NONE"
            assert brain["promotion_authority"] == "NONE"
            assert brain["execution_authority"] == "NONE"
            assert brain["merge_authority"] == "NONE"

            assert search["ready"] is True
            assert_handles_only(search)
            assert frontier["ready"] is True
            assert frontier["state"] == "REVIEW_REQUIRED"
            assert frontier["candidate_set_sha256"] == candidate_set_sha256
            assert_handles_only(frontier)
            assert frontier["training_authority"] == "NONE"
            assert frontier["execution_authority"] == "NONE"

            assert formulas["ready"] is True
            assert formulas["attributed_formula_count"] == EXPECTED_ATTRIBUTED_FORMULAS
            assert formulas["executable_formula_count"] == EXPECTED_EXECUTABLE_FORMULAS
            assert formulas["locked_proven_count"] == EXPECTED_LOCKED_PROVEN
            assert formulas["f_number_mapping"] == "UNKNOWN_NOT_INFERRED"
            assert formulas["lambda_status"] == "CONJECTURE_1_OPEN_ADVISORY_ONLY"
            assert_handles_only(formulas)

            assert quant["ready"] is True
            assert quant["quant_domain_count"] == EXPECTED_QUANT_DOMAINS
            assert len(quant["domains"]) == EXPECTED_QUANT_DOMAINS
            assert_handles_only(quant)

            assert ouroboros["ready"] is True
            assert ouroboros["loop_contract"]["bounded"] is True
            assert ouroboros["loop_contract"]["terminating"] is True
            assert ouroboros["loop_contract"]["receipt_closed"] is True
            assert ouroboros["loop_contract"]["recommendations_executed"] is False
            assert_handles_only(ouroboros)

            assert neural["ready"] is True
            assert neural["version"] == "7.0.0"
            assert neural["candidate_set_sha256"] == candidate_set_sha256
            assert neural["brain"]["chunk_count"] == EXPECTED_PUBLIC_CHUNKS
            assert neural["brain"]["frontier_candidate_count"] == frontier_candidate_count
            assert neural["formulas"]["attributed"] == EXPECTED_ATTRIBUTED_FORMULAS
            assert neural["formulas"]["executable"] == EXPECTED_EXECUTABLE_FORMULAS
            assert neural["formulas"]["locked_proven"] == EXPECTED_LOCKED_PROVEN
            assert neural["quant"]["domain_count"] == EXPECTED_QUANT_DOMAINS
            assert neural["content_access"] == "HANDLES_ONLY"
            assert neural["authority"] == {
                "training": "NONE",
                "promotion": "NONE",
                "execution": "NONE",
                "merge": "NONE",
                "provider_mutation": "NONE",
            }
            for group in ("formulas", "quant", "ouroboros"):
                assert_handles_only(neural[group])

            assert holographic["ready"] is True
            assert holographic["state"] == "SOURCE_BOUND_READ_ONLY"
            assert holographic["claims"] == {
                "content_exposed": False,
                "weights_trained": False,
                "claim_promoted": False,
                "private_graph_used": False,
                "execution_performed": False,
                "human_review_required": True,
            }
            assert atlas["ready"] is True
            assert atlas["state"] == "SOURCE_BOUND_REVIEW_MEMORY"
            assert atlas["second_brain_source_revision"] == brain_revision
            assert atlas["candidate_set_sha256"] == candidate_set_sha256
            assert atlas["candidate_count"] == frontier_candidate_count
            assert atlas["source_count"] == frontier_source_count
            assert atlas["formula_atlas"] == {
                "attributed_formula_count": EXPECTED_ATTRIBUTED_FORMULAS,
                "executable_formula_count": EXPECTED_EXECUTABLE_FORMULAS,
                "quant_domain_count": EXPECTED_QUANT_DOMAINS,
                "locked_proven_formula_count": EXPECTED_LOCKED_PROVEN,
                "f_number_to_executable_mapping": "UNKNOWN_NOT_INFERRED",
            }
            assert atlas["content_access"] == "HANDLES_ONLY"
            assert atlas["training_authority"] == "NONE"
            assert atlas["promotion_authority"] == "NONE"
            assert atlas["execution_authority"] == "NONE"
            assert atlas["private_graph_present"] is False
            assert atlas_formulas["ready"] is True
            assert atlas_formulas["matched_count"] >= 60
            assert atlas_formulas["returned_count"] == 48
            assert len(atlas_formulas["handles"]) == 48
            assert_handles_only(atlas_formulas)
            assert all(
                handle["contentAccess"] == "HANDLES_ONLY"
                and handle["authority"] == "NONE"
                for handle in atlas_formulas["handles"]
            )

            assert get_status(
                LIVE_BASE + "/.runtime/second-brain/frontier-candidates.public.jsonl"
            ) == 404
            assert version["gitSha"] == source_revision
            assert version["deploymentRevision"] == target_sha
            assert version["secondBrainSourceRevision"] == brain_revision
            assert version["secondBrainCandidateSetSha256"] == candidate_set_sha256
            assert version["experienceVersion"] == "NEURAL_QUANT_V7"
            assert evidence["gitSha"] == source_revision
            assert evidence["source"]["deployment"]["hf_revision"] == target_sha
            assert (
                evidence["dependencies"]["secondBrain"]["candidateSetSha256"]
                == candidate_set_sha256
            )
            assert source["deployment"]["hf_revision"] == target_sha
            assert source["source"]["commit"] == source_revision
            assert source["deployment"]["workflow_run_id"] == workflow_run_id
            print(
                "Verified creator-profile Living Anatomy Neural Quant v7:",
                target_sha,
                "Second Brain:",
                brain_revision,
                "frontier:",
                candidate_set_sha256,
                flush=True,
            )
            return
        except Exception as error:  # live build may still be warming
            last_error = error
            if attempt == 23:
                break
            print(
                "Live verification retry:",
                type(error).__name__,
                error,
                flush=True,
            )
            time.sleep(10)
    raise RuntimeError(
        "creator-profile Living Anatomy v7 live verification failed"
    ) from last_error


def main() -> None:
    hf_token = os.environ.get("HF_TOKEN", "")
    github_token = os.environ.get("GITHUB_TOKEN", "")
    source_revision = os.environ.get("GITHUB_SHA", "").lower()
    source_ref = os.environ.get("GITHUB_REF", "")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    workflow_run_id = os.environ.get("GITHUB_RUN_ID", "")

    if not hf_token:
        raise RuntimeError("HF_TOKEN is unavailable")
    if not github_token:
        raise RuntimeError("GITHUB_TOKEN is unavailable")
    if len(source_revision) != 40 or any(
        character not in "0123456789abcdef" for character in source_revision
    ):
        raise RuntimeError("GITHUB_SHA is not an exact revision")
    if source_ref != "refs/heads/main":
        raise RuntimeError(f"refusing production deploy from {source_ref!r}")
    if repository != EXPECTED_REPOSITORY:
        raise RuntimeError(f"unexpected GitHub repository: {repository!r}")
    if not workflow_run_id.isdigit():
        raise RuntimeError("GITHUB_RUN_ID is not numeric")
    if current_protected_main(repository, github_token) != source_revision:
        raise RuntimeError("refusing stale deployment at the mutation boundary")

    brain_source = json.loads(
        Path(".runtime/second-brain/source.json").read_text(encoding="utf-8")
    )
    brain_revision = str(brain_source.get("source_revision") or "").lower()
    candidate_set_sha256 = str(
        brain_source.get("frontier_candidate_set_sha256") or ""
    ).lower()
    frontier_candidate_count = int(
        brain_source.get("frontier_candidate_count") or 0
    )
    frontier_source_count = int(brain_source.get("frontier_source_count") or 0)
    if len(brain_revision) != 40:
        raise RuntimeError("Second Brain snapshot lacks an exact source revision")
    if int(brain_source.get("public_chunk_count") or 0) != EXPECTED_PUBLIC_CHUNKS:
        raise RuntimeError("Second Brain snapshot must contain 575 public chunks")
    if frontier_candidate_count < MIN_FRONTIER_CANDIDATES:
        raise RuntimeError("Second Brain frontier candidate set is incomplete")
    if frontier_source_count < MIN_FRONTIER_SOURCES:
        raise RuntimeError("Second Brain frontier source inventory is incomplete")
    if len(candidate_set_sha256) != 64:
        raise RuntimeError("Second Brain frontier candidate-set digest is invalid")
    if brain_source.get("formula_counts") != {
        "attributed": EXPECTED_ATTRIBUTED_FORMULAS,
        "executable": EXPECTED_EXECUTABLE_FORMULAS,
        "locked_proven": EXPECTED_LOCKED_PROVEN,
    }:
        raise RuntimeError("Second Brain formula authority counts drifted")
    if int(brain_source.get("quant_domain_count") or 0) != EXPECTED_QUANT_DOMAINS:
        raise RuntimeError("Second Brain quant domain count drifted")
    expected_zero_authority = {
        "private_graph_nodes_materialized": 0,
        "raw_graph_nodes_admitted_to_gradients": 0,
        "training_authority": "NONE",
        "promotion_authority": "NONE",
        "execution_authority": "NONE",
        "merge_authority": "NONE",
        "lambda_state": "CONJECTURE_1",
    }
    for key, value in expected_zero_authority.items():
        if brain_source.get(key) != value:
            raise RuntimeError(f"Second Brain snapshot authority drift: {key}")

    api = HfApi(token=hf_token)
    identity = api.whoami(token=hf_token)
    identity_name = str(identity.get("name") or identity.get("fullname") or "")
    if identity_name.lower() != EXPECTED_IDENTITY:
        raise RuntimeError(
            f"wrong Hugging Face identity: expected {EXPECTED_IDENTITY}, "
            f"got {identity_name!r}"
        )
    ensure_destination(api)

    deploy_manifest = {
        "schema": "szl.hf-deploy-manifest/v1",
        "source_repository": EXPECTED_REPOSITORY,
        "source_revision": source_revision,
        "source_path": "",
        "destination": {
            "repo_id": SPACE_ID,
            "repo_type": "space",
            "mode": "creator-profile-runtime-whitelist",
            "visibility": "public",
            "lifecycle": "PUBLIC_CREATIVE",
        },
        "dependencies": {
            "second_brain": {
                "source_repository": brain_source["source_repository"],
                "source_revision": brain_revision,
                "public_chunk_count": brain_source["public_chunk_count"],
                "corpus_sha256": brain_source["corpus_sha256"],
                "frontier_candidate_count": frontier_candidate_count,
                "frontier_source_count": brain_source["frontier_source_count"],
                "frontier_candidate_set_sha256": candidate_set_sha256,
                "frontier_state_sha256": brain_source["frontier_state_sha256"],
                "frontier_candidates_sha256": brain_source[
                    "frontier_candidates_sha256"
                ],
                "formula_counts": brain_source["formula_counts"],
                "quant_domain_count": brain_source["quant_domain_count"],
                "lambda_state": "CONJECTURE_1",
                "candidate_state": "DISCOVERED_REVIEW_REQUIRED",
                "authority_state": "READ_ONLY",
                "content_access": "HANDLES_ONLY",
                "training_authority": "NONE",
                "promotion_authority": "NONE",
                "execution_authority": "NONE",
                "merge_authority": "NONE",
            }
        },
        "workflow_run_id": workflow_run_id,
    }


    observed_manifest = live_deploy_manifest()
    if deployment_inputs_match(observed_manifest, deploy_manifest):
        info = api.repo_info(repo_id=SPACE_ID, repo_type="space")
        current_sha = str(getattr(info, "sha", "") or "")
        observed_run_id = str(observed_manifest.get("workflow_run_id") or "")
        if len(current_sha) != 40:
            raise RuntimeError("reusable creator-profile revision is invalid")
        if not observed_run_id.isdigit():
            raise RuntimeError("reusable deployment manifest lacks a workflow run ID")
        print(
            "NOOP: exact Anatomy, Brain, frontier, formula, and quant inputs are "
            f"already deployed at {current_sha}; verifying and preserving revision.",
            flush=True,
        )
        wait_running(api, current_sha)
        verify_live(
            source_revision,
            current_sha,
            brain_revision,
            observed_run_id,
            candidate_set_sha256,
            frontier_candidate_count,
            frontier_source_count,
        )
        return

    operations = [
        CommitOperationAdd(path_in_repo=path, path_or_fileobj=path)
        for path in runtime_files()
    ]
    operations.append(
        CommitOperationAdd(
            path_in_repo="hf-deploy-manifest.json",
            path_or_fileobj=(
                json.dumps(deploy_manifest, sort_keys=True, indent=2) + "\n"
            ).encode("utf-8"),
        )
    )
    commit = api.create_commit(
        repo_id=SPACE_ID,
        repo_type="space",
        operations=operations,
        commit_message=(
            f"hf-sync: source {source_revision} "
            f"run {workflow_run_id}"
        ),
    )
    target_sha = str(commit.oid)
    if len(target_sha) != 40:
        raise RuntimeError(f"invalid destination revision: {target_sha!r}")
    wait_running(api, target_sha)
    verify_live(
        source_revision,
        target_sha,
        brain_revision,
        workflow_run_id,
        candidate_set_sha256,
        frontier_candidate_count,
        frontier_source_count,
    )


if __name__ == "__main__":
    main()
