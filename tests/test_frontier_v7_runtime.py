from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from frontier_v7_runtime import FrontierV7Snapshot, install_frontier_v7_routes
from scripts.materialize_frontier_memory import (
    FrontierMaterializationError,
    canonical_bytes,
    validate_snapshot,
)


REVISION = "a" * 40


def candidate(
    candidate_id: str,
    *,
    kind: str,
    repository: str,
    title: str,
    quant_domain: str | None = None,
) -> dict:
    content = f"{title}. Source-bound review candidate for {kind}."
    row = {
        "schema": "szl.second-brain.frontier-candidate/v1",
        "id": candidate_id,
        "title": title,
        "content": content,
        "content_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "source_repository": repository,
        "source_revision": REVISION,
        "source_path": "fixture/source.json",
        "source_kind": kind,
        "admission": "DISCOVERED_REVIEW_REQUIRED",
        "candidate_state": "DISCOVERED_REVIEW_REQUIRED",
        "content_access": "CONTROLLER_ONLY",
    }
    if quant_domain:
        row["quant_domain"] = quant_domain
    return row


def snapshot_bytes() -> tuple[bytes, bytes]:
    rows = [
        candidate(
            "frontier:" + "1" * 32,
            kind="attributed-formula",
            repository="szl-holdings/szl-formulas",
            title="Fisher-Rao information geometry",
            quant_domain="information_geometry",
        ),
        candidate(
            "frontier:" + "2" * 32,
            kind="source-document",
            repository="szl-holdings/ouroboros",
            title="Bounded loop convergence",
        ),
        candidate(
            "frontier:" + "3" * 32,
            kind="source-document",
            repository="szl-holdings/anatomy",
            title="Living Anatomy source contract",
        ),
    ]
    candidates_raw = b"".join(canonical_bytes(row) + b"\n" for row in rows)
    state = {
        "schema": "szl.second-brain.frontier-state/v1",
        "state": "REVIEW_REQUIRED",
        "candidate_count": len(rows),
        "candidate_set_sha256": hashlib.sha256(candidates_raw).hexdigest(),
        "source_count": 6,
        "sources": [
            {
                "source_id": "living_anatomy",
                "repository": "szl-holdings/anatomy",
                "revision": REVISION,
                "path": "README.md",
                "parser": "markdown",
                "content_sha256": "b" * 64,
                "candidate_count": 1,
            }
        ],
        "public_content_access": "HANDLES_ONLY",
        "controller_content_access": "AUTHORIZED_CONTROLLER_ONLY",
        "private_graph_nodes_loaded": 0,
        "raw_graph_nodes_admitted_to_gradients": 0,
        "training_authority": "NONE",
        "promotion_authority": "NONE",
        "execution_authority": "NONE",
        "merge_authority": "NONE",
        "lambda": "CONJECTURE_1",
    }
    return (
        (json.dumps(state, sort_keys=True, indent=2) + "\n").encode("utf-8"),
        candidates_raw,
    )


class FrontierMaterializerTests(unittest.TestCase):
    def test_snapshot_validation_replays_all_digests_and_boundaries(self) -> None:
        state_raw, candidate_raw = snapshot_bytes()
        result = validate_snapshot(state_raw, candidate_raw)
        self.assertEqual(result["candidate_count"], 3)
        self.assertEqual(result["source_count"], 6)
        self.assertEqual(
            result["candidate_set_sha256"], hashlib.sha256(candidate_raw).hexdigest()
        )
        self.assertEqual(result["training_authority"], "NONE")
        self.assertEqual(result["promotion_authority"], "NONE")
        self.assertEqual(result["execution_authority"], "NONE")
        self.assertEqual(result["private_graph_nodes_loaded"], 0)
        self.assertEqual(result["lambda"], "CONJECTURE_1")

    def test_snapshot_validation_fails_on_promoted_candidate(self) -> None:
        state_raw, candidate_raw = snapshot_bytes()
        rows = [json.loads(line) for line in candidate_raw.splitlines()]
        rows[0]["candidate_state"] = "PROMOTED"
        tampered = b"".join(canonical_bytes(row) + b"\n" for row in rows)
        with self.assertRaisesRegex(
            FrontierMaterializationError, "candidate was promoted"
        ):
            validate_snapshot(state_raw, tampered)

    def test_snapshot_validation_rejects_secret_like_material_without_echo(self) -> None:
        state_raw, candidate_raw = snapshot_bytes()
        rows = [json.loads(line) for line in candidate_raw.splitlines()]
        secret = "sk-" + "X" * 32
        rows[0]["content"] = secret
        rows[0]["content_sha256"] = hashlib.sha256(secret.encode()).hexdigest()
        tampered = b"".join(canonical_bytes(row) + b"\n" for row in rows)
        state = json.loads(state_raw)
        state["candidate_set_sha256"] = hashlib.sha256(tampered).hexdigest()
        state_raw = (json.dumps(state) + "\n").encode()
        with self.assertRaisesRegex(
            FrontierMaterializationError, "secret-like material was rejected"
        ) as context:
            validate_snapshot(state_raw, tampered)
        self.assertNotIn(secret, str(context.exception))


class FrontierV7RuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        directory = Path(self.temporary.name)
        state_raw, candidate_raw = snapshot_bytes()
        (directory / "frontier-state.v1.json").write_bytes(state_raw)
        (directory / "frontier-candidates.public.jsonl").write_bytes(candidate_raw)
        app = FastAPI()
        install_frontier_v7_routes(app, snapshot=FrontierV7Snapshot(directory))
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def assert_handles_only(self, payload: dict) -> None:
        serialized = json.dumps(payload, sort_keys=True).lower()
        self.assertNotIn('"content"', serialized)
        self.assertNotIn('"text"', serialized)
        for handle in payload.get("handles", []):
            self.assertEqual(handle["contentAccess"], "HANDLES_ONLY")
            self.assertEqual(
                handle["candidateState"], "DISCOVERED_REVIEW_REQUIRED"
            )
            self.assertRegex(handle["nodeId"], r"^frontier:[0-9a-f]{32}$")
            self.assertRegex(handle["sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(handle["revision"], r"^[0-9a-f]{40}$")

    def test_health_exposes_exact_counts_without_candidate_content(self) -> None:
        response = self.client.get("/api/anatomy/v1/frontier-health")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ready"])
        self.assertEqual(payload["state"], "REVIEW_REQUIRED")
        self.assertEqual(payload["candidate_count"], 3)
        self.assertEqual(payload["source_revision"], REVISION)
        self.assertEqual(payload["training_authority"], "NONE")
        self.assertEqual(payload["execution_authority"], "NONE")
        self.assertEqual(payload["private_graph_nodes_loaded"], 0)
        self.assertEqual(payload["lambda"], "CONJECTURE_1")
        self.assert_handles_only(payload)

    def test_frontier_formula_quant_and_ouroboros_routes_are_filtered(self) -> None:
        routes = {
            "/api/anatomy/v1/brain/frontier": 3,
            "/api/anatomy/v1/brain/formulas": 1,
            "/api/anatomy/v1/brain/quant": 1,
            "/api/anatomy/v1/brain/ouroboros": 1,
        }
        for route, expected in routes.items():
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertEqual(len(payload["handles"]), expected)
                self.assertEqual(payload["state"], "REVIEW_REQUIRED")
                self.assertEqual(payload["execution_authority"], "NONE")
                self.assert_handles_only(payload)

    def test_formula_route_preserves_locked_eight_and_lambda_boundary(self) -> None:
        payload = self.client.get("/api/anatomy/v1/brain/formulas").json()
        self.assertEqual(payload["locked_proven_count"], 8)
        self.assertEqual(
            set(payload["locked_proven_ids"]),
            {"F1", "F4", "F7", "F11", "F12", "F18", "F19", "F22"},
        )
        self.assertEqual(payload["f_number_mapping"], "UNKNOWN_NOT_INFERRED")
        self.assertEqual(payload["lambda"], "CONJECTURE_1")

    def test_unavailable_snapshot_fails_closed_without_synthetic_handles(self) -> None:
        with tempfile.TemporaryDirectory() as empty:
            app = FastAPI()
            install_frontier_v7_routes(
                app,
                snapshot=FrontierV7Snapshot(Path(empty)),
            )
            payload = TestClient(app).get(
                "/api/anatomy/v1/brain/frontier"
            ).json()
        self.assertFalse(payload["ready"])
        self.assertEqual(payload["state"], "UNAVAILABLE")
        self.assertEqual(payload["handles"], [])
        self.assertEqual(payload["content_access"], "HANDLES_ONLY")


class BrainV7AssetTests(unittest.TestCase):
    def test_assets_are_same_origin_and_accessible(self) -> None:
        script = Path("brain-v7.js").read_text(encoding="utf-8")
        style = Path("brain-v7.css").read_text(encoding="utf-8")
        self.assertNotIn("https://", script)
        self.assertNotIn("http://", script)
        self.assertIn('credentials: "same-origin"', script)
        self.assertIn('redirect: "error"', script)
        self.assertIn("CONTENT_BOUNDARY_VIOLATION", script)
        self.assertIn("prefers-reduced-motion", script)
        self.assertIn("aria-modal", script)
        self.assertIn("env(safe-area-inset-bottom)", style)
        self.assertIn("@media (max-width: 640px)", style)
        self.assertIn("@media (forced-colors: active)", style)
        self.assertIn("@media (prefers-reduced-motion: reduce)", style)

    def test_index_loads_one_v7_style_and_script(self) -> None:
        html = Path("index.html").read_text(encoding="utf-8")
        self.assertEqual(html.count('data-szl-brain-v7="style"'), 1)
        self.assertEqual(html.count('data-szl-brain-v7="script"'), 1)
        self.assertIn('href="/brain-v7.css"', html)
        self.assertIn('src="/brain-v7.js"', html)

    def test_living_runtime_installs_v7_routes_once(self) -> None:
        runtime = Path("living_runtime.py").read_text(encoding="utf-8")
        self.assertEqual(runtime.count("install_frontier_v7_routes(app)"), 1)
        self.assertIn("from frontier_v7_runtime import", runtime)

    def test_creator_publisher_contains_all_v7_runtime_files(self) -> None:
        publisher = Path("scripts/sync_hf_creator_profile.py").read_text(
            encoding="utf-8"
        )
        workflow = Path(".github/workflows/hf-sync.yml").read_text(
            encoding="utf-8"
        )
        for filename in (
            "frontier_v7_runtime.py",
            "brain-v7.js",
            "brain-v7.css",
        ):
            self.assertIn(f'"{filename}"', publisher)
        self.assertIn("scripts/materialize_frontier_memory.py", workflow)
        self.assertIn("frontier-state.v1.json", publisher)
        self.assertIn("frontier-candidates.public.jsonl", publisher)
        self.assertIn("frontier-source.json", publisher)


if __name__ == "__main__":
    unittest.main()
