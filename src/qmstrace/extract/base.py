"""The extractor seam: text in, items out — never a path to open, never a repo.

An extractor is chosen by the name a trace configuration gives an item type, never by the
type's own name, so a second trace schema needs no engine change. It takes a file's text, so
the same extractor reads the working tree, a tree at a baseline tag and a sibling. A problem
in the text is a finding in what it returns; an extractor never raises for the user's repo.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final, Protocol

from qmstrace.core.config import ItemType, TraceConfig
from qmstrace.core.model import Extracted
from qmstrace.extract import markdown, pytest_tests, python_module


class IExtractor(Protocol):
    """Read one file's text for items of one type."""

    def __call__(
        self, path: str, text: str, item_type: ItemType, config: TraceConfig
    ) -> Extracted: ...


REGISTRY: Final[Mapping[str, IExtractor]] = {
    "markdown": markdown.extract,
    "python-module": python_module.extract,
    "pytest": pytest_tests.extract,
}
