#!/usr/bin/env python3
"""Publish Living Anatomy to Stephen's public Hugging Face creator profile.

GitHub protected main is authoritative. The workflow materializes the exact
public Second Brain projection first, uploads only the runtime whitelist,
keeps the Space public/running, and verifies live source-bound contracts.
"""
from __future__ import annotations

import glob
import json
import os
import time
import urllib.request
from pathlib import Path

from huggingface_hub import CommitOperationAdd, HfApi

SPACE_ID = "betterwithage/anatomy"
EXPECTED_IDENTITY = "betterwithage"
EXPECTED_REPOSITORY = "szl-holdings/anatomy"
LIVE_BASE = "https://betterwithage-anatomy.hf.space"


def stage_name(runtime: object) -> str:
    value = getattr(runtime, "stage", None)
    return str(getattr(value, "value", value) or "UNKNOWN").upper()


def get_json(url: str, timeout: int = 20) -> dict:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "szl-anatomy-creator-sync/1.0"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def current_protected_main(repository: str, token: str) -> str:
    request = urllib.request.Request(
        os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
        + f"/repos/{repository}/commits/main",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "szl-anatomy-creator-sync/1.0",
        },
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        return str(json.load(response).get("sha") or "").lower()


def runtime_files() -> list[str]:
    patterns = [
        "README.md",
        "Dockerfile",
        ".dockerignore",
        "server.py",
        "organ_integrity.py",
        "living_runtime.py",
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
        "server.py",
        "living_runtime.py",
        "second_brain_runtime.py",
        ".runtime/second-brain/manifest.json",
        ".runtime/second-brain/brain-corpus.public.jsonl",
        ".runtime/second-brain/source.json",
    }
    missing = sorted(required - files)
    if missing:
        raise RuntimeError(f"required Living Anatomy artifacts missing: {missing}")
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


def verify_live(
    source_revision: str,
    target_sha: str,
    brain_revision: str,
    workflow_run_id: str,
) -> None:
    last_error: Exception | None = None
    for attempt in range(24):
        try:
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
            version = get_json(LIVE_BASE + "/version?refresh=1")
            evidence = get_json(LIVE_BASE + "/evidence?refresh=1", timeout=25)
            source = get_json(
                LIVE_BASE + "/.well-known/szl-source.json?refresh=1"
            )

            assert health["transport_state"] == "REACHABLE"
            assert living["ready"] is True
            assert living["organs"]["brain"]["chunk_count"] == 575
            assert brain["ready"] is True
            assert brain["source_revision"] == brain_revision
            assert brain["chunk_count"] == 575
            assert brain["private_graph_nodes_loaded"] == 0
            assert brain["content_access"] == "HANDLES_ONLY"
            assert search["ready"] is True
            assert search["handles"]
            assert all("text" not in handle for handle in search["handles"])
            assert version["gitSha"] == source_revision
            assert version["deploymentRevision"] == target_sha
            assert version["secondBrainSourceRevision"] == brain_revision
            assert evidence["gitSha"] == source_revision
            assert evidence["source"]["deployment"]["hf_revision"] == target_sha
            assert source["deployment"]["hf_revision"] == target_sha
            assert source["source"]["commit"] == source_revision
            assert source["deployment"]["workflow_run_id"] == workflow_run_id
            print(
                "Verified creator-profile Living Anatomy:",
                target_sha,
                "Second Brain:",
                brain_revision,
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
        "creator-profile Living Anatomy live verification failed"
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
    if len(brain_revision) != 40:
        raise RuntimeError("Second Brain snapshot lacks an exact source revision")
    if int(brain_source.get("public_chunk_count") or 0) != 575:
        raise RuntimeError("Second Brain snapshot must contain 575 public chunks")
    if brain_source.get("private_graph_nodes_materialized") != 0:
        raise RuntimeError("private Second Brain nodes entered the public snapshot")

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
                "authority_state": "READ_ONLY",
                "content_access": "HANDLES_ONLY",
            }
        },
        "workflow_run_id": workflow_run_id,
    }

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
            f"hf-sync: creator profile source {source_revision} "
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
    )


if __name__ == "__main__":
    main()
