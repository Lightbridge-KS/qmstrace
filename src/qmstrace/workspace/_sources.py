"""Surrounding sibling, external and change-request evidence.

Implements: DSN-QMT-02, DSN-QMT-07
"""

from __future__ import annotations

import posixpath
from collections import Counter
from dataclasses import replace
from pathlib import Path

from qmstrace.core import findings
from qmstrace.core.assessment import ExternalState, SiblingState
from qmstrace.core.baselines import Register
from qmstrace.core.config import ExternalSource, TraceConfig
from qmstrace.core.errors import CouldNotJudge
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


def _register(root: Path, ledger: Path | None, config: TraceConfig) -> Register:
    spec = config.change_requests
    if spec is None:
        return Register()
    location = _shown(root, ledger / spec.source) if ledger else None
    files = request_files(ledger / spec.source, spec.prefix) if ledger else None
    if files is None:
        return Register(location, accepted=spec.accepted)
    requests = []
    wrong = []
    for name, text in files.items():
        file = posixpath.join(location or "", name)
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
    ledger: Path | None, source: ExternalSource, root: Path
) -> tuple[ExternalState, frozenset[str] | None]:
    """An external source and the IDs it declares — `None` when it could not be read."""
    if ledger is None:
        return ExternalState(source.name, source.prefix, None, None), None
    path = ledger / source.source
    text = _read(path)
    declared = source.declared_in(text) if text is not None else None
    count = len(declared) if declared is not None else None
    return ExternalState(source.name, source.prefix, _shown(root, path), count), declared


def _siblings(
    root: Path, config: TraceConfig, trees: TreeFactory, ledger: Path | None
) -> tuple[list[tuple[SiblingState, dict[str, Item] | None, tuple[Link, ...]]], bool, bool]:
    """Each sibling with its items (None when not read) and the links those items declare;
    whether the siblings could be located at all; whether this repo is among the project's
    repos."""
    if ledger is None:
        return [], not config.repos, False
    found: list[tuple[SiblingState, dict[str, Item] | None, tuple[Link, ...]]] = []
    listed = False
    for name, relative in sorted(config.repos.items()):
        path = ledger / relative
        location = _shown(root, path)
        if _same(path, root):
            listed = True
            continue
        if not (path / CONFIG_FILE).is_file():
            found.append((SiblingState(name, location, None, "not reachable"), None, ()))
            continue
        try:
            tree = trees(path)
            config = _configuration(path, tree)
        except CouldNotJudge as stopped:
            problem = f"its configuration could not be read — {stopped.what}"
            found.append((SiblingState(name, location, None, problem), None, ()))
            continue
        authored = [t for t in config.item_types.values() if t.id_pattern is not None]
        scan = _scan(tree, config, authored, with_misplaced=False)
        # a sibling's files, as a reader of this repo would write them: ../service/docs/…
        items = {
            i.id: replace(i, file=posixpath.join(location, i.file))
            for part in scan.extracted
            for i in part.items
        }
        links = tuple(
            replace(link, file=posixpath.join(location, link.file))
            for part in scan.extracted
            for link in part.links
            if link.src in items
        )
        counts = Counter(item.type for item in items.values())
        declares = {t.name: counts[t.name] for t in authored if counts[t.name]}
        found.append((SiblingState(name, location, declares), items, links))
    return found, True, listed
