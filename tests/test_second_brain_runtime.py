from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from second_brain_runtime import PublicSecondBrain  # noqa: E402


class PublicSecondBrainTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.snapshot = Path(self.temporary.name)
        sources = ["doc"] * 152 + ["formula"] * 269 + ["ingest"] * 143 + ["invariant"] * 11
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
        corpus_raw = "".join(
            json.dumps(row, separators=(",", ":")) + "\n" for row in rows
        ).encode("utf-8")
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
        source = {
            "schema": "szl.second-brain.snapshot/v1",
            "source_repository": "szl-holdings/szl-second-brain",
            "source_revision": "a" * 40,
            "manifest_sha256": hashlib.sha256(manifest_raw).hexdigest(),
            "corpus_sha256": hashlib.sha256(corpus_raw).hexdigest(),
            "public_chunk_count": 575,
        }
        (self.snapshot / "manifest.json").write_bytes(manifest_raw)
        (self.snapshot / "brain-corpus.public.jsonl").write_bytes(corpus_raw)
        (self.snapshot / "source.json").write_text(
            json.dumps(source, indent=2) + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_source_bound_snapshot_loads_exact_public_projection(self) -> None:
        brain = PublicSecondBrain(self.snapshot)
        health = brain.health()
        self.assertTrue(health["ready"])
        self.assertEqual(575, health["chunk_count"])
        self.assertEqual("a" * 40, health["source_revision"])
        self.assertEqual("HANDLES_ONLY", health["content_access"])
        self.assertEqual(0, health["private_graph_nodes_loaded"])
        self.assertEqual(
            {"doc": 152, "formula": 269, "ingest": 143, "invariant": 11},
            health["by_source"],
        )

    def test_search_returns_only_receipted_handles(self) -> None:
        brain = PublicSecondBrain(self.snapshot)
        result = brain.search("governed receipt anatomy", k=4)
        self.assertTrue(result["ready"])
        self.assertEqual(4, len(result["handles"]))
        self.assertEqual(4, len(result["scores"]))
        self.assertEqual(64, len(result["result_sha256"]))
        for handle in result["handles"]:
            self.assertEqual(
                {"nodeId", "nodeKind", "label", "note", "source", "sourceId", "sha256"},
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
