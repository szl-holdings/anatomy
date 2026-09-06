# SPDX-License-Identifier: Apache-2.0
"""README architecture truth must follow the shipped application runtime."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


def test_runtime_files_exist() -> None:
    """The documentation boundary is conditioned on the deployed runtime tree."""
    for relative in (
        "server.py",
        "frontier_runtime.py",
        "second_brain_runtime.py",
        "living_runtime.py",
        "organ_integrity.py",
        "requirements.txt",
    ):
        assert (ROOT / relative).is_file(), relative


def test_readme_describes_application_runtime_not_static_server() -> None:
    text = README.read_text(encoding="utf-8")

    assert "no application backend" not in text
    assert "`python http.server` on port 7860" not in text
    assert "Python/FastAPI runtime" in text
    assert "`living_runtime.py` on port 7860" in text
    assert "atlas shell" in text
    assert "static and offline-capable" in text


def test_load_bearing_doctrine_sentences_remain_present() -> None:
    text = README.read_text(encoding="utf-8")

    assert (
        "Locked-proven stays **exactly 8** {F1,F4,F7,F11,F12,F18,F19,F22} "
        "@ `c7c0ba17`; the doctrine\nfooter is unchanged."
    ) in text
    assert "Λ unconditional uniqueness = Conjecture 1 (machine-checked FALSE)" in text
    assert "Khipu BFT safety = Conjecture 2" in text
