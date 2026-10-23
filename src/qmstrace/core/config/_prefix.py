"""Conservatively prove the literal beginning shared by every ID-pattern branch.

Only a small, unambiguous part of Python's regex syntax contributes to the proof. An
unrecognised atom is variable; text after it cannot extend a guaranteed prefix. This is
deliberately a proof of a prefix, not a second regex engine.

Implements: DSN-QMT-03
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class _Start:
    text: str
    fixed: bool  # every match of this expression is exactly `text`


def common_prefix(pattern: re.Pattern[str]) -> str:
    """Return a start that every match has, or empty when it cannot be proved.

    Ignore-case and verbose patterns change the meaning of raw literal characters. An
    unsupported group extension makes the whole proof inconclusive.
    """
    if pattern.flags & (re.IGNORECASE | re.VERBOSE):
        return ""
    proof = _PrefixProof(pattern.pattern)
    start = proof.expression()
    return "" if proof.unsupported else start.text


def _shared(starts: list[_Start]) -> _Start:
    first = starts[0].text
    for other in starts[1:]:
        length = 0
        while length < min(len(first), len(other.text)) and first[length] == other.text[length]:
            length += 1
        first = first[:length]
    return _Start(first, all(start.fixed and start.text == first for start in starts))


class _PrefixProof:
    def __init__(self, source: str) -> None:
        self.source = source
        self.pos = 0
        self.unsupported = False

    def expression(self) -> _Start:
        branches: list[_Start] = []
        while True:
            text = ""
            fixed = True
            while self.pos < len(self.source) and self.source[self.pos] not in ")|":
                atom = self._atom()
                atom = self._quantified(atom)
                if fixed:
                    text += atom.text
                    fixed = atom.fixed
            branches.append(_Start(text, fixed))
            if self.pos >= len(self.source) or self.source[self.pos] == ")":
                return _shared(branches)
            self.pos += 1  # top-level or group alternative

    def _atom(self) -> _Start:
        char = self.source[self.pos]
        self.pos += 1
        if char == "(":
            if self.source.startswith("?:", self.pos):
                self.pos += 2
                inside = self.expression()
                self.pos += 1  # closing parenthesis; regex compilation checked it
                return inside
            if self.pos < len(self.source) and self.source[self.pos] == "?":
                self.unsupported = True
                self._skip_group()
                return _Start("", False)
            inside = self.expression()
            self.pos += 1
            return inside
        if char == "[":
            self._skip_class()
            return _Start("", False)
        if char == "\\":
            escape = self.source[self.pos]
            self.pos += 1
            if escape == "A":
                return _Start("", True)
            if not escape.isalnum():
                return _Start(escape, True)
            return _Start("", False)
        if char == "^":
            return _Start("", True)
        if char in ".${}":
            return _Start("", False)
        return _Start(char, True)

    def _quantified(self, atom: _Start) -> _Start:
        if self.pos >= len(self.source):
            return atom
        char = self.source[self.pos]
        if char in "?*+":
            self.pos += 1
            if self.pos < len(self.source) and self.source[self.pos] in "?+":
                self.pos += 1  # lazy or possessive form
            return _Start("" if char in "?*" else atom.text, False)
        if char != "{":
            return atom
        match = re.match(r"\{(\d+)(?:,(\d*))?\}", self.source[self.pos :])
        if match is None:
            return atom
        self.pos += len(match.group())
        if self.pos < len(self.source) and self.source[self.pos] in "?+":
            self.pos += 1
        minimum = int(match.group(1))
        maximum = match.group(2)
        exact_one = minimum == 1 and maximum is None
        return _Start(atom.text if minimum else "", atom.fixed and exact_one)

    def _skip_class(self) -> None:
        if self.pos < len(self.source) and self.source[self.pos] == "^":
            self.pos += 1
        if self.pos < len(self.source) and self.source[self.pos] == "]":
            self.pos += 1
        while self.pos < len(self.source):
            char = self.source[self.pos]
            self.pos += 1
            if char == "\\":
                self.pos += 1
            elif char == "]":
                return

    def _skip_group(self) -> None:
        depth = 1
        while depth and self.pos < len(self.source):
            char = self.source[self.pos]
            self.pos += 1
            if char == "\\":
                self.pos += 1
            elif char == "[":
                self._skip_class()
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
