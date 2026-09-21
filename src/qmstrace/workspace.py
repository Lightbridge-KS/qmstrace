"""The workspace — the one place that sequences a run: find the repo, read it, judge it.

`Workspace.open(start)` walks up to the trace configuration and reads it; `assessment()` scans
the tree, reads what lies outside the repo — the ledger's external sources, the project's
other repos — and builds the graph once. A command renders the result.

One scan function serves every tree. A sibling is read with the same function, for the item
types that carry authored IDs; its own findings are its own business and are dropped, and its
own siblings are never read.
"""

from __future__ import annotations

import os
import posixpath
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final

from qmstrace.core import findings
from qmstrace.core.assessment import Assessment, ExternalState, Scanned, SiblingState
from qmstrace.core.config import ExternalSource, ItemType, SchemaForm, TraceConfig
from qmstrace.core.errors import CouldNotJudge
from qmstrace.core.graph import Surroundings, TraceGraph
from qmstrace.core.model import Extracted, Finding, Item, Notice
from qmstrace.extract.base import REGISTRY
from qmstrace.infra.globbing import matches
from qmstrace.infra.tree import ISourceTree, WorkingTree

CONFIG_FILE: Final = "qmstrace.toml"
SCHEMA_FILE: Final = "qmstrace.schema.toml"
_MARKDOWN: Final = ("*.md", "**/*.md", "*.qmd", "**/*.qmd")

TreeFactory = Callable[[Path], ISourceTree]


@dataclass(frozen=True, slots=True)
class _Scan:
    """What one scan of one tree found."""

    extracted: tuple[Extracted, ...]
    scanned: tuple[Scanned, ...]
    misplaced: tuple[Item, ...]


@dataclass(frozen=True, slots=True)
class Workspace:
    """A product repo, opened: its root, its tree and its configuration."""

    root: Path
    tree: ISourceTree
    config: TraceConfig
    trees: TreeFactory

    @classmethod
    def open(cls, start: Path, *, trees: TreeFactory = WorkingTree) -> Workspace:
        """Find the product repo at or above `start`, and read its trace configuration.

        Raises
        ------
        CouldNotJudge
            When no trace configuration is found, when `start` is inside a ledger repo, or when
            the configuration cannot be trusted.
        """
        root = _find_root(start)
        tree = trees(root)
        return cls(root, tree, _configuration(root, tree), trees)

    def assessment(self) -> Assessment:
        """Scan, read what lies around the repo, build the graph — once."""
        config = self.config
        scan = _scan(self.tree, config, config.item_types.values(), with_misplaced=True)
        ledger = _ledger(self.root, config)
        externals = [
            _external(ledger, config.externals[name], self.root)
            for name in sorted(config.externals)
        ]
        siblings, located, listed = self._siblings(ledger)
        around = Surroundings(
            siblings={s.name: items for s, items in siblings if items is not None},
            every_sibling_read=located and all(items is not None for _, items in siblings),
            externals={state.name: declared for state, declared in externals},
        )
        graph, violations = TraceGraph.build(
            config, scan.extracted, around, misplaced=scan.misplaced
        )

        notices: list[Notice] = []
        if located and config.repos and not listed:
            notices.append(
                Notice(
                    "this repo is not among the project's repos in the trace schema ([repos] "
                    f"lists {', '.join(sorted(config.repos))}) — the ledger's import will not "
                    "read it"
                )
            )
        if config.baselines:
            names = ", ".join(config.baselines)
            notices.append(
                Notice(
                    f"baselines: {len(config.baselines)} configured ({names}) — not judged: this "
                    "version of qmstrace does not read baselines yet"
                )
            )
        return Assessment(
            config=config,
            tree_label=self.tree.label,
            schema_location=config.schema_path,
            scanned=scan.scanned,
            graph=graph,
            violations=tuple(violations),
            externals=tuple(state for state, _ in externals),
            siblings=tuple(state for state, _ in siblings),
            siblings_located=located,
            notices=tuple(notices),
        )

    def thread(self, item_id: str) -> Assessment:
        """The assessment, once `item_id` is known to be something this run can see.

        Raises
        ------
        CouldNotJudge
            For an ID nothing here declares or cites. Where a sibling could not be read, it says
            so rather than claim the item does not exist.
        """
        assessment = self.assessment()
        if assessment.graph.node(item_id) is not None:
            return assessment
        unread = [s.name for s in assessment.siblings if s.declares is None]
        beyond = ""
        if not assessment.siblings_located:
            beyond = ", and the project's other repos could not be located"
        elif unread:
            beyond = f", and sibling {', '.join(unread)} could not be read"
        near = assessment.graph.closest(item_id)
        hint = f"the closest here: {', '.join(near)}; " if near else ""
        raise CouldNotJudge(
            f"{item_id} is not an item this run can see — nothing here declares or cites it"
            f"{beyond}.",
            f"Fix: check the ID — {hint}`qmstrace status` lists this repo's requirements.",
        )

    def _siblings(
        self, ledger: Path | None
    ) -> tuple[list[tuple[SiblingState, dict[str, Item] | None]], bool, bool]:
        """Each sibling with its items (None when not read); whether the siblings could be
        located at all; whether this repo is among the project's repos."""
        if ledger is None:
            return [], not self.config.repos, False
        found: list[tuple[SiblingState, dict[str, Item] | None]] = []
        listed = False
        for name, relative in sorted(self.config.repos.items()):
            path = ledger / relative
            location = _shown(self.root, path)
            if _same(path, self.root):
                listed = True
                continue
            if not (path / CONFIG_FILE).is_file():
                found.append((SiblingState(name, location, None, "not reachable"), None))
                continue
            try:
                tree = self.trees(path)
                config = _configuration(path, tree)
            except CouldNotJudge as stopped:
                problem = f"its configuration could not be read — {stopped.what}"
                found.append((SiblingState(name, location, None, problem), None))
                continue
            authored = [t for t in config.item_types.values() if t.id_pattern is not None]
            scan = _scan(tree, config, authored, with_misplaced=False)
            # a sibling's files, as a reader of this repo would write them: ../service/docs/…
            items = {
                i.id: replace(i, file=posixpath.join(location, i.file))
                for part in scan.extracted
                for i in part.items
            }
            counts = Counter(item.type for item in items.values())
            declares = {t.name: counts[t.name] for t in authored if counts[t.name]}
            found.append((SiblingState(name, location, declares), items))
        return found, True, listed


# ── finding and reading the repo ────────────────────────────────────────────────────────────


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
                "them), or point at one with -C <path>.",
            )
    raise CouldNotJudge(
        f"there is no {CONFIG_FILE} in {here} or any folder above it, so this is not a traced "
        "product repo.",
        "Fix: run qmstrace inside a product repo, or point at one with -C <path>.",
    )


def _configuration(root: Path, tree: ISourceTree) -> TraceConfig:
    try:
        local = tree.read(CONFIG_FILE)
    except UnicodeDecodeError:
        raise CouldNotJudge(
            f"{CONFIG_FILE} in {root} is not UTF-8 text.", "Fix: save it as UTF-8."
        ) from None
    reference = TraceConfig.schema_reference(local)
    schema = _read(root / reference) if reference else None
    return TraceConfig.parse(local, schema)


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None


# ── the one scan function ───────────────────────────────────────────────────────────────────


def _scan(
    tree: ISourceTree, config: TraceConfig, types: Iterable[ItemType], *, with_misplaced: bool
) -> _Scan:
    files = tree.files()
    texts: dict[str, str | None] = {}
    unreadable: list[Finding] = []

    def text_of(path: str) -> str | None:
        if path not in texts:
            try:
                texts[path] = tree.read(path)
            except UnicodeDecodeError:
                texts[path] = None
                unreadable.append(findings.cannot_read(path))
        return texts[path]

    extracted: list[Extracted] = []
    scanned: list[Scanned] = []
    read_for: dict[str, set[str]] = {}
    for item_type in sorted(types, key=lambda t: t.name):
        if not item_type.declared_here or item_type.extractor is None:
            continue
        selected = [p for p in files if matches(p, item_type.files)]
        ignored = {p for p in selected if matches(p, item_type.ignore)}
        chosen = [p for p in selected if p not in ignored]
        read_for[item_type.name] = set(selected)
        extract = REGISTRY[item_type.extractor]
        before = len(extracted)
        for path in chosen:
            text = text_of(path)
            if text is not None:
                extracted.append(extract(path, text, item_type, config))
        items = sum(len(part.items) for part in extracted[before:])
        scanned.append(
            Scanned(
                item_type.name, item_type.files, item_type.ignore, len(chosen), items, len(ignored)
            )
        )

    misplaced: list[Item] = []
    if with_misplaced:
        documents = [p for p in files if matches(p, _MARKDOWN)]
        for item_type in (t for t in config.item_types.values() if t.extractor == "markdown"):
            if item_type.name not in read_for:
                continue
            for path in (p for p in documents if p not in read_for[item_type.name]):
                text = text_of(path)
                if text is not None:
                    misplaced += REGISTRY["markdown"](path, text, item_type, config).items
    extracted.append(Extracted(findings=tuple(unreadable)))
    return _Scan(tuple(extracted), tuple(scanned), tuple(misplaced))


# ── what lies around the repo ───────────────────────────────────────────────────────────────


def _ledger(root: Path, config: TraceConfig) -> Path | None:
    """Where the agreement and the project's other repos are looked for."""
    if config.schema_form is SchemaForm.OWN:
        return root
    return root / config.ledger if config.ledger else None


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


def _shown(root: Path, path: Path) -> str:
    """A path as a reader of this repo would write it — relative, and never resolved, so a
    temporary folder's real location never leaks into the output."""
    return posixpath.normpath(Path(os.path.relpath(path, root)).as_posix())


def _same(one: Path, other: Path) -> bool:
    """Whether two paths name one folder — by their text first, since in a pipeline the ledger
    they are written through may not exist; then on disk, which also sees through links."""
    if os.path.normpath(os.path.abspath(one)) == os.path.normpath(os.path.abspath(other)):
        return True
    try:
        return os.path.samefile(one, other)
    except OSError:
        return False
