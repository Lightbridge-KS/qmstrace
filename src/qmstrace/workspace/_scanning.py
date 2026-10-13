"""One scan for working trees, siblings and immutable historical trees.

Implements: DSN-QMT-02
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final

from qmstrace.core import findings
from qmstrace.core.assessment import Scanned
from qmstrace.core.config import ItemType, TraceConfig
from qmstrace.core.model import Extracted, Finding, Item
from qmstrace.extract.base import REGISTRY
from qmstrace.infra.globbing import matches
from qmstrace.infra.tree import ISourceTree

_MARKDOWN: Final = ("*.md", "**/*.md", "*.qmd", "**/*.qmd")


@dataclass(frozen=True, slots=True)
class _Scan:
    """What one scan of one tree found."""

    extracted: tuple[Extracted, ...]
    scanned: tuple[Scanned, ...]
    misplaced: tuple[Item, ...]


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
