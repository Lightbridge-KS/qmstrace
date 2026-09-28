"""Pure edits for setup: managed guide blocks, existing pytest configuration, and the
project's schema copied into a product repo's configuration.

Implements: DSN-QMT-11
"""

from __future__ import annotations

import configparser
import json
import re
import tomllib
from dataclasses import dataclass
from typing import Literal

from qmstrace.core.config import (
    COPY_BEGIN,
    COPY_END,
    TraceConfig,
    schema_digest,
    structural,
)
from qmstrace.core.errors import CouldNotJudge

BEGIN = "<!-- qmstrace:begin"
END = "<!-- qmstrace:end -->"
MARKER = "verifies(*ids): trace the items this test actually verifies"

# Where the packaged skill is installed: the folder harnesses read for a repo's skills, named
# after the skill. Claude Code reads its own folder, so it is linked there when the repo has one.
SKILL_FILE = ".agents/skills/qmstrace/SKILL.md"
CLAUDE_LINK = ".claude/skills/qmstrace"
CLAUDE_LINK_TARGET = "../../.agents/skills/qmstrace"  # relative to the link's folder
LEGACY_SKILL = ".qmstrace/skill/SKILL.md"  # the skill's home before M9c


def stanza(template: str, config: TraceConfig) -> str:
    return template.format(
        skill=SKILL_FILE,
        project=config.project,
        subjects=", ".join(f"{s.name} ({s.key})" for s in config.subjects.values())
        or "none declared",
        items="; ".join(
            f"{t.name} `{t.id_pattern.pattern if t.id_pattern else t.extractor}` in "
            + ", ".join(f"`{p}`" for p in t.files)
            for t in config.item_types.values()
            if t.declared_here
        ),
    )


def guide(original: str, block: str) -> str:
    if BEGIN not in original and END not in original:
        return original + ("\n" if original.endswith("\n") else "\n\n" if original else "") + block
    if original.count(BEGIN) != 1 or original.count(END) != 1:
        raise CouldNotJudge(
            "The agent guide has conflicting qmstrace markers.",
            "Fix: keep exactly one begin/end pair, then run init again.",
        )
    start, end = original.index(BEGIN), original.index(END)
    if end < start:
        raise CouldNotJudge(
            "The agent guide closes its qmstrace block before it begins.",
            "Fix: repair the begin/end pair, then run init again.",
        )
    return original[:start] + block.rstrip("\n") + original[end + len(END) :]


def pytest_section(name: str, source: str) -> str | None:
    """Return the active section in one candidate, in pytest's discovery order."""
    try:
        if name.endswith(".toml"):
            data = tomllib.loads(source)
            if name != "pyproject.toml":
                return "pytest"
            tool = data.get("tool", {}).get("pytest", {})
            if "ini_options" in tool and len(tool) > 1:
                raise ValueError("Both native pytest and ini_options settings are present")
            if "ini_options" in tool:
                return "tool.pytest.ini_options"
            return "tool.pytest" if "pytest" in data.get("tool", {}) else None
        data_ini = configparser.ConfigParser(interpolation=None)
        data_ini.read_string(source)
        section = "tool:pytest" if name == "setup.cfg" else "pytest"
        return section if name in {"pytest.ini", ".pytest.ini"} or section in data_ini else None
    except (ValueError, configparser.Error, AttributeError) as exc:
        raise CouldNotJudge(
            f"Cannot read {name}: {exc}", "Fix: repair its configuration before running init."
        ) from exc


def register_marker(name: str, source: str, section: str) -> str:
    """Keep other settings verbatim; change only the existing marker value or add it."""
    match = re.search(r"(?m)^\[" + re.escape(section) + r"\][^\n]*(?:\n|$)", source)
    if match is None:
        # A valid but unconventional TOML table must not be duplicated.
        if name.endswith(".toml"):
            data = tomllib.loads(source)
            branch: object = data
            for part in section.split("."):
                branch = branch.get(part) if isinstance(branch, dict) else None
            if branch is not None:
                raise CouldNotJudge(
                    f"{name} uses a nonstandard spelling of [{section}].",
                    "Fix: use a plain table header, then rerun init.",
                )
        addition = f"\n[{section}]\n"
        source += addition
        return register_marker(name, source, section)
    next_header = re.search(r"(?m)^\[", source[match.end() :])
    end = match.end() + next_header.start() if next_header else len(source)
    body = source[match.end() : end]
    field = re.search(
        r"^[ \t]*markers[ \t]*=[ \t]*",
        body,
        re.MULTILINE | (0 if name.endswith(".toml") else re.IGNORECASE),
    )
    if name.endswith(".toml"):
        data = tomllib.loads(source)
        table = data
        for part in section.split("."):
            table = table[part]
        markers = table.get("markers", [])
        if isinstance(markers, str):
            markers = markers.splitlines()
        if not isinstance(markers, list) or any(not isinstance(m, str) for m in markers):
            raise CouldNotJudge(
                f"{name}: markers must be strings.", "Fix: correct the markers setting."
            )
        if any(re.match(r"^\s*verifies\b", m) for m in markers):
            return source
        value = "markers = " + json.dumps([*markers, MARKER], ensure_ascii=False) + "\n"
        if "markers" in table and field is None:
            raise CouldNotJudge(
                "Cannot safely locate the markers assignment.",
                "Fix: use an unquoted markers key in the pytest table.",
            )
        if field:
            # The first complete TOML value terminates the original assignment, including arrays.
            stop = field.end()
            for line in body[field.end() :].splitlines(keepends=True):
                stop += len(line)
                try:
                    tomllib.loads("markers = " + body[field.end() : stop])
                except ValueError:
                    continue
                break
            body = body[: field.start()] + value + body[stop:]
        else:
            body = value + body
    else:
        ini = configparser.ConfigParser(interpolation=None)
        ini.read_string(source)
        markers = ini.get(section, "markers", fallback="")
        if any(re.match(r"^\s*verifies\b", m) for m in markers.splitlines()):
            return source
        if field:
            line_end = body.find("\n", field.end())
            if line_end < 0:
                body += "\n"
                line_end = len(body) - 1
            body = body[: line_end + 1] + "    " + MARKER + "\n" + body[line_end + 1 :]
        else:
            body = "markers =\n    " + MARKER + "\n" + body
    return source[: match.end()] + body + source[end:]


# ── the schema copy (D9) ────────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class Held:
    """What a product repo's configuration holds as the project's schema, and on which lines.

    `start` and `end` bound the lines a copy replaces: the marked block, or — before the first
    copy — the run of consecutive `[schema…]` tables.
    """

    start: int
    end: int
    kind: Literal["path", "copy", "empty", "own"]
    path: str | None = None
    project: str | None = None
    digest: str | None = None
    edited: bool = False  # a copy whose content no longer matches its digest


@dataclass(frozen=True, slots=True)
class Copied:
    """One repo's copy, as `qmstrace ledger copy-schema` reports it."""

    repo: str  # its name in the schema's [repos]
    file: str  # its qmstrace.toml, as the ledger reaches it
    changed: bool
    before: str  # what it held: by path, a copy of older rules, one edited by hand, …


def before_copy(held: Held, digest: str) -> str:
    """What a repo held before the copy, in the words its report line uses."""
    if held.kind == "path":
        return "was by path"
    if held.kind == "empty":
        return "was an empty [schema]"
    if held.edited:
        return "replaced a copy edited by hand"
    if held.digest == digest:
        return "layout only — rules unchanged"
    return f"rules changed (was {held.digest})"


def held_schema(local_text: str, file: str = "qmstrace.toml") -> Held:
    """Find the project's schema in a product repo's configuration, and say what form it is in."""
    try:
        whole = tomllib.loads(local_text)
    except tomllib.TOMLDecodeError as broken:
        raise CouldNotJudge(
            f"{file} is not valid TOML: {broken}.", "Fix: correct the file's syntax."
        ) from None
    lines = local_text.splitlines(keepends=True)
    ok = structural(lines)
    headers = [
        (index, next(iter(tomllib.loads(line)), ""))
        for index, (line, fits) in enumerate(zip(lines, ok, strict=True))
        if fits and line.lstrip().startswith("[")
    ]
    begins = [i for i, line in enumerate(lines) if ok[i] and line.startswith(COPY_BEGIN)]
    ends = [i for i, line in enumerate(lines) if ok[i] and line.startswith(COPY_END)]
    if begins or ends:
        if len(begins) != 1 or len(ends) != 1 or ends[0] < begins[0]:
            raise CouldNotJudge(
                f"{file} has conflicting qmstrace markers around the schema copy.",
                "Fix: keep exactly one begin/end pair around one [schema] block, then copy again.",
            )
        start, end = begins[0], ends[0] + 1
        if any(key == "schema" and not start < index < end for index, key in headers):
            raise CouldNotJudge(
                f"{file} has a [schema…] table outside the generated block.",
                "Fix: move it inside the markers or remove it — the copy owns every schema table.",
            )
    else:
        schema_rows = [index for index, key in headers if key == "schema"]
        if not schema_rows and "schema" in whole:
            raise CouldNotJudge(
                f"{file} sets schema keys outside its [schema] tables.",
                "Fix: move them into a [schema] table, then copy again.",
            )
        if not schema_rows:
            raise CouldNotJudge(
                f"{file} has no [schema] table.",
                'Fix: add [schema] with path = "<ledger>/qmstrace.schema.toml", then copy again.',
            )
        start, end = schema_rows[0], len(lines)
        for index, key in headers:
            if index > start and key != "schema":
                end = index
                break
        if any(key == "schema" and index >= end for index, key in headers):
            raise CouldNotJudge(
                f"{file} has its [schema…] tables split around other tables.",
                "Fix: keep the schema tables together, then copy again.",
            )
        while end > start + 1 and (not lines[end - 1].strip() or lines[end - 1].startswith("#")):
            end -= 1  # blank lines and a comment above the next table belong to what follows
    outside = tomllib.loads("".join(lines[:start] + lines[end:]))
    if "schema" in outside:
        raise CouldNotJudge(
            f"{file} sets schema keys outside its [schema] tables.",
            "Fix: move them into the [schema] tables, then copy again.",
        )
    held = tomllib.loads("".join(lines[start:end])).get("schema", {})
    if "path" in held:
        return Held(start, end, "path", path=str(held["path"]))
    if "digest" in held:
        stated = str(held["digest"])
        project = held.get("project")
        return Held(
            start,
            end,
            "copy",
            project=project if isinstance(project, str) else None,
            digest=stated,
            edited=schema_digest(held) != stated,
        )
    return Held(start, end, "own" if held else "empty")


def schema_block(schema_text: str, project: str) -> str:
    """The project's trace schema as the marked, digested block a product repo carries."""
    lines = schema_text.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    block = [
        f"{COPY_BEGIN} — the {project} trace schema, generated in its ledger by "
        "`qmstrace ledger copy-schema`; edit it there, never here\n",
        "[schema]\n",
        f'digest = "{schema_digest(tomllib.loads(schema_text))}"\n',
    ]
    for line, fits in zip(lines, structural(lines), strict=True):
        if fits and line.lstrip().startswith("["):
            line = re.sub(r"^(\s*\[\[?\s*)", r"\1schema.", line, count=1)
        block.append(line)
    while block and not block[-1].strip():
        block.pop()
    return "".join(block) + COPY_END + "\n"


def copy_schema(local_text: str, held: Held, block: str, file: str = "qmstrace.toml") -> str:
    """Put the block where the held schema was, keeping every other byte — then prove it."""
    lines = local_text.splitlines(keepends=True)
    newline = "\r\n" if "\r\n" in local_text else "\n"
    written = block.replace("\n", newline)
    updated = "".join(lines[: held.start]) + written + "".join(lines[held.end :])
    before, after = tomllib.loads(local_text), tomllib.loads(updated)
    copy = after.get("schema", {})
    if {k: v for k, v in before.items() if k != "schema"} != {
        k: v for k, v in after.items() if k != "schema"
    } or copy.get("digest") != schema_digest(copy):
        raise CouldNotJudge(
            f"{file}: the schema copy could not be written without changing something else.",
            "Fix: nothing was written — report this, with the ledger's schema and this file.",
        )
    TraceConfig.parse(updated, local_name=file)  # the repo still loads under the new rules
    return updated
