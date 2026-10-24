"""Schema-copy fingerprints and TOML-aware marker recognition.

Implements: DSN-QMT-03
"""

from __future__ import annotations

import hashlib
import json
import tomllib
from collections.abc import Mapping
from typing import Final

# A product repo's copy of the project's trace schema sits between these two comment lines —
# generated in the ledger by `qmstrace ledger copy-schema`, never edited by hand (D9).
COPY_BEGIN: Final = "# qmstrace:begin"
COPY_END: Final = "# qmstrace:end"


def structural(lines: list[str]) -> list[bool]:
    """For each line, whether everything above it is complete TOML — only such a line can be a
    table header or a copy marker, never one inside a multi-line string or array."""
    found: list[bool] = []
    for index, line in enumerate(lines):
        if not line.lstrip().startswith(("[", "#")):
            found.append(False)
            continue
        try:
            tomllib.loads("".join(lines[:index]))
        except tomllib.TOMLDecodeError:
            found.append(False)
        else:
            found.append(True)
    return found


def marked(text: str) -> bool:
    """Whether the text holds a schema copy's begin marker, where a marker can be."""
    lines = text.splitlines(keepends=True)
    return any(
        ok and line.startswith(COPY_BEGIN)
        for line, ok in zip(lines, structural(lines), strict=True)
    )


def schema_digest(schema: Mapping[str, object]) -> str:
    """The digest of a trace schema's content — independent of key order, comments and layout.

    `digest` and `path` are not part of the content, so the same function serves the ledger's
    file and a product repo's copy of it.
    """
    content = {k: v for k, v in schema.items() if k not in {"digest", "path"}}
    repos = content.get("repos")
    if content.get("version") == 2 and isinstance(repos, dict):
        members = repos.get("members")
        if isinstance(members, list) and all(isinstance(name, str) for name in members):
            content["repos"] = {**repos, "members": sorted(members)}
    canonical = json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
