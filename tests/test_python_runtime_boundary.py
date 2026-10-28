# SPDX-License-Identifier: Apache-2.0
"""Guard: the shipped runtime is Python, and its imports stay declared.

Two claims, each checked on the tracked tree (``git ls-files``) and on
synthetic negative controls:

1. Python entrypoint. In every tracked ``Dockerfile`` the final stage's last
   ``CMD`` is the exec form ``["python", "<script>.py", ...]`` (``python``,
   ``python3`` or ``python3.N``, optionally under ``/usr/bin`` or
   ``/usr/local/bin``, with only value-less interpreter flags before the
   script). The stage sets no ``ENTRYPOINT`` that would wrap it and copies the
   build context into its ``WORKDIR`` with ``COPY . <dir>``. The script is a
   tracked file of the build context that ``.dockerignore`` does not exclude.
2. Import boundary. Every tracked non-test ``.py`` file (not under a ``tests``
   directory and not named ``test_*.py``, ``*_test.py`` or ``conftest.py``)
   imports only the running interpreter's standard library
   (``sys.stdlib_module_names``), repository modules, or a declared
   dependency. A dependency is declared by a tracked ``requirements.txt`` or,
   for CI-only publisher tools, by an exactly pinned quoted ``"name==version"``
   in a ``.github/workflows`` file that runs ``pip install``. In addition, the
   repository-module import closure of each Dockerfile's CMD script may use
   only the standard library, modules of that build context that
   ``.dockerignore`` keeps, and the build context's own ``requirements.txt``.
   A workflow-only tool such as ``huggingface_hub`` therefore never enters an
   image's runtime import path.

It is stdlib-only so it runs under ``unittest discover`` (pytest is not
installed yet at that step) as well as under pytest.

Boundaries -- static on purpose, not a general Dockerfile or import system:

* Imports are read with ``ast`` from every ``import`` and ``from ... import``
  statement, including ones nested in functions or ``try`` blocks, so an import
  guarded by ``except ImportError`` still counts. Repository modules resolve
  from the importing file's directory or the repository root (for the runtime
  closure: the build context root), as files or packages with
  ``__init__.py``. A namespace package, ``importlib.import_module``,
  ``__import__`` and ``sys.path`` edits are not interpreted.
* Distribution names are compared with top-level import names after
  normalisation (``-``, ``_`` and ``.`` are equal, case is ignored). A
  distribution whose import name differs (PyYAML provides ``yaml``) is
  reported as undeclared: the guard fails closed.
* The Dockerfile reader joins ``\\`` continuations and drops comment lines, so
  ``HEALTHCHECK ... CMD`` stays part of ``HEALTHCHECK``. It rejects an
  ``escape`` parser directive, heredocs, shell-form ``CMD``, ``python -m`` and
  ``python -c``, and ``.dockerignore`` ``!`` exceptions instead of guessing.
  ``.dockerignore`` patterns are matched with ``fnmatch`` against every path
  prefix, which can only over-exclude.
* The standard-library list is the running interpreter's; CI and the image
  use Python 3.12.

Not covered: whether the image really installs ``requirements.txt`` or starts
(container-contract.yml builds and exercises the image), an ENTRYPOINT
inherited from the base image, browser JavaScript, and the Node test harnesses.
"""

from __future__ import annotations

import ast
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
import fnmatch
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_DIR = ".github/workflows/"
INTERPRETER = re.compile(r"(?:/usr(?:/local)?/bin/)?python(?:3(?:\.[0-9]+)?)?")
# Interpreter options that take no value and leave the next argument as the script.
INTERPRETER_FLAGS = frozenset({"-B", "-E", "-I", "-O", "-OO", "-P", "-q", "-s", "-S", "-u"})
EXACT_PIN = re.compile(
    r"""(["'])([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]"']*\])?==[A-Za-z0-9][A-Za-z0-9.+!_-]*\1"""
)
REQUIREMENT = re.compile(r"([A-Za-z0-9][A-Za-z0-9._-]*)(?=$|[\s\[=<>!~;@\\])")
ESCAPE_DIRECTIVE = re.compile(r"#\s*escape\s*=.*", re.IGNORECASE)


class FormatError(ValueError):
    """The input has a shape this guard does not interpret."""


@dataclass(frozen=True)
class Import:
    line: int
    level: int
    module: str
    names: tuple[str, ...]

    @property
    def label(self) -> str:
        return "." * self.level + self.module


# --- inventory ---------------------------------------------------------------


def tracked_files(root: Path) -> list[str]:
    output = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=True,
        capture_output=True,
    ).stdout
    return sorted(name for name in output.decode("utf-8").split("\0") if name)


def is_test_path(relative: str) -> bool:
    path = PurePosixPath(relative)
    return (
        "tests" in path.parts[:-1]
        or path.name.startswith("test_")
        or path.name.endswith("_test.py")
        or path.name == "conftest.py"
    )


def non_test_python(files: Iterable[str]) -> list[str]:
    return sorted(name for name in files if name.endswith(".py") and not is_test_path(name))


def dockerfiles(files: Iterable[str]) -> list[str]:
    return sorted(name for name in files if PurePosixPath(name).name == "Dockerfile")


# --- declared dependencies ---------------------------------------------------


def normalize(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def requirement_names(path: Path) -> set[str]:
    names: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split(" #", 1)[0].strip()
        if not line or line.startswith(("#", "-")):
            continue
        match = REQUIREMENT.match(line)
        if match is None:
            raise FormatError(f"{path.name}: requirement {raw.strip()!r} is not interpreted")
        names.add(normalize(match.group(1)))
    return names


def workflow_pins(root: Path, files: Iterable[str]) -> set[str]:
    names: set[str] = set()
    for relative in files:
        if not (relative.startswith(WORKFLOW_DIR) and relative.endswith((".yml", ".yaml"))):
            continue
        text = (root / relative).read_text(encoding="utf-8")
        if "pip install" in text:
            names.update(normalize(match.group(2)) for match in EXACT_PIN.finditer(text))
    return names


def declared_dependencies(root: Path, files: Sequence[str]) -> set[str]:
    declared = workflow_pins(root, files)
    for relative in files:
        if PurePosixPath(relative).name == "requirements.txt":
            declared |= requirement_names(root / relative)
    return declared


# --- Dockerfile --------------------------------------------------------------


def dockerfile_instructions(text: str) -> list[tuple[str, str]]:
    """Logical instructions as (KEYWORD, rest), continuations joined."""

    instructions: list[tuple[str, str]] = []
    pending: list[str] = []
    for raw in text.splitlines():
        stripped = raw.strip()
        if not instructions and not pending and ESCAPE_DIRECTIVE.fullmatch(stripped):
            raise FormatError("an escape parser directive is not interpreted")
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.endswith("\\"):
            pending.append(stripped[:-1].strip())
            continue
        pending.append(stripped)
        keyword, *rest = re.split(r"\s+", " ".join(pending), maxsplit=1)
        pending = []
        instructions.append((keyword.upper(), rest[0].strip() if rest else ""))
    if pending:
        raise FormatError("the file ends inside a line continuation")
    for keyword, rest in instructions:
        if "<<" in rest:
            raise FormatError(f"a heredoc in {keyword} is not interpreted")
    return instructions


def _context_copy_target(rest: str, workdir: str) -> str | None:
    """The image directory a COPY/ADD puts the whole build context into, if any."""

    if rest.startswith("["):
        try:
            tokens = json.loads(rest)
        except json.JSONDecodeError as error:
            raise FormatError(f"COPY {rest!r} is not interpreted") from error
        if not (isinstance(tokens, list) and all(isinstance(token, str) for token in tokens)):
            raise FormatError(f"COPY {rest!r} is not interpreted")
    else:
        tokens = rest.split()
    if any(token.startswith("--from") for token in tokens):
        return None
    paths = [token for token in tokens if not token.startswith("--")]
    if len(paths) < 2 or not any(posixpath.normpath(source) == "." for source in paths[:-1]):
        return None
    return posixpath.normpath(posixpath.join(workdir, paths[-1]))


def dockerignore_patterns(root: Path, context: PurePosixPath) -> list[str]:
    path = root / context / ".dockerignore"
    if not path.is_file():
        return []
    patterns = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("!"):
            raise FormatError(".dockerignore exceptions (!) are not interpreted")
        patterns.append(posixpath.normpath(line.lstrip("/")))
    return patterns


def excluded(patterns: Sequence[str], relative: str) -> bool:
    parts = PurePosixPath(relative).parts
    prefixes = ["/".join(parts[: index + 1]) for index in range(len(parts))]
    return any(fnmatch.fnmatchcase(prefix, pattern) for prefix in prefixes for pattern in patterns)


def python_entrypoint(
    root: Path, dockerfile: str, files: Sequence[str]
) -> tuple[str | None, list[str]]:
    """The repository path of the script a Dockerfile's CMD runs, and every problem."""

    context = PurePosixPath(dockerfile).parent
    try:
        instructions = dockerfile_instructions((root / dockerfile).read_text(encoding="utf-8"))
    except FormatError as error:
        return None, [f"{dockerfile}: {error}"]
    starts = [index for index, (keyword, _) in enumerate(instructions) if keyword == "FROM"]
    if not starts:
        return None, [f"{dockerfile}: no FROM instruction"]

    problems: list[str] = []
    workdir = "/"
    copied: set[str] = set()
    commands: list[str] = []
    for keyword, rest in instructions[starts[-1] + 1 :]:
        if keyword == "WORKDIR":
            workdir = posixpath.normpath(posixpath.join(workdir, rest.strip("\"'")))
        elif keyword in {"COPY", "ADD"}:
            try:
                target = _context_copy_target(rest, workdir)
            except FormatError as error:
                return None, [f"{dockerfile}: {error}"]
            if target is not None:
                copied.add(target)
        elif keyword == "ENTRYPOINT":
            problems.append(f"{dockerfile}: the final stage sets ENTRYPOINT, which would wrap CMD")
        elif keyword == "CMD":
            commands.append(rest)
    if not commands:
        return None, problems + [f"{dockerfile}: the final stage has no CMD"]

    try:
        argv = json.loads(commands[-1])
    except json.JSONDecodeError:
        argv = None
    if not (isinstance(argv, list) and argv and all(isinstance(arg, str) for arg in argv)):
        return None, problems + [
            f'{dockerfile}: CMD {commands[-1]!r} is not the exec form ["python", "<script>.py"]'
        ]
    if not INTERPRETER.fullmatch(argv[0]):
        return None, problems + [f"{dockerfile}: CMD runs {argv[0]!r}, not a Python interpreter"]
    args = argv[1:]
    while args and args[0] in INTERPRETER_FLAGS:
        args = args[1:]
    if not args or args[0].startswith("-") or not args[0].endswith(".py"):
        return None, problems + [
            f"{dockerfile}: CMD {argv!r} does not name a .py script "
            "(-m and -c are not interpreted)"
        ]
    script = args[0]
    if script.startswith("/") or ".." in PurePosixPath(script).parts:
        return None, problems + [
            f"{dockerfile}: CMD script {script!r} must be relative to WORKDIR "
            "inside the build context"
        ]

    if workdir not in copied:
        problems.append(
            f"{dockerfile}: the final stage does not COPY the build context into WORKDIR {workdir}"
        )
    relative = (context / script).as_posix()
    if relative not in set(files) or not (root / relative).is_file():
        problems.append(
            f"{dockerfile}: CMD script {script!r} is not a tracked file of the build context"
        )
    else:
        try:
            if excluded(dockerignore_patterns(root, context), script):
                problems.append(
                    f"{dockerfile}: CMD script {script!r} is excluded by .dockerignore"
                )
        except FormatError as error:
            problems.append(f"{dockerfile}: {error}")
    return relative, problems


# --- imports -----------------------------------------------------------------


def imports_of(path: Path) -> list[Import]:
    tree = ast.parse(path.read_bytes(), filename=str(path))
    found: list[Import] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(Import(node.lineno, 0, alias.name, ()) for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names = tuple(alias.name for alias in node.names)
            found.append(Import(node.lineno, node.level, node.module or "", names))
    return sorted(found, key=lambda item: (item.line, item.label))


def _module_files(base: Path, parts: Sequence[str]) -> list[Path] | None:
    """Files that importing the dotted ``parts`` from ``base`` executes, or None."""

    loaded: list[Path] = []
    current = base
    for index, part in enumerate(parts):
        package = current / part / "__init__.py"
        module = current / f"{part}.py"
        if package.is_file():
            loaded.append(package)
            current = current / part
        elif module.is_file() and index == len(parts) - 1:
            loaded.append(module)
        else:
            return None
    return loaded


def classify(
    importer: Path, item: Import, bases: Sequence[Path], declared: set[str]
) -> tuple[str, list[Path]]:
    """One of repository/stdlib/declared/undeclared/unresolved, with repository files loaded."""

    parts = item.module.split(".") if item.module else []
    if item.level:
        base = importer.parent
        for _ in range(item.level - 1):
            base = base.parent
        search = [base]
    else:
        search = list(dict.fromkeys(bases))
    for base in search:
        if parts:
            loaded = _module_files(base, parts)
        else:  # `from . import name`: the package itself
            init = base / "__init__.py"
            loaded = [init] if init.is_file() else None
        if loaded is None:
            continue
        if loaded[-1].name == "__init__.py":
            for name in item.names:
                loaded.extend(_module_files(loaded[-1].parent, [name]) or [])
        return "repository", loaded
    if item.level or any(_module_files(base, parts[:1]) for base in search):
        return "unresolved", []
    if parts[0] in sys.stdlib_module_names:
        return "stdlib", []
    if normalize(parts[0]) in declared:
        return "declared", []
    return "undeclared", []


def import_problems(root: Path, files: Sequence[str]) -> list[str]:
    declared = declared_dependencies(root, files)
    problems: list[str] = []
    for relative in non_test_python(files):
        path = root / relative
        for item in imports_of(path):
            kind, _ = classify(path, item, (path.parent, root), declared)
            if kind == "undeclared":
                problems.append(
                    f"{relative}:{item.line} imports {item.label!r}, which is not the standard "
                    "library, a repository module or a declared dependency"
                )
            elif kind == "unresolved":
                problems.append(
                    f"{relative}:{item.line} imports {item.label!r}, which does not resolve to a "
                    "repository module"
                )
    return problems


def runtime_closure(
    root: Path, dockerfile: str, script: str, files: Sequence[str]
) -> tuple[list[str], list[str]]:
    """Repository modules on a CMD script's import path, and every boundary problem."""

    context_path = PurePosixPath(dockerfile).parent
    context = root / context_path
    requirements = (context_path / "requirements.txt").as_posix()
    allowed = requirement_names(root / requirements) if requirements in files else set()
    try:
        patterns = dockerignore_patterns(root, context_path)
    except FormatError as error:
        return [], [f"{dockerfile}: {error}"]

    problems: list[str] = []
    seen: list[Path] = []
    queue = [root / script]
    while queue:
        path = queue.pop(0)
        if path in seen:
            continue
        seen.append(path)
        relative = path.relative_to(root).as_posix()
        for item in imports_of(path):
            kind, loaded = classify(path, item, (path.parent, context), allowed)
            if kind == "repository":
                for module in loaded:
                    if not module.is_relative_to(context):
                        problems.append(
                            f"{relative}:{item.line} imports {item.label!r} from outside "
                            f"the build context of {dockerfile}"
                        )
                    elif excluded(patterns, module.relative_to(context).as_posix()):
                        problems.append(
                            f"{relative}:{item.line} imports {item.label!r}, whose "
                            f"{module.relative_to(root).as_posix()} is excluded by .dockerignore"
                        )
                    else:
                        queue.append(module)
            elif kind == "unresolved":
                problems.append(
                    f"{relative}:{item.line} imports {item.label!r}, which does not resolve to a "
                    f"module of the build context of {dockerfile}"
                )
            elif kind == "undeclared":
                problems.append(
                    f"{relative}:{item.line} imports {item.label!r} on the {dockerfile} runtime "
                    f"path, which provides only the standard library, its build context and "
                    f"{requirements}"
                )
    return sorted(path.relative_to(root).as_posix() for path in seen), problems


def boundary_problems(root: Path, files: Sequence[str]) -> list[str]:
    """Every entrypoint, import and runtime-closure problem of a tree."""

    problems = import_problems(root, files)
    for dockerfile in dockerfiles(files):
        script, entry_problems = python_entrypoint(root, dockerfile, files)
        problems.extend(entry_problems)
        if script is not None and not entry_problems:
            problems.extend(runtime_closure(root, dockerfile, script, files)[1])
    return problems


# --- tests -------------------------------------------------------------------


class PythonRuntimeBoundaryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.files = tracked_files(ROOT)
        cls.dockerfiles = dockerfiles(cls.files)

    def test_every_dockerfile_cmd_is_a_python_entrypoint(self) -> None:
        self.assertIn("Dockerfile", self.dockerfiles)
        for dockerfile in self.dockerfiles:
            with self.subTest(dockerfile=dockerfile):
                script, problems = python_entrypoint(ROOT, dockerfile, self.files)
                self.assertEqual(problems, [])
                self.assertIn(script, non_test_python(self.files))

    def test_non_test_python_imports_only_stdlib_repository_or_declared(self) -> None:
        self.assertIn("server.py", non_test_python(self.files))
        self.assertEqual(import_problems(ROOT, self.files), [])

    def test_image_runtime_import_path_needs_only_its_requirements(self) -> None:
        for dockerfile in self.dockerfiles:
            with self.subTest(dockerfile=dockerfile):
                script, problems = python_entrypoint(ROOT, dockerfile, self.files)
                self.assertEqual(problems, [])
                modules, problems = runtime_closure(ROOT, dockerfile, script, self.files)
                self.assertIn(script, modules)
                self.assertEqual(problems, [])


GOOD_DOCKERFILE = """\
# A comment line.
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY . /app
HEALTHCHECK --interval=30s \\
  CMD python -c "import sys"
CMD ["python", "app.py"]
"""

GOOD_TREE = {
    "Dockerfile": GOOD_DOCKERFILE,
    ".dockerignore": "tests\n*.py[cod]\n",
    "requirements.txt": "fastapi==0.115.12\n",
    "app.py": (
        "import json\n\nimport helper\nfrom pkg import sub\n\n\n"
        "def serve():\n    import fastapi\n"
    ),
    "helper.py": "from __future__ import annotations\n\nimport os\n",
    "pkg/__init__.py": "",
    "pkg/sub.py": "from . import other\n",
    "pkg/other.py": "",
    "scripts/publish.py": "import huggingface_hub\n\nimport helper\n",
    ".github/workflows/publish.yml": (
        "jobs:\n  publish:\n    steps:\n"
        '      - run: python -m pip install "huggingface_hub==1.23.0"\n'
    ),
    "tests/test_app.py": "import pytest\n",
}


def _edit(path: str, old: str, new: str):
    def apply(tree: dict[str, str]) -> None:
        assert old in tree[path], (path, old)
        tree[path] = tree[path].replace(old, new)

    return apply


def _append(path: str, text: str):
    def apply(tree: dict[str, str]) -> None:
        tree[path] = tree.get(path, "") + text

    return apply


GOOD_CMD = 'CMD ["python", "app.py"]\n'
# Control name -> (mutation of GOOD_TREE, text every reported problem must contain).
NEGATIVE_CONTROLS = {
    "CMD runs node": (
        _edit("Dockerfile", GOOD_CMD, 'CMD ["node", "server.js"]\n'),
        "not a Python interpreter",
    ),
    "shell-form CMD": (
        _edit("Dockerfile", GOOD_CMD, "CMD python app.py\n"),
        "is not the exec form",
    ),
    "ENTRYPOINT wraps CMD": (_append("Dockerfile", 'ENTRYPOINT ["node"]\n'), "sets ENTRYPOINT"),
    "CMD script missing": (_edit("Dockerfile", "app.py", "missing.py"), "is not a tracked file"),
    "python -m module": (
        _edit("Dockerfile", '"app.py"', '"-m", "app"'),
        "does not name a .py script",
    ),
    "only a HEALTHCHECK CMD": (_edit("Dockerfile", GOOD_CMD, ""), "has no CMD"),
    "final stage is Node": (
        _append("Dockerfile", 'FROM node:22-slim\nCMD ["node", "server.js"]\n'),
        "not a Python interpreter",
    ),
    "build context not copied": (
        _edit("Dockerfile", "COPY . /app\n", ""),
        "does not COPY the build context",
    ),
    "CMD script ignored": (_append(".dockerignore", "app.py\n"), "excluded by .dockerignore"),
    "runtime package ignored": (_append(".dockerignore", "pkg\n"), "excluded by .dockerignore"),
    "dockerignore exception": (_append(".dockerignore", "!keep.py\n"), "are not interpreted"),
    "undeclared import": (_append("helper.py", "import requests\n"), "imports 'requests'"),
    "undeclared nested import": (
        _append("app.py", "\n\ndef extra():\n    import yaml\n"),
        "imports 'yaml'",
    ),
    "unresolved repository import": (
        _append("app.py", "import pkg.missing\n"),
        "does not resolve",
    ),
    "loosely pinned publisher tool": (
        _edit(".github/workflows/publish.yml", "huggingface_hub==1.23.0", "huggingface_hub>=1"),
        "scripts/publish.py:1 imports 'huggingface_hub'",
    ),
    "publisher tool on the runtime path": (
        _append("helper.py", "import huggingface_hub\n"),
        "imports 'huggingface_hub' on the Dockerfile runtime path",
    ),
}


def _tree_problems(tree: dict[str, str]) -> list[str]:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        for relative, text in tree.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(text.encode("utf-8"))
        return boundary_problems(root, sorted(tree))


class BoundaryNegativeControlTest(unittest.TestCase):
    def test_conforming_synthetic_tree_passes(self) -> None:
        self.assertEqual(_tree_problems(GOOD_TREE), [])

    def test_each_violation_is_reported_for_its_own_reason(self) -> None:
        for name, (mutate, expected) in NEGATIVE_CONTROLS.items():
            with self.subTest(control=name):
                tree = dict(GOOD_TREE)
                mutate(tree)
                problems = _tree_problems(tree)
                self.assertTrue(problems, name)
                for problem in problems:
                    self.assertIn(expected, problem)


if __name__ == "__main__":
    unittest.main()
