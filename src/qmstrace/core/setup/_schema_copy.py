"""Inspect and replace the schema copy, preserving everything outside its block.

Implements: DSN-QMT-11
"""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from typing import Literal

from qmstrace.core.config import COPY_BEGIN, COPY_END, TraceConfig, schema_digest, structural
from qmstrace.core.errors import CouldNotJudge


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
    skipped: bool = False  # the ledger itself, listed as "." — it reads its schema by path
    location_notice: str | None = None


def ledger_itself(local_text: str | None) -> str:
    """Why the ledger's own entry in [repos] is skipped, in the words its report line uses —
    and, for a ledger that already holds a copy of its own schema, how to undo it."""
    if local_text is None:
        return "it holds the schema"
    try:
        held = held_schema(local_text)
    except CouldNotJudge:
        return "it holds the schema"
    if held.kind == "copy":
        return (
            "but its qmstrace.toml holds a copy of its own schema — replace that [schema] with "
            'path = "qmstrace.schema.toml", so the ledger reads the rules it holds'
        )
    if held.kind == "path":
        return "its qmstrace.toml reads qmstrace.schema.toml by path"
    return "it holds the schema"


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
