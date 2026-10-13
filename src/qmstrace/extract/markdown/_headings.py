"""Heading syntax, normalized titles and item-shaped section boundaries.

Implements: DSN-QMT-04
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from qmstrace.core.config import ItemType
from qmstrace.core.model import ID_TOKEN

_HEADING: Final = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_LEADING_ID: Final = re.compile(rf"({ID_TOKEN.pattern})(?![A-Za-z0-9-])\s*(.*)$")
_SEPARATOR: Final = re.compile(r"^[\s\u2014\u2013:-]+")  # em dash, en dash, colon, hyphen
_ATTRIBUTE: Final = re.compile(r"\s*\{[#.-][^{}]*\}\s*$")  # Pandoc: {#id}, {.class}, {-}
_NUMBER: Final = re.compile(r"(?:\u00a7\s*)?(\d+(?:\.\d+)*)\.?\s+")  # 4.2, 4.2.1., § 4.2
_WRAPS: Final = ("**", "__", "`", "*", "_")  # longest first: `**` before `*`


@dataclass(frozen=True, slots=True)
class _Heading:
    """One heading line, read: its level, its words, and the ID it starts with, if any."""

    level: int
    text: str  # the words, without the `#` marks and a trailing attribute
    number: str | None  # a leading section number, `4.2`
    bare: str  # the words without that number
    token: str | None  # the ID the heading starts with
    title: str  # the words after that ID and its separator

    def in_item(self, number: str | None) -> str:
        """The words this heading adds to an item's text: its number only when it is not a
        continuation of the item's own — `4.2.1` under `4.2` is layout, `404` is text."""
        if self.number and number and self.number.startswith(number + "."):
            return self.bare
        return self.text


def _heading(raw: str) -> _Heading | None:
    """A heading line, read — or `None` for any other line."""
    found = _HEADING.match(raw)
    if found is None:
        return None
    level, words = len(found.group(1)), _ATTRIBUTE.sub("", found.group(2))
    numbered = _NUMBER.match(words)
    number, bare = (numbered.group(1), words[numbered.end() :]) if numbered else (None, words)
    token, title = _leading_id(bare)
    return _Heading(level, words, number, bare, token, title if token else words)


def _leading_id(words: str) -> tuple[str | None, str]:
    """The ID a heading's words start with — bare, or wrapped in emphasis or backticks that
    close right after it or at the end of the heading — and the title after it."""
    for wrap in _WRAPS:
        if not words.startswith(wrap):
            continue
        inner = words[len(wrap) :]
        lead = _LEADING_ID.match(inner)
        if lead is None:
            continue
        after = inner[lead.end(1) :]
        if after.startswith(wrap):
            after = after[len(wrap) :]
        elif after.endswith(wrap):
            after = after[: -len(wrap)]
        else:
            continue
        return lead.group(1), _SEPARATOR.sub("", after).rstrip()
    lead = _LEADING_ID.match(words)
    if lead is None:
        return None, words
    return lead.group(1), _SEPARATOR.sub("", lead.group(2))


def _item_shaped(token: str, patterned: list[ItemType]) -> bool:
    """Whether an ID is one of this repo's kinds: its pattern, or the prefix it starts with."""
    stem = token.split("-", 1)[0]
    for item_type in patterned:
        pattern, prefix = item_type.id_pattern, item_type.id_prefix or ""
        if (pattern is not None and pattern.fullmatch(token)) or (
            prefix and (token.startswith(prefix) or stem == prefix.split("-", 1)[0])
        ):
            return True
    return False
