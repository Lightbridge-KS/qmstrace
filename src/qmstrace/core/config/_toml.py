"""Strict TOML reading with file/key diagnostics and unknown-key rejection.

Implements: DSN-QMT-03
"""

from __future__ import annotations

import re
import tomllib
from collections.abc import Mapping
from typing import Final, cast

from qmstrace.core.errors import CouldNotJudge

SUPPORTED_VERSION: Final = 1

_FIX_UNKNOWN: Final = (
    "Fix: correct or remove the key — an unknown key is an error because a mistyped one "
    "would be a rule nobody can see."
)


def _load(text: str, name: str) -> dict[str, object]:
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as broken:
        raise CouldNotJudge(
            f"{name} is not valid TOML: {broken}.", "Fix: correct the file's syntax."
        ) from None


class _Table:
    """A TOML table that knows where it is, and refuses keys nobody read."""

    def __init__(
        self,
        raw: Mapping[str, object],
        where: str,
        file: str,
        *,
        skip: frozenset[str] = frozenset(),
    ) -> None:
        self.raw = raw
        self.where = where
        self.file = file
        self._read: set[str] = set(skip)

    def _at(self, key: str) -> str:
        return f"{self.where}.{key}" if self.where else key

    def _wrong(self, key: str, wanted: str) -> CouldNotJudge:
        return CouldNotJudge(
            f"{self.file}: '{self._at(key)}' must be {wanted}.", "Fix: correct its value."
        )

    def _get(self, key: str) -> object | None:
        self._read.add(key)
        return self.raw.get(key)

    def text(self, key: str) -> str:
        value = self.opt_text(key)
        if value is None:
            raise CouldNotJudge(
                f"{self.file}: '{self._at(key)}' is missing.", "Fix: add it — it is required."
            )
        return value

    def opt_text(self, key: str) -> str | None:
        value = self._get(key)
        if value is None:
            return None
        if not isinstance(value, str) or not value:
            raise self._wrong(key, "a non-empty string")
        return value

    def whole(self, key: str) -> int | None:
        value = self._get(key)
        if value is None:
            return None
        if not isinstance(value, int) or isinstance(value, bool):
            raise self._wrong(key, "a whole number")
        return value

    def flag(self, key: str, *, default: bool) -> bool:
        value = self._get(key)
        if value is None:
            return default
        if not isinstance(value, bool):
            raise self._wrong(key, "true or false")
        return value

    def texts(self, key: str) -> tuple[str, ...]:
        value = self._get(key)
        if value is None:
            return ()
        if not isinstance(value, list) or not all(isinstance(v, str) and v for v in value):
            raise self._wrong(key, "a list of non-empty strings")
        return tuple(cast(list[str], value))

    def pattern(self, key: str) -> re.Pattern[str] | None:
        source = self.opt_text(key)
        if source is None:
            return None
        try:
            return re.compile(source)
        except re.error as broken:
            raise self._wrong(key, f"a valid regular expression ({broken})") from None

    def table(self, key: str, *, required: bool = False) -> _Table:
        value = self._get(key)
        if value is None:
            if required:
                raise CouldNotJudge(
                    f"{self.file}: the [{self._at(key)}] table is missing.",
                    "Fix: add it — see the annotated example in the project's documentation.",
                )
            value = {}
        if not isinstance(value, dict):
            raise self._wrong(key, "a table")
        return _Table(cast(dict[str, object], value), self._at(key), self.file)

    def tables(self, key: str) -> dict[str, _Table]:
        """A table of tables: `[links]` holding one table per marker."""
        outer = self.table(key)
        found = {name: outer.table(name) for name in outer.raw}
        outer.done()
        return found

    def array(self, key: str) -> list[_Table]:
        value = self._get(key)
        if value is None:
            return []
        if not isinstance(value, list) or not all(isinstance(v, dict) for v in value):
            raise self._wrong(key, "an array of tables")
        rows = cast(list[dict[str, object]], value)
        return [_Table(row, f"{self._at(key)}[{i}]", self.file) for i, row in enumerate(rows)]

    def remaining(self) -> list[str]:
        return sorted(set(self.raw) - self._read)

    def consume_all(self) -> None:
        self._read |= set(self.raw)

    def done(self) -> None:
        """Every key must have been read by now."""
        unknown = self.remaining()
        if unknown:
            known = ", ".join(sorted(self._read)) or "none"
            raise CouldNotJudge(
                f"{self.file}: unknown key '{self._at(unknown[0])}' (known here: {known}).",
                _FIX_UNKNOWN,
            )


def _version(table: _Table) -> None:
    version = table.whole("version")
    if version != SUPPORTED_VERSION:
        raise CouldNotJudge(
            f"{table.file}: 'version' is {version!r}; this qmstrace reads version "
            f"{SUPPORTED_VERSION}.",
            "Fix: set version = 1, or use the qmstrace that matches the file.",
        )
