# SPDX-License-Identifier: Apache-2.0
"""README architecture truth must follow the shipped application runtime."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
DOCKERFILE = ROOT / "Dockerfile"


def _image_entrypoint() -> str:
    """Script named by the Dockerfile's last top-level exec-form ``CMD``.

    Derived rather than hard-coded, so a change of entrypoint (as when the
    refinement observatory wrapped ``living_runtime.py``) fails here until the
    README follows. ``HEALTHCHECK ... CMD`` continuation lines are indented, so
    only an instruction at the start of a line counts.
    """
    commands = [
        line
        for line in DOCKERFILE.read_text(encoding="utf-8").splitlines()
        if line.startswith("CMD ")
    ]
    assert commands, "Dockerfile has no top-level CMD"
    argv = json.loads(commands[-1][len("CMD "):])
    assert isinstance(argv, list) and len(argv) >= 2, argv
    assert argv[0] in {"python", "python3"} and argv[1].endswith(".py"), argv
    return argv[1]


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
    entrypoint = _image_entrypoint()

    assert "no application backend" not in text
    assert "`python http.server` on port 7860" not in text
    assert "Python application runtime" in text
    # The README names the image's real entrypoint and runs that same script.
    assert f"`{entrypoint}` on port 7860" in text
    assert f"python3 {entrypoint}" in text
    # It also names the transport that entrypoint actually serves from.
    assert "ThreadingHTTPServer" in (ROOT / entrypoint).read_text(encoding="utf-8")
    assert "standard-library `ThreadingHTTPServer`" in text
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
