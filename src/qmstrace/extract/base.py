"""The extractor seam: text in, items out — never a path to open, never a repo.

An extractor is chosen by the name a trace configuration gives an item type, never by the
type's own name, so a second trace schema needs no engine change. It takes a file's text, so
the same extractor reads the working tree, a tree at a baseline tag and a sibling. A problem
in the text is a finding in what it returns; an extractor never raises for the user's repo.

Implements: DSN-QMT-04
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Final, Protocol

from qmstrace.core.config import ItemType, TraceConfig
from qmstrace.core.model import Extracted
from qmstrace.extract import markdown
from qmstrace.extract.csharp import component as csharp_file
from qmstrace.extract.csharp import xunit
from qmstrace.extract.python import module, pytest_tests


class IExtractor(Protocol):
    """Read one file's text for items of one type."""

    def __call__(
        self, path: str, text: str, item_type: ItemType, config: TraceConfig
    ) -> Extracted: ...


REGISTRY: Final[Mapping[str, IExtractor]] = {
    "markdown": markdown.extract,
    "python-module": module.extract,
    "pytest": pytest_tests.extract,
    "csharp-file": csharp_file.extract,
    "xunit": xunit.extract,
}

# How each extractor's items declare a link — `form(marker, target)`, for a gap's next move. The
# syntax lives with the extractor that reads it, and a test round-trips every form.
FORMS: Final[Mapping[str, Callable[[str, str], str]]] = {
    "markdown": markdown.form,
    "python-module": module.form,
    "pytest": pytest_tests.form,
    "csharp-file": csharp_file.form,
    "xunit": xunit.form,
}
