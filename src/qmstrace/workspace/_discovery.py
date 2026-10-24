"""Repository discovery, configuration loading and repository-relative paths.

Implements: DSN-QMT-02
"""

from __future__ import annotations

import os
import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Final

from qmstrace.core.config import SchemaForm, TraceConfig
from qmstrace.core.errors import CouldNotJudge
from qmstrace.infra.locations import relative
from qmstrace.infra.tree import GitTree, ISourceTree

CONFIG_FILE: Final = "qmstrace.toml"


SCHEMA_FILE: Final = "qmstrace.schema.toml"


TreeFactory = Callable[[Path], ISourceTree]


def _find_root(start: Path) -> Path:
    here = Path(os.path.abspath(start))
    for folder in (here, *here.parents):
        if (folder / CONFIG_FILE).is_file():
            return folder
        if (folder / SCHEMA_FILE).is_file():
            raise CouldNotJudge(
                f"{folder} is a project's ledger repo — it holds {SCHEMA_FILE} — and this "
                "command runs in a product repo.",
                "Fix: run it in one of the project's product repos (the schema's [repos] names "
                "them), or point at one with -C <path>; the ledger's own verbs are under "
                "qmstrace ledger.",
            )
    raise CouldNotJudge(
        f"there is no {CONFIG_FILE} in {here} or any folder above it, so this is not a traced "
        "product repo.",
        "Fix: run qmstrace inside a product repo, or point at one with -C <path>.",
    )


def _find_ledger(start: Path) -> Path:
    here = Path(os.path.abspath(start))
    for folder in (here, *here.parents):
        if (folder / SCHEMA_FILE).is_file():
            return folder
        if (folder / CONFIG_FILE).is_file():
            try:
                pointer = tomllib.loads((folder / CONFIG_FILE).read_text(encoding="utf-8"))
            except (OSError, UnicodeError, tomllib.TOMLDecodeError):
                pointer = {}
            ledger = pointer.get("ledger")
            where = f" — its ledger is at {ledger}" if isinstance(ledger, str) else ""
            raise CouldNotJudge(
                f"{folder} is a product repo{where} — and this command runs in the project's "
                "ledger repo.",
                f"Fix: run it where {SCHEMA_FILE} is, or point there with -C <path>.",
            )
    raise CouldNotJudge(
        f"there is no {SCHEMA_FILE} in {here} or any folder above it, so this is not a "
        "project's ledger repo.",
        "Fix: run qmstrace ledger inside the ledger repo, or point at it with -C <path>.",
    )


def _configuration(root: Path, tree: ISourceTree) -> TraceConfig:
    try:
        local = tree.read(CONFIG_FILE)
    except UnicodeDecodeError:
        raise CouldNotJudge(
            f"{CONFIG_FILE} in {root} is not UTF-8 text.", "Fix: save it as UTF-8."
        ) from None
    reference = TraceConfig.schema_reference(local)
    try:
        schema = (
            (tree.read(reference) if isinstance(tree, GitTree) else _read(root / reference))
            if reference
            else None
        )
    except UnicodeDecodeError:
        raise CouldNotJudge(
            f"Historical schema '{reference}' is not UTF-8 text.",
            "Fix: inspect the tagged schema; a current schema cannot replace it.",
        ) from None
    return TraceConfig.parse(local, schema)


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None


def _ledger(root: Path, config: TraceConfig) -> Path | None:
    """Where the agreement and the project's other repos are looked for."""
    if config.version == 2:
        return root if config.repo == config.ledger_repo else None
    if config.schema_form is SchemaForm.OWN:
        return root
    return root / config.ledger if config.ledger else None


def _shown(root: Path, path: Path) -> str:
    """A path as a reader of this repo would write it — relative, and never resolved, so a
    temporary folder's real location never leaks into the output."""
    return relative(root, path)


def _report_label(root: Path, path: Path) -> str:
    """A report's label: its path from the root when it is inside the repo, else its file name
    alone — never a path of the machine, nor the climb out of the repo to it."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.name


def _ledger_configuration(root: Path, schema_text: str) -> TraceConfig:
    """A v2 ledger supplies its real identity/profile; a legacy schema may stand alone."""
    schema = TraceConfig.of_schema(schema_text)
    if schema.version == 1:
        return schema
    local = _read(root / CONFIG_FILE)
    if local is None:
        raise CouldNotJudge(
            "A v2 ledger requires a readable qmstrace.toml with repo and workspace_profile.",
            'Fix: create its v2 local header and [schema] path = "qmstrace.schema.toml".',
        )
    reference = TraceConfig.schema_reference(local)
    if reference is None or not _same(root / reference, root / SCHEMA_FILE):
        raise CouldNotJudge(
            "A v2 ledger must read its authoritative qmstrace.schema.toml by path.",
            'Fix: set [schema] path = "qmstrace.schema.toml"; a map cannot repair the reference.',
        )
    own = TraceConfig.parse(local, _read(root / reference))
    if own.repo != schema.ledger_repo or own.schema_digest != schema.schema_digest:
        raise CouldNotJudge(
            "The ledger's local identity or schema differs from the schema it owns.",
            "Fix: declare the ledger role and read its authoritative schema by path.",
        )
    return own


def _same(one: Path, other: Path) -> bool:
    """Whether two paths name one folder — by their text first, since in a pipeline the ledger
    they are written through may not exist; then on disk, which also sees through links."""
    if os.path.normpath(os.path.abspath(one)) == os.path.normpath(os.path.abspath(other)):
        return True
    try:
        return os.path.samefile(one, other)
    except OSError:
        return False
