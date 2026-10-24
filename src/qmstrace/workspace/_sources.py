"""Surrounding sibling, external and change-request evidence.

Implements: DSN-QMT-02, DSN-QMT-07
"""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from pathlib import Path

from qmstrace.core import findings
from qmstrace.core.assessment import ExternalState, SiblingState
from qmstrace.core.baselines import Register
from qmstrace.core.config import ExternalSource, TraceConfig
from qmstrace.core.errors import CouldNotJudge
from qmstrace.core.locations import Locations, joined, qualify
from qmstrace.core.model import ID_TOKEN, Item, Link
from qmstrace.extract import change_requests
from qmstrace.infra.externals import request_files
from qmstrace.workspace._discovery import (
    CONFIG_FILE,
    TreeFactory,
    _configuration,
    _read,
    _same,
    _shown,
)
from qmstrace.workspace._scanning import _scan


def _source_location(
    root: Path, path: Path, ledger: Path, config: TraceConfig, locations: Locations | None
) -> str:
    name = locations.ledger_repo if locations else config.ledger_repo
    if name:
        try:
            internal = path.resolve().relative_to(ledger.resolve()).as_posix()
        except (OSError, RuntimeError, ValueError):
            # An explicitly configured out-of-tree source has no verified repo owner.
            # Keep its read semantics, using a safe label as with external reports.
            return path.name
        return qualify(name, internal)
    return _shown(root, path)


def _register(
    root: Path, ledger: Path | None, config: TraceConfig, locations: Locations | None = None
) -> Register:
    spec = config.change_requests
    if spec is None:
        return Register()
    location = (
        _source_location(root, ledger / spec.source, ledger, config, locations) if ledger else None
    )
    files = request_files(ledger / spec.source, spec.prefix) if ledger else None
    if files is None:
        return Register(location, accepted=spec.accepted)
    requests = []
    wrong = []
    for name, text in files.items():
        file = joined(location or "", name)
        if text is None:
            wrong.append(findings.cannot_read(file))
            continue
        request_id = name.removesuffix(".md")
        if not ID_TOKEN.fullmatch(request_id):
            wrong.append(findings.cannot_parse(file, 1, "request filename is not an ID"))
            continue
        request, problem = change_requests.read(file, request_id, text)
        if request:
            requests.append(request)
        else:
            wrong.append(findings.cannot_parse(file, 1, problem or "invalid request metadata"))
    return Register(location, True, spec.accepted, tuple(requests), tuple(wrong))


def _external(
    ledger: Path | None,
    source: ExternalSource,
    root: Path,
    locations: Locations | None = None,
    config: TraceConfig | None = None,
) -> tuple[ExternalState, frozenset[str] | None]:
    """An external source and the IDs it declares — `None` when it could not be read."""
    if ledger is None:
        return ExternalState(source.name, source.prefix, None, None), None
    path = ledger / source.source
    text = _read(path)
    declared = source.declared_in(text) if text is not None else None
    count = len(declared) if declared is not None else None
    location = (
        _source_location(root, path, ledger, config, locations) if config else _shown(root, path)
    )
    return ExternalState(source.name, source.prefix, location, count), declared


def _siblings(
    root: Path,
    config: TraceConfig,
    trees: TreeFactory,
    ledger: Path | None,
    locations: Locations | None = None,
) -> tuple[list[tuple[SiblingState, dict[str, Item] | None, tuple[Link, ...]]], bool, bool]:
    """Each sibling with its items (None when not read) and the links those items declare;
    whether the siblings could be located at all; whether this repo is among the project's
    repos."""
    if ledger is None:
        return [], not config.repos, False
    found: list[tuple[SiblingState, dict[str, Item] | None, tuple[Link, ...]]] = []
    listed = False
    project_name = config.project
    for name, relative in sorted(config.repos.items()):
        path = (
            locations.roots.get(name)
            if locations
            else (root if name == config.repo else None)
            if config.version == 2
            else ledger / relative
        )
        if path is None:
            found.append((SiblingState(name, "not mapped", None, "not reachable"), None, ()))
            continue
        location = qualify(name)
        if _same(path, root):
            listed = True
            continue
        if not (path / CONFIG_FILE).is_file():
            found.append((SiblingState(name, location, None, "not reachable"), None, ()))
            continue
        try:
            tree = trees(path)
            own = _configuration(path, tree)
        except CouldNotJudge as stopped:
            problem = f"its configuration could not be read — {stopped.what}"
            found.append((SiblingState(name, location, None, problem), None, ()))
            continue
        if locations and (own.project != project_name or (own.version == 2 and own.repo != name)):
            raise CouldNotJudge(
                f"Mapped member {name} belongs to project {own.project}, not {project_name}.",
                "Fix: bind the member to the intended project's trace root.",
            )
        authored = [t for t in own.item_types.values() if t.id_pattern is not None]
        scan = _scan(tree, own, authored, with_misplaced=False)
        # Logical source labels never reconstruct native sibling checkout paths.
        items = {
            i.id: replace(i, file=joined(location, i.file))
            for part in scan.extracted
            for i in part.items
        }
        links = tuple(
            replace(link, file=joined(location, link.file))
            for part in scan.extracted
            for link in part.links
            if link.src in items
        )
        counts = Counter(item.type for item in items.values())
        declares = {t.name: counts[t.name] for t in authored if counts[t.name]}
        found.append((SiblingState(name, location, declares), items, links))
    return found, True, listed
