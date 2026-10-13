"""Guard: both CI gates must run pytest over the whole tests/ directory.

``python -m unittest discover`` runs only ``unittest.TestCase`` methods. Plain
pytest tests (module-level ``def test_*`` / ``async def test_*`` and methods
of plain ``class Test*``) run only because container-contract.yml and
hf-sync.yml each also execute

    python -m pytest -q -p no:cacheprovider \\
        -W error::pytest.PytestUnhandledCoroutineWarning tests

pytest's recursive discovery then finds every test, and the targeted filter
turns pytest 8.3's unhandled-coroutine warning (an unmarked ``async def
test_*`` is otherwise skipped with exit code 0) into a failure. This module
fails if that command stops being executable in either gate, is narrowed to
files, or loses the filter; in hf-sync.yml it must also run before Publish.

It is stdlib-only so it runs under ``unittest discover`` (pytest is not
installed yet at that step) as well as under pytest.

Boundaries -- constrained on purpose, not a general YAML or shell interpreter:

* YAML. When PyYAML is importable (hf-sync.yml gets it from huggingface_hub)
  every check runs on PyYAML's parse and on the built-in line reader, and
  the two parses of the real workflows must be identical. Where PyYAML is
  absent (container-contract.yml) only the line reader runs. The line reader
  handles block mappings and sequences, plain and single-line quoted scalars,
  and ``|``/``|-``/``|+``/``>``/``>-``/``>+`` block scalars with YAML folding.
  A ``run`` it cannot decode counts as no command, and if it mentions pytest
  that is a failure.
* Shell. A decoded ``run`` is split into lines (backslash continuations
  joined, heredoc bodies skipped) and each line into simple commands with
  ``shlex`` (POSIX rules, ``#`` comments dropped, ``&& || ; | & ( )`` as
  separators). Only a simple command starting ``python -m pytest`` counts, so
  YAML comments, step names, ``echo`` arguments and shell comments never do.
  It must be the last command of its step, reached only through ``&&``, with
  ``-W error::pytest.PytestUnhandledCoroutineWarning``, optionally ``-q`` and
  ``-p no:cacheprovider``, nothing else, and exactly one positional
  argument: ``tests``.
* Structure. Exactly one step of the gate job runs pytest. That step has only
  ``name`` and ``run``. The job has no ``if``, ``continue-on-error`` or
  ``defaults``, the workflow has no ``defaults``, and the file never mentions
  ``PYTEST_ADDOPTS`` or ``PYTEST_PLUGINS``.

Not covered: workflow triggers, and earlier steps that end the job early.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import shlex
import tempfile
from typing import Callable
import unittest

try:  # hf-sync.yml installs PyYAML (huggingface_hub); container-contract.yml does not.
    import yaml
except ImportError:
    yaml = None


ROOT = Path(__file__).resolve().parents[1]
COROUTINE_FILTER = "error::pytest.PytestUnhandledCoroutineWarning"
PYTEST = ["python", "-m", "pytest"]
# Flag -> allowed values (None: the flag takes no value).
ALLOWED_FLAGS: dict[str, set[str] | None] = {
    "-q": None,
    "-p": {"no:cacheprovider"},
    "-W": {COROUTINE_FILTER},
}
SEPARATORS = {"&&", "||", ";", ";;", "|", "|&", "&", "(", ")"}
STEP_KEYS = {"name", "run"}
FORBIDDEN_WORKFLOW_KEYS = ("defaults",)
FORBIDDEN_JOB_KEYS = ("if", "continue-on-error", "defaults")
FORBIDDEN_TEXT = ("PYTEST_ADDOPTS", "PYTEST_PLUGINS")


@dataclass(frozen=True)
class Gate:
    workflow: Path
    job: str
    # Leading tokens of a command that must run only after the pytest step.
    publish: tuple[str, ...] = ()


GATES = (
    Gate(ROOT / ".github/workflows/container-contract.yml", "container-contract"),
    Gate(
        ROOT / ".github/workflows/hf-sync.yml",
        "sync",
        publish=("python", "scripts/sync_hf_creator_profile.py"),
    ),
)


class FormatError(ValueError):
    """The workflow text has a shape this guard does not interpret."""


@dataclass
class Step:
    keys: list[str]
    name: str | None
    run: str | None  # decoded run scalar; None when absent or undecodable
    raw_run: str = field(default="", compare=False)


@dataclass
class Workflow:
    keys: list[str]
    job_keys: list[str] | None  # None when the gate job is missing
    steps: list[Step] | None  # None when the job has no steps list


# --- line reader -------------------------------------------------------------

_KEY = re.compile(r"(?P<key>[A-Za-z_][A-Za-z0-9_-]*):(?:[ ]+(?P<value>.*))?")
_BLOCK_HEADER = re.compile(r"(?P<style>[|>])(?P<chomp>[-+]?)")


@dataclass
class _Entry:
    key: str | None  # None when the line is not a plain `key:` entry
    value: str  # raw text after `key:` on the entry's own line
    body: list[str]  # following deeper-indented, blank and comment lines
    indent: int


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _structural(line: str) -> bool:
    text = line.strip()
    return bool(text) and not text.startswith("#")


def _uncommented(value: str) -> str:
    """A plain value up to its YAML comment (`#` at the start or after a space)."""

    if value.startswith("#"):
        return ""
    return value.split(" #", 1)[0].strip()


def _block_indent(lines: list[str]) -> int:
    for line in lines:
        if _structural(line):
            return _indent(line)
    raise FormatError("expected an indented block")


def _entries(lines: list[str], indent: int) -> list[_Entry]:
    """Split a block mapping whose keys sit at exactly ``indent`` columns."""

    entries: list[_Entry] = []
    for line in lines:
        if not _structural(line) or (_indent(line) > indent and entries):
            if entries:
                entries[-1].body.append(line)
            continue
        if _indent(line) != indent:
            raise FormatError(f"unexpected indentation: {line.strip()!r}")
        match = _KEY.fullmatch(line[indent:].rstrip())
        if match is None:
            entries.append(_Entry(None, line.strip(), [], indent))
        else:
            entries.append(_Entry(match["key"], (match["value"] or "").rstrip(), [], indent))
    return entries


def _items(lines: list[str], indent: int) -> list[list[str]]:
    """Split a block sequence whose dashes sit at ``indent``; items become mappings."""

    items: list[list[str]] = []
    for line in lines:
        if not _structural(line) or (_indent(line) > indent and items):
            if items:
                items[-1].append(line)
            continue
        rest = line[indent:]
        if _indent(line) != indent or not rest.startswith("- ") or rest[2:3] in ("", " "):
            raise FormatError(f"unsupported sequence entry: {line.strip()!r}")
        items.append([" " * (indent + 2) + rest[2:]])
    return items


def _mapping(entries: list[_Entry], where: str) -> dict[str, _Entry]:
    mapping: dict[str, _Entry] = {}
    for entry in entries:
        if entry.key is None:
            raise FormatError(f"{where}: unsupported entry {entry.value!r}")
        if entry.key in mapping:
            raise FormatError(f"{where}: duplicate key {entry.key!r}")
        mapping[entry.key] = entry
    return mapping


def _fold(lines: list[str]) -> str:
    """YAML line folding for block-scalar content (indentation removed)."""

    text, previous, empties = "", None, 0
    for line in lines:
        if not line:
            empties += 1
            continue
        kind = "spaced" if line[0] in " \t" else "normal"
        if previous is None:
            text += "\n" * empties + line
        elif previous == kind == "normal":
            text += (" " if empties == 0 else "\n" * empties) + line
        else:
            text += "\n" * (empties + 1) + line
        previous, empties = kind, 0
    return text


def _block_scalar(entry: _Entry, style: str, chomp: str) -> str:
    content: list[str] = []
    content_indent: int | None = None
    ended = False
    for line in entry.body:
        if not line.strip():
            if not ended:
                content.append("")
            continue
        column = _indent(line)
        if content_indent is None:
            if column <= entry.indent:
                raise FormatError("block scalar content is not indented")
            content_indent = column
        if column < content_indent:
            if line.strip().startswith("#"):
                ended = True  # trailing comment after the scalar
                continue
            raise FormatError("block scalar content is under-indented")
        if ended:
            raise FormatError("block scalar content after a trailing comment")
        content.append(line[content_indent:])
    trailing = 0
    while content and not content[-1]:
        content.pop()
        trailing += 1
    text = "\n".join(content) if style == "|" else _fold(content)
    if not text or chomp == "-":
        return text
    return text + "\n" * (trailing + 1 if chomp == "+" else 1)


def _scalar(entry: _Entry) -> str:
    """Decode a scalar value; FormatError when outside the supported subset."""

    header = _uncommented(entry.value)
    block = _BLOCK_HEADER.fullmatch(header)
    if block:
        return _block_scalar(entry, block["style"], block["chomp"])
    structural = [line for line in entry.body if _structural(line)]
    if header[:1] in ("'", '"'):
        if structural:
            raise FormatError("multi-line quoted scalar")
        quote = header[0]
        end = entry.value.find(quote, 1)
        while quote == "'" and end != -1 and entry.value[end + 1 : end + 2] == "'":
            end = entry.value.find(quote, end + 2)
        if end == -1 or _uncommented(entry.value[end + 1 :].strip()):
            raise FormatError("unterminated or trailing quoted scalar")
        inner = entry.value[1:end]
        if quote == '"':
            if "\\" in inner:
                raise FormatError("escapes in double-quoted scalar")
            return inner
        return inner.replace("''", "'")
    if header[:1] in ("[", "{", "&", "*", "!", "|", ">", "@", "`"):
        raise FormatError(f"unsupported scalar {header!r}")
    lines = [header] if header else []
    ended = False
    for line in entry.body:
        text = line.strip()
        if not text:
            if not ended:
                lines.append("")
            continue
        if ended or text.startswith("#"):
            if not text.startswith("#"):
                raise FormatError("plain scalar continues after a comment")
            ended = True
            continue
        if " #" in text:
            text, ended = text.split(" #", 1)[0].rstrip(), True
        lines.append(text)
    while lines and not lines[-1]:
        lines.pop()
    return _fold(lines)


def read_lines(text: str, job_name: str) -> Workflow:
    top = _mapping(_entries(text.splitlines(), 0), "workflow")
    jobs_entry = top.get("jobs")
    if jobs_entry is None or _uncommented(jobs_entry.value):
        return Workflow(list(top), None, None)
    jobs = _mapping(_entries(jobs_entry.body, _block_indent(jobs_entry.body)), "jobs")
    job_entry = jobs.get(job_name)
    if job_entry is None or _uncommented(job_entry.value):
        return Workflow(list(top), None, None)
    job = _mapping(_entries(job_entry.body, _block_indent(job_entry.body)), job_name)
    steps_entry = job.get("steps")
    if steps_entry is None or _uncommented(steps_entry.value):
        return Workflow(list(top), list(job), None)
    steps = []
    for item in _items(steps_entry.body, _block_indent(steps_entry.body)):
        step = _mapping(_entries(item, _block_indent(item)), "step")
        name, run, raw = None, None, ""
        if "name" in step:
            try:
                name = _scalar(step["name"])
            except FormatError:
                name = None
        if "run" in step:
            raw = "\n".join([step["run"].value, *step["run"].body])
            try:
                run = _scalar(step["run"])
            except FormatError:
                run = None
        steps.append(Step(list(step), name, run, raw))
    return Workflow(list(top), list(job), steps)


def read_yaml(text: str, job_name: str) -> Workflow:
    assert yaml is not None
    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError as error:
        raise FormatError(f"PyYAML: {error}") from error
    if not isinstance(document, dict):
        raise FormatError("workflow is not a mapping")
    keys = ["on" if key is True else str(key) for key in document]  # YAML 1.1 `on`
    jobs = document.get("jobs")
    job = jobs.get(job_name) if isinstance(jobs, dict) else None
    if not isinstance(job, dict):
        return Workflow(keys, None, None)
    raw_steps = job.get("steps")
    if not isinstance(raw_steps, list):
        return Workflow(keys, [str(key) for key in job], None)
    steps = []
    for raw_step in raw_steps:
        if not isinstance(raw_step, dict):
            raise FormatError("step is not a mapping")
        name, run = raw_step.get("name"), raw_step.get("run")
        steps.append(
            Step(
                [str(key) for key in raw_step],
                name if isinstance(name, str) else None,
                run if isinstance(run, str) else None,
                "" if run is None else str(run),
            )
        )
    return Workflow(keys, [str(key) for key in job], steps)


Reader = Callable[[str, str], Workflow]


def readers() -> list[tuple[str, Reader]]:
    available: list[tuple[str, Reader]] = [("line reader", read_lines)]
    if yaml is not None:
        available.append(("PyYAML", read_yaml))
    return available


# --- shell ---------------------------------------------------------------------

_HEREDOC = re.compile(r"<<-?\s*(['\"]?)(?P<tag>[A-Za-z_][A-Za-z0-9_]*)\1")


def _command_lines(script: str) -> list[str]:
    lines, heredoc = [], None
    for line in script.replace("\\\n", " ").split("\n"):
        if heredoc is not None:
            if line.strip() == heredoc:
                heredoc = None
            continue
        lines.append(line)
        match = _HEREDOC.search(line)
        if match:
            heredoc = match["tag"]
    return lines


def _simple_commands(line: str) -> list[tuple[str | None, list[str], str | None]]:
    """(separator before, tokens, separator after) for each command on a line."""

    lexer = shlex.shlex(line, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    commands: list[tuple[str | None, list[str], str | None]] = []
    before, current = None, []
    for token in lexer:
        if token in SEPARATORS:
            if current:
                commands.append((before, current, token))
            before, current = token, []
        else:
            current.append(token)
    if current:
        commands.append((before, current, None))
    return commands


def _argument_problems(arguments: list[str]) -> list[str]:
    problems, flags, positional = [], [], []
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument in ALLOWED_FLAGS:
            values = ALLOWED_FLAGS[argument]
            if values is None:
                flags.append((argument,))
                index += 1
                continue
            value = arguments[index + 1] if index + 1 < len(arguments) else None
            if value not in values:
                problems.append(f"pytest option {argument} {value!r} is not allowed")
            flags.append((argument, value))
            index += 2
            continue
        if argument.startswith("-"):
            problems.append(f"pytest option {argument!r} is not allowed")
        else:
            positional.append(argument)
        index += 1
    if ("-W", COROUTINE_FILTER) not in flags:
        problems.append(f"pytest must run with -W {COROUTINE_FILTER} (coroutine filter)")
    if positional != ["tests"]:
        problems.append(
            f"pytest positional arguments must be exactly ['tests'], got {positional}"
        )
    return problems


def pytest_command_problems(script: str) -> tuple[int, list[str]]:
    """Count `python -m pytest` commands in a run script and check them."""

    found, problems, last_line = [], [], None
    lines = _command_lines(script)
    for number, line in enumerate(lines):
        try:
            commands = _simple_commands(line)
        except ValueError:
            if "pytest" in line:
                problems.append(f"cannot tokenize a shell line that mentions pytest: {line!r}")
            continue
        if commands:
            last_line = number
        separators = {before for before, _, _ in commands if before is not None}
        for position, (before, tokens, after) in enumerate(commands):
            if tokens[:3] == PYTEST:
                found.append((number, position == len(commands) - 1, after, separators, tokens))
    for number, last_on_line, after, separators, tokens in found:
        if number != last_line or not last_on_line or after is not None or separators - {"&&"}:
            problems.append(
                "python -m pytest must be the last command of its step, reached only "
                "through &&"
            )
        problems.extend(_argument_problems(tokens[3:]))
    if len(found) > 1:
        problems.append(f"a step may run python -m pytest once, found {len(found)}")
    return len(found), problems


def _runs(script: str, prefix: tuple[str, ...]) -> bool:
    for line in _command_lines(script):
        try:
            commands = _simple_commands(line)
        except ValueError:
            continue
        if any(tuple(tokens[: len(prefix)]) == prefix for _, tokens, _ in commands):
            return True
    return False


# --- gate ---------------------------------------------------------------------


def gate_problems(text: str, gate: Gate, read: Reader) -> list[str]:
    """Problems that stop ``gate.job`` from provably running the full pytest gate."""

    where = f"{gate.workflow.name} job {gate.job!r}"
    problems = [f"{gate.workflow.name}: {name} must not be set" for name in FORBIDDEN_TEXT if name in text]
    try:
        workflow = read(text, gate.job)
    except FormatError as error:
        return problems + [f"{where}: unreadable workflow: {error}"]
    problems += [
        f"{gate.workflow.name}: workflow-level {key!r} is not allowed in a gate"
        for key in FORBIDDEN_WORKFLOW_KEYS
        if key in workflow.keys
    ]
    if workflow.job_keys is None:
        return problems + [f"{where}: job not found"]
    problems += [
        f"{where}: job-level {key!r} is not allowed in a gate"
        for key in FORBIDDEN_JOB_KEYS
        if key in workflow.job_keys
    ]
    if workflow.steps is None:
        return problems + [f"{where}: no steps list"]

    pytest_steps = []
    for index, step in enumerate(workflow.steps):
        if step.run is None:
            if "pytest" in step.raw_run:
                problems.append(f"{where}: step {index + 1} mentions pytest in an undecodable run")
            continue
        count, step_problems = pytest_command_problems(step.run)
        if count:
            pytest_steps.append((index, step, step_problems))
    if len(pytest_steps) != 1:
        return problems + [
            f"{where}: expected exactly one step running python -m pytest, "
            f"found {len(pytest_steps)}"
        ]
    index, step, step_problems = pytest_steps[0]
    problems += [f"{where}: step {step.name!r}: {problem}" for problem in step_problems]
    extra = sorted(set(step.keys) - STEP_KEYS)
    if extra:
        problems.append(f"{where}: the pytest step must only have name and run, found {extra}")
    if gate.publish:
        command = " ".join(gate.publish)
        publishing = [
            i
            for i, other in enumerate(workflow.steps)
            if (other.run is not None and _runs(other.run, gate.publish))
            or (other.run is None and gate.publish[-1] in other.raw_run)
        ]
        if not publishing:
            problems.append(f"{where}: publish step `{command}` not found")
        elif min(publishing) < index:
            problems.append(f"{where}: `{command}` must run after the pytest step")
    return problems


# --- tests ----------------------------------------------------------------------

PYTEST_LINE = "          && python -m pytest -q -p no:cacheprovider\n"
FILTER_LINE = f"          -W {COROUTINE_FILTER} tests\n"
FULL_COMMAND = f"python -m pytest -q -p no:cacheprovider -W {COROUTINE_FILTER} tests"
PUBLISH_STEP = (
    "      - name: Publish and verify betterwithage/anatomy\n"
    "        run: python scripts/sync_hf_creator_profile.py\n"
)


def _once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise AssertionError(f"mutation anchor is not unique: {old!r}")
    return text.replace(old, new)


def _pytest_step(text: str) -> str:
    end = text.index(FILTER_LINE) + len(FILTER_LINE)
    return text[text.rindex("      - name: ", 0, end) : end]


def _step_name_line(text: str) -> str:
    step = _pytest_step(text)
    return step[: step.index("\n") + 1]


def _with_step(text: str, replacement: str) -> str:
    return _once(text, _pytest_step(text), replacement)


Mutation = Callable[[str, Gate], str]

# case -> (mutation of a real workflow, fragment the rejection must contain)
REJECTED: dict[str, tuple[Mutation, str]] = {
    "step-removed": (lambda t, g: _with_step(t, ""), "found 0"),
    "turned-into-echo": (
        lambda t, g: _once(t, PYTEST_LINE, PYTEST_LINE.replace("&& python", "&& echo python")),
        "found 0",
    ),
    "tests-only-in-yaml-comment": (
        lambda t, g: _once(
            _once(t, FILTER_LINE, f"          -W {COROUTINE_FILTER}\n"),
            _step_name_line(t),
            "      # tests\n" + _step_name_line(t),
        ),
        "positional arguments must be exactly ['tests'], got []",
    ),
    "tests-only-in-step-name": (
        lambda t, g: _once(
            _once(t, FILTER_LINE, f"          -W {COROUTINE_FILTER}\n"),
            _step_name_line(t),
            "      - name: Run pytest on tests\n",
        ),
        "positional arguments must be exactly ['tests'], got []",
    ),
    "filter-dropped": (lambda t, g: _once(t, FILTER_LINE, "          tests\n"), "coroutine filter"),
    "narrowed-to-files": (
        lambda t, g: _once(
            t,
            FILTER_LINE,
            f"          -W {COROUTINE_FILTER}\n"
            "          tests/test_frontier_runtime.py tests/test_readme_runtime_truth.py\n",
        ),
        "positional arguments must be exactly ['tests']",
    ),
    "narrowed-to-node-id": (
        lambda t, g: _once(t, FILTER_LINE, FILTER_LINE.replace(" tests\n", " tests/test_frontier_runtime.py::test_x\n")),
        "positional arguments must be exactly ['tests']",
    ),
    "tests-plus-file": (
        lambda t, g: _once(t, FILTER_LINE, FILTER_LINE.replace(" tests\n", " tests tests/test_frontier_runtime.py\n")),
        "positional arguments must be exactly ['tests']",
    ),
    "command-only-in-commentary": (
        lambda t, g: _with_step(
            t,
            f"      # {FULL_COMMAND}\n"
            f"      - name: {FULL_COMMAND}\n"
            f'        run: echo "{FULL_COMMAND}"\n',
        ),
        "found 0",
    ),
    "folded-shell-comment": (
        lambda t, g: _once(t, PYTEST_LINE, PYTEST_LINE.replace("&& python", "# python")),
        "found 0",
    ),
    "or-true": (
        lambda t, g: _once(t, FILTER_LINE, FILTER_LINE + "          || true\n"),
        "last command of its step",
    ),
    "reached-through-or": (
        lambda t, g: _once(t, PYTEST_LINE, PYTEST_LINE.replace("&&", "||")),
        "last command of its step",
    ),
    "later-command": (
        lambda t, g: _once(t, FILTER_LINE, FILTER_LINE + "          ; exit 0\n"),
        "last command of its step",
    ),
    "deselect-added": (
        lambda t, g: _once(t, FILTER_LINE, f"          -W {COROUTINE_FILTER} --deselect tests/test_frontier_runtime.py tests\n"),
        "'--deselect' is not allowed",
    ),
    "warnings-plugin-disabled": (
        lambda t, g: _once(t, PYTEST_LINE, PYTEST_LINE.replace("no:cacheprovider", "no:warnings")),
        "-p 'no:warnings' is not allowed",
    ),
    "filter-overridden": (
        lambda t, g: _once(t, FILTER_LINE, FILTER_LINE.replace(" tests\n", " -W ignore::pytest.PytestUnhandledCoroutineWarning tests\n")),
        "is not allowed",
    ),
    "step-if-false": (
        lambda t, g: _once(t, _step_name_line(t), _step_name_line(t) + "        if: false\n"),
        "must only have name and run, found ['if']",
    ),
    "step-continue-on-error": (
        lambda t, g: _once(t, _step_name_line(t), _step_name_line(t) + "        continue-on-error: true\n"),
        "must only have name and run, found ['continue-on-error']",
    ),
    "second-pytest-step": (lambda t, g: _with_step(t, _pytest_step(t) + "\n" + _pytest_step(t)), "found 2"),
    "pytest-addopts": (
        lambda t, g: _once(t, "\njobs:\n", "\nenv:\n  PYTEST_ADDOPTS: -p no:warnings\njobs:\n"),
        "PYTEST_ADDOPTS must not be set",
    ),
    "job-if-false": (
        lambda t, g: _once(t, f"\n  {g.job}:\n", f"\n  {g.job}:\n    if: false\n"),
        "job-level 'if'",
    ),
    "workflow-defaults": (
        lambda t, g: _once(t, "\njobs:\n", "\ndefaults:\n  run:\n    shell: bash\njobs:\n"),
        "workflow-level 'defaults'",
    ),
}
REJECTED_HF_SYNC: dict[str, tuple[Mutation, str]] = {
    "moved-after-publish": (
        lambda t, g: _once(_with_step(t, ""), PUBLISH_STEP, PUBLISH_STEP + "\n" + _pytest_step(t)),
        "must run after the pytest step",
    ),
}
# Equivalent spellings that must stay accepted, so rejections above are for
# the named reason rather than incidental breakage.
ACCEPTED: dict[str, Mutation] = {
    "literal-block-two-lines": lambda t, g: _once(
        t,
        _pytest_step(t)[len(_step_name_line(t)) :],
        "        run: |\n"
        '          python -m pip install --disable-pip-version-check --no-cache-dir "pytest==8.3.5"\n'
        f"          python -m pytest -W {COROUTINE_FILTER} -q tests\n",
    ),
    "trailing-yaml-comment": lambda t, g: _once(t, FILTER_LINE, FILTER_LINE + "      # end of pytest gate\n"),
}


class CiPytestStepGuardTest(unittest.TestCase):
    def test_real_gates_run_full_pytest_with_coroutine_filter(self) -> None:
        for gate in GATES:
            text = gate.workflow.read_text(encoding="utf-8")
            for reader_name, read in readers():
                with self.subTest(gate=gate.workflow.name, reader=reader_name):
                    self.assertEqual([], gate_problems(text, gate, read))
            if yaml is not None:
                with self.subTest(gate=gate.workflow.name, reader="line reader == PyYAML"):
                    self.assertEqual(read_yaml(text, gate.job), read_lines(text, gate.job))

    def test_mutated_copies_of_the_gates_fail_for_the_named_reason(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            for gate in GATES:
                original = gate.workflow.read_text(encoding="utf-8")
                cases = dict(REJECTED, **(REJECTED_HF_SYNC if gate.publish else {}))
                for case, (mutate, reason) in sorted(cases.items()):
                    copy = Path(directory) / f"{case}.{gate.workflow.name}"
                    copy.write_text(mutate(original, gate), encoding="utf-8")
                    mutated = copy.read_text(encoding="utf-8")
                    for reader_name, read in readers():
                        with self.subTest(gate=gate.workflow.name, case=case, reader=reader_name):
                            problems = gate_problems(mutated, gate, read)
                            self.assertTrue(
                                any(reason in problem for problem in problems),
                                f"expected {reason!r} in {problems}",
                            )

    def test_equivalent_spellings_stay_accepted(self) -> None:
        for gate in GATES:
            original = gate.workflow.read_text(encoding="utf-8")
            for case, mutate in sorted(ACCEPTED.items()):
                mutated = mutate(original, gate)
                for reader_name, read in readers():
                    with self.subTest(gate=gate.workflow.name, case=case, reader=reader_name):
                        self.assertEqual([], gate_problems(mutated, gate, read))


if __name__ == "__main__":
    unittest.main()
