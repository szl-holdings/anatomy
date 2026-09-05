from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from typing import Any
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from second_brain_runtime import PublicSecondBrain  # noqa: E402


QUANT_DOMAINS = [
    "algebra_number_theory",
    "coding_error_control",
    "dynamics_consensus",
    "energy_entropy_physics",
    "governance_receipts",
    "information_geometry",
    "narrative_lineage",
    "topology_geometry",
    "trust_aggregation",
]


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def frontier_row(
    stable: str,
    *,
    title: str,
    content: str,
    kind: str,
    repository: str = "szl-holdings/szl-formulas",
    path: str = "fixture/source.md",
    quant_domain: str | None = None,
    admission: str = "DISCOVERED_REVIEW_REQUIRED",
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "schema": "szl.second-brain.frontier-candidate/v1",
        "id": "frontier:" + hashlib.sha256(stable.encode()).hexdigest()[:32],
        "title": title,
        "content": content,
        "content_sha256": hashlib.sha256(content.encode()).hexdigest(),
        "source_repository": repository,
        "source_revision": hashlib.sha1(repository.encode()).hexdigest(),
        "source_path": path,
        "source_kind": kind,
        "admission": admission,
        "candidate_state": "DISCOVERED_REVIEW_REQUIRED",
        "content_access": "CONTROLLER_ONLY",
    }
    if quant_domain:
        row["quant_domain"] = quant_domain
    return row


class PublicSecondBrainTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.snapshot = Path(self.temporary.name)
        sources = (
            ["doc"] * 152
            + ["formula"] * 269
            + ["ingest"] * 143
            + ["invariant"] * 11
        )
        rows = []
        for index, source in enumerate(sources):
            text = (
                f"governed receipt living anatomy second brain {index} {source}"
                if index < 8
                else f"public knowledge chunk {index} {source}"
            )
            rows.append(
                {
                    "id": f"{source}:fixture:{index:04d}",
                    "source": source,
                    "sourceId": f"{source}-{index}",
                    "title": f"Fixture {source} {index}",
                    "text": text,
                    "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                }
            )
        corpus_raw = b"".join(canonical_bytes(row) + b"\n" for row in rows)
        manifest = {
            "datasetName": "test public projection",
            "publicChunkCount": 575,
            "bySource": {
                "doc": 152,
                "formula": 269,
                "ingest": 143,
                "invariant": 11,
            },
            "projectionSha256": "test-only",
            "secretScan": "PASS",
        }
        manifest_raw = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")

        formula_authority = {
            "executable_registry_repository": "szl-holdings/szl-formulas",
            "executable_registry_count": 21,
            "locked_proven_count": 8,
            "locked_proven_ids": [
                "F1",
                "F11",
                "F12",
                "F18",
                "F19",
                "F22",
                "F4",
                "F7",
            ],
            "lambda_status": "CONJECTURE_1_OPEN_ADVISORY_ONLY",
            "f_number_to_executable_registry_mapping": "UNKNOWN_NOT_INFERRED",
        }
        frontier_rows = [
            frontier_row(
                "authority",
                title="SZL formula authority and proof boundary",
                content=json.dumps(formula_authority, sort_keys=True),
                kind="formula-authority",
                admission="REFERENCE_AND_CONSTRAINT_INPUT_ONLY",
            )
        ]
        for index in range(30):
            domain = QUANT_DOMAINS[index % len(QUANT_DOMAINS)]
            frontier_rows.append(
                frontier_row(
                    f"attributed-{index}",
                    title=f"Attributed formula F{index + 1}",
                    content=(
                        f"Formula F{index + 1}; quant domain {domain}; "
                        "reported status retained; review required."
                    ),
                    kind="attributed-formula",
                    quant_domain=domain,
                    admission="REFERENCE_AND_CONSTRAINT_INPUT_ONLY",
                )
            )
        for index in range(21):
            frontier_rows.append(
                frontier_row(
                    f"executable-{index}",
                    title=f"Executable formula kernel_{index}",
                    content=(
                        f"Executable formula kernel_{index}; per-obligation status; "
                        "no inferred F-number mapping."
                    ),
                    kind="executable-formula",
                    admission="EXECUTABLE_CONSTRAINT_REVIEW_REQUIRED",
                )
            )
        for domain in QUANT_DOMAINS:
            frontier_rows.append(
                frontier_row(
                    f"domain-{domain}",
                    title=f"Quant domain {domain}",
                    content=f"Quant domain {domain}; reference and constraint input only.",
                    kind="quant-domain",
                    quant_domain=domain,
                    admission="REFERENCE_AND_CONSTRAINT_INPUT_ONLY",
                )
            )
        for index in range(10):
            repository = (
                "szl-holdings/ouroboros"
                if index < 4
                else "szl-holdings/anatomy"
            )
            frontier_rows.append(
                frontier_row(
                    f"source-{index}",
                    title=f"Source document {index}",
                    content=(
                        "Ouroboros bounded loop convergence termination receipt closure Codex"
                        if index < 4
                        else "Living Anatomy holographic brain frontier observation"
                    ),
                    kind="source-document",
                    repository=repository,
                    path=(f"fixture/source-{index}.md" if 4 <= index < 8 else "fixture/source.md"),
                )
            )
        frontier_rows.sort(key=lambda row: row["id"])
        source_bindings = sorted({
            (row["source_repository"], row["source_revision"], row["source_path"])
            for row in frontier_rows
        })
        frontier_sources = [
            {
                "source_id": "ouroboros_runtime" if binding[0].endswith("/ouroboros") else f"source_{index}",
                "repository": binding[0],
                "revision": binding[1],
                "path": binding[2],
                "parser": "markdown",
                "content_sha256": hashlib.sha256(canonical_bytes(binding)).hexdigest(),
                "candidate_count": sum(
                    (row["source_repository"], row["source_revision"], row["source_path"]) == binding
                    for row in frontier_rows
                ),
            }
            for index, binding in enumerate(source_bindings)
        ]
        frontier_candidates_raw = b"".join(
            canonical_bytes(row) + b"\n" for row in frontier_rows
        )
        candidate_set_sha256 = hashlib.sha256(frontier_candidates_raw).hexdigest()
        source_kind_counts = {
            "formula-authority": 1,
            "attributed-formula": 30,
            "executable-formula": 21,
            "quant-domain": 9,
            "source-document": 10,
        }
        quant_domain_counts = {
            domain: sum(
                1 for row in frontier_rows if row.get("quant_domain") == domain
            )
            for domain in QUANT_DOMAINS
        }
        frontier_state = {
            "schema": "szl.second-brain.frontier-state/v1",
            "state": "REVIEW_REQUIRED",
            "candidate_count": len(frontier_rows),
            "candidate_set_sha256": candidate_set_sha256,
            "source_count": len(frontier_sources),
            "sources": frontier_sources,
            "source_kind_counts": source_kind_counts,
            "quant_domain_counts": quant_domain_counts,
            "public_content_access": "HANDLES_ONLY",
            "controller_content_access": "AUTHORIZED_CONTROLLER_ONLY",
            "private_graph_nodes_loaded": 0,
            "raw_graph_nodes_admitted_to_gradients": 0,
            "training_authority": "NONE",
            "promotion_authority": "NONE",
            "execution_authority": "NONE",
            "merge_authority": "NONE",
            "lambda": "CONJECTURE_1",
            "learning_definition": (
                "Content-addressed public-source candidates are proposed for human review."
            ),
            "state_sha256": "c" * 64,
        }
        frontier_state_raw = (
            json.dumps(frontier_state, sort_keys=True, indent=2) + "\n"
        ).encode("utf-8")
        source = {
            "schema": "szl.second-brain.snapshot/v1",
            "source_repository": "szl-holdings/szl-second-brain",
            "source_revision": "a" * 40,
            "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
            "corpus_sha256": hashlib.sha256(corpus_raw).hexdigest(),
            "public_chunk_count": 575,
            "frontier_state_sha256": hashlib.sha256(frontier_state_raw).hexdigest(),
            "frontier_candidates_sha256": hashlib.sha256(
                frontier_candidates_raw
            ).hexdigest(),
            "frontier_candidate_count": len(frontier_rows),
            "frontier_source_count": len(frontier_sources),
            "frontier_candidate_set_sha256": candidate_set_sha256,
            "private_graph_nodes_materialized": 0,
            "raw_graph_nodes_admitted_to_gradients": 0,
            "training_authority": "NONE",
            "promotion_authority": "NONE",
            "execution_authority": "NONE",
            "merge_authority": "NONE",
            "lambda_state": "CONJECTURE_1",
        }
        (self.snapshot / "manifest.json").write_bytes(manifest_raw)
        (self.snapshot / "brain-corpus.public.jsonl").write_bytes(corpus_raw)
        (self.snapshot / "frontier-state.v1.json").write_bytes(frontier_state_raw)
        (self.snapshot / "frontier-candidates.public.jsonl").write_bytes(
            frontier_candidates_raw
        )
        (self.snapshot / "source.json").write_text(
            json.dumps(source, indent=2) + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _rewrite_frontier(self, state: dict[str, Any], rows: list[dict[str, Any]]) -> None:
        candidates_raw = b"".join(canonical_bytes(row) + b"\n" for row in rows)
        state["candidate_count"] = len(rows)
        state["candidate_set_sha256"] = hashlib.sha256(candidates_raw).hexdigest()
        state_raw = canonical_bytes(state) + b"\n"
        source = json.loads((self.snapshot / "source.json").read_text(encoding="utf-8"))
        source.update({
            "frontier_state_sha256": hashlib.sha256(state_raw).hexdigest(),
            "frontier_candidates_sha256": hashlib.sha256(candidates_raw).hexdigest(),
            "frontier_candidate_set_sha256": state["candidate_set_sha256"],
            "frontier_candidate_count": len(rows),
            "frontier_source_count": state["source_count"],
        })
        (self.snapshot / "frontier-state.v1.json").write_bytes(state_raw)
        (self.snapshot / "frontier-candidates.public.jsonl").write_bytes(candidates_raw)
        (self.snapshot / "source.json").write_bytes(canonical_bytes(source) + b"\n")

    def _frontier_fixture(self) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        state = json.loads((self.snapshot / "frontier-state.v1.json").read_text(encoding="utf-8"))
        rows = [
            json.loads(line)
            for line in (self.snapshot / "frontier-candidates.public.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        return state, rows

    def _assert_frontier_rejected(self, state: dict[str, Any], rows: list[dict[str, Any]]) -> None:
        import scripts.materialize_second_brain as materializer

        self._rewrite_frontier(state, rows)
        with self.assertRaisesRegex(ValueError, "frontier.*source"):
            materializer.validate_frontier_snapshot(
                (self.snapshot / "frontier-state.v1.json").read_bytes(),
                (self.snapshot / "frontier-candidates.public.jsonl").read_bytes(),
            )
        health = PublicSecondBrain(self.snapshot).health()
        self.assertFalse(health["ready"])
        self.assertIn("source", str(health["load_error"]))

    def test_additive_eighth_source_materializes_and_serves(self) -> None:
        import scripts.materialize_second_brain as materializer

        state, rows = self._frontier_fixture()
        row = frontier_row(
            "additional-source",
            title="Additional reviewed-source candidate",
            content="Public-source candidate awaiting review.",
            kind="source-document",
            repository="szl-holdings/additional-source",
        )
        rows.append(row)
        rows.sort(key=lambda candidate: candidate["id"])
        state["sources"].append({
            "source_id": "additional_source",
            "repository": row["source_repository"],
            "revision": row["source_revision"],
            "path": row["source_path"],
            "parser": "markdown",
            "content_sha256": row["content_sha256"],
            "candidate_count": 1,
        })
        state["source_count"] = len(state["sources"])
        state["source_kind_counts"]["source-document"] += 1
        self._rewrite_frontier(state, rows)
        output = self.snapshot / "additive-materialized"
        with patch.object(materializer, "resolve_revision", return_value="a" * 40), patch.object(
            materializer,
            "request_bytes",
            side_effect=lambda url, **kwargs: (self.snapshot / url.rsplit("/", 1)[1]).read_bytes(),
        ):
            materializer.materialize(output)
        brain = PublicSecondBrain(output)
        self.assertTrue(brain.ready, brain.health()["load_error"])
        self.assertEqual(8, brain.health()["frontier"]["source_count"])
        self.assertEqual(72, brain.health()["frontier"]["candidate_count"])
        self.assertTrue(brain.frontier_search("additional reviewed source")["handles"])

    def test_manifest_metadata_must_bind_each_candidate_group(self) -> None:
        state, rows = self._frontier_fixture()
        for field, value in (
            ("repository", "szl-holdings/unrelated"),
            ("revision", "f" * 40),
            ("path", "unrelated/path.md"),
        ):
            with self.subTest(field=field):
                changed = deepcopy(state)
                changed["sources"][0][field] = value
                self._assert_frontier_rejected(changed, rows)

    def test_per_source_counts_reject_redistribution_with_same_total(self) -> None:
        state, rows = self._frontier_fixture()
        donor = next(source for source in state["sources"] if source["candidate_count"] > 1)
        recipient = next(source for source in state["sources"] if source is not donor)
        donor["candidate_count"] -= 1
        recipient["candidate_count"] += 1
        self._assert_frontier_rejected(state, rows)

    def test_duplicate_source_binding_rejected_even_with_unique_id(self) -> None:
        state, rows = self._frontier_fixture()
        duplicate = deepcopy(state["sources"][0])
        duplicate["source_id"] = "duplicate_binding"
        state["sources"].append(duplicate)
        state["source_count"] += 1
        self._assert_frontier_rejected(state, rows)

    def test_source_counts_require_integers(self) -> None:
        state, rows = self._frontier_fixture()
        for count in (True, 1.5, "1"):
            with self.subTest(count=count):
                changed = deepcopy(state)
                changed["sources"][0]["candidate_count"] = count
                self._assert_frontier_rejected(changed, rows)

    def test_dropping_one_of_seven_sources_fails_closed(self) -> None:
        state, rows = self._frontier_fixture()
        removed = next(source for source in state["sources"] if source["candidate_count"] == 1)
        state["sources"].remove(removed)
        state["source_count"] -= 1
        remaining = [
            row for row in rows
            if (row["source_repository"], row["source_revision"], row["source_path"])
            != (removed["repository"], removed["revision"], removed["path"])
        ]
        self.assertEqual(70, len(remaining))
        self._assert_frontier_rejected(state, remaining)

    def test_runtime_rejects_missing_or_stale_receipt_source_count(self) -> None:
        receipt_path = self.snapshot / "source.json"
        original = json.loads(receipt_path.read_text(encoding="utf-8"))
        for count in (None, 6, 8, "7", True):
            with self.subTest(count=count):
                receipt = deepcopy(original)
                if count is None:
                    receipt.pop("frontier_source_count")
                else:
                    receipt["frontier_source_count"] = count
                receipt_path.write_bytes(canonical_bytes(receipt) + b"\n")
                health = PublicSecondBrain(self.snapshot).health()
                self.assertFalse(health["ready"])
                self.assertIn("source receipt count mismatch", str(health["load_error"]))

    def test_source_bound_snapshot_loads_retrieval_and_frontier(self) -> None:
        brain = PublicSecondBrain(self.snapshot)
        health = brain.health()
        self.assertTrue(health["ready"])
        self.assertEqual(575, health["chunk_count"])
        self.assertEqual("a" * 40, health["source_revision"])
        self.assertEqual("HANDLES_ONLY", health["content_access"])
        self.assertEqual(0, health["private_graph_nodes_loaded"])
        self.assertEqual(71, health["frontier"]["candidate_count"])
        self.assertEqual(7, health["frontier"]["source_count"])
        self.assertEqual(30, health["formula_atlas"]["attributed_formula_count"])
        self.assertEqual(21, health["formula_atlas"]["executable_formula_count"])
        self.assertEqual(8, health["formula_atlas"]["locked_proven_count"])
        self.assertEqual(9, health["quant_domain_count"])
        self.assertEqual(
            {"doc": 152, "formula": 269, "ingest": 143, "invariant": 11},
            health["by_source"],
        )

    def test_materializer_receipt_loads_holographic_routes(self) -> None:
        import frontier_runtime
        import scripts.materialize_second_brain as materializer
        from fastapi.testclient import TestClient

        output = self.snapshot / "materialized"
        with patch.object(materializer, "resolve_revision", return_value="a" * 40), patch.object(
            materializer,
            "request_bytes",
            side_effect=lambda url, **kwargs: (self.snapshot / url.rsplit("/", 1)[1]).read_bytes(),
        ):
            materializer.materialize(output)

        with patch.multiple(
            frontier_runtime,
            STATE_PATH=output / "frontier-state.v1.json",
            CANDIDATES_PATH=output / "frontier-candidates.public.jsonl",
            SOURCE_PATH=output / "source.json",
            ATLAS=frontier_runtime.FrontierAtlas(),
        ):
            client = TestClient(frontier_runtime.app)
            response = client.get("/api/anatomy/v1/holographic-v7")
            self.assertEqual(200, response.status_code)
            self.assertEqual("SOURCE_BOUND_READ_ONLY", response.json()["state"])
            formulas = client.get("/api/anatomy/v1/frontier/formulas?k=48")
            self.assertEqual(200, formulas.status_code)
            payload = formulas.json()
            self.assertEqual(61, payload["matched_count"])
            self.assertEqual(48, payload["returned_count"])
            self.assertEqual(48, len(payload["handles"]))
            self.assertTrue(all(handle["authority"] == "NONE" for handle in payload["handles"]))
            self.assertNotIn('"content"', formulas.text)
            self.assertNotIn('"text"', formulas.text)

            source = json.loads((output / "source.json").read_text(encoding="utf-8"))
            source["frontier_candidate_set_sha256"] = "0" * 64
            (output / "source.json").write_text(json.dumps(source), encoding="utf-8")
            with patch.object(frontier_runtime, "ATLAS", frontier_runtime.FrontierAtlas()):
                self.assertEqual(503, client.get("/api/anatomy/v1/holographic-v7").status_code)

    def test_search_returns_only_receipted_handles(self) -> None:
        brain = PublicSecondBrain(self.snapshot)
        result = brain.search("governed receipt anatomy", k=4)
        self.assertTrue(result["ready"])
        self.assertEqual(4, len(result["handles"]))
        self.assertEqual(4, len(result["scores"]))
        self.assertEqual(64, len(result["result_sha256"]))
        for handle in result["handles"]:
            self.assertEqual(
                {
                    "nodeId",
                    "nodeKind",
                    "label",
                    "note",
                    "source",
                    "sourceId",
                    "sha256",
                },
                set(handle),
            )
            self.assertNotIn("text", handle)
            self.assertEqual(64, len(handle["sha256"]))

    def test_context_has_no_training_or_write_authority(self) -> None:
        brain = PublicSecondBrain(self.snapshot)
        context = brain.context("living anatomy", k=3)
        self.assertTrue(context["ready"])
        self.assertEqual("NONE", context["training_authority"])
        self.assertEqual("NONE", context["write_authority"])
        self.assertEqual(0, context["private_graph_nodes_loaded"])
        self.assertEqual(3, len(context["model_handles"]))
        self.assertEqual(3, len(context["evidence"]))

    def test_frontier_formula_quant_and_ouroboros_views_are_handles_only(self) -> None:
        brain = PublicSecondBrain(self.snapshot)
        frontier = brain.frontier_search("formula quant anatomy ouroboros", k=12)
        self.assertTrue(frontier["ready"])
        self.assertEqual("REVIEW_REQUIRED", frontier["state"])
        self.assertTrue(frontier["handles"])
        self.assertEqual("NONE", frontier["training_authority"])
        self.assertEqual("NONE", frontier["execution_authority"])
        self.assertTrue(all("content" not in handle for handle in frontier["handles"]))

        formulas = brain.formula_view(k=24)
        self.assertEqual(30, formulas["attributed_formula_count"])
        self.assertEqual(21, formulas["executable_formula_count"])
        self.assertEqual(8, formulas["locked_proven_count"])
        self.assertEqual("UNKNOWN_NOT_INFERRED", formulas["f_number_mapping"])
        self.assertEqual(
            "CONJECTURE_1_OPEN_ADVISORY_ONLY",
            formulas["lambda_status"],
        )

        quant = brain.quant_view(k=24)
        self.assertEqual(9, quant["quant_domain_count"])
        self.assertEqual(9, len(quant["domains"]))

        ouroboros = brain.ouroboros_view(k=12)
        self.assertTrue(ouroboros["loop_contract"]["bounded"])
        self.assertTrue(ouroboros["loop_contract"]["terminating"])
        self.assertTrue(ouroboros["loop_contract"]["receipt_closed"])
        self.assertFalse(
            ouroboros["loop_contract"]["recommendations_executed"]
        )
        self.assertTrue(ouroboros["handles"])

    def test_neural_quant_v7_is_receipted_and_non_mutating(self) -> None:
        brain = PublicSecondBrain(self.snapshot)
        payload = brain.neural_quant_view(k=12)
        self.assertTrue(payload["ready"])
        self.assertEqual("7.0.0", payload["version"])
        self.assertEqual(575, payload["brain"]["chunk_count"])
        self.assertEqual(71, payload["brain"]["frontier_candidate_count"])
        self.assertEqual(30, payload["formulas"]["attributed"])
        self.assertEqual(21, payload["formulas"]["executable"])
        self.assertEqual(8, payload["formulas"]["locked_proven"])
        self.assertEqual(9, payload["quant"]["domain_count"])
        self.assertEqual("HANDLES_ONLY", payload["content_access"])
        self.assertEqual(
            {
                "training": "NONE",
                "promotion": "NONE",
                "execution": "NONE",
                "merge": "NONE",
                "provider_mutation": "NONE",
            },
            payload["authority"],
        )
        self.assertEqual(64, len(payload["view_sha256"]))
        for group in ("formulas", "quant", "ouroboros"):
            for handle in payload[group]["handles"]:
                self.assertNotIn("content", handle)
                self.assertNotIn("text", handle)

    def test_corrupt_frontier_candidate_fails_closed(self) -> None:
        path = self.snapshot / "frontier-candidates.public.jsonl"
        rows = path.read_text(encoding="utf-8").splitlines()
        candidate = json.loads(rows[0])
        candidate["content"] = "tampered"
        rows[0] = json.dumps(candidate, sort_keys=True, separators=(",", ":"))
        path.write_text("\n".join(rows) + "\n", encoding="utf-8")
        brain = PublicSecondBrain(self.snapshot)
        health = brain.health()
        self.assertFalse(health["ready"])
        self.assertEqual("UNAVAILABLE", health["state"])
        self.assertIn("mismatch", str(health["load_error"]).lower())

    def test_corrupt_corpus_fails_closed(self) -> None:
        path = self.snapshot / "brain-corpus.public.jsonl"
        path.write_bytes(path.read_bytes() + b"{}\n")
        brain = PublicSecondBrain(self.snapshot)
        health = brain.health()
        self.assertFalse(health["ready"])
        self.assertEqual("UNAVAILABLE", health["state"])
        self.assertIn("mismatch", str(health["load_error"]).lower())


if __name__ == "__main__":
    unittest.main()
