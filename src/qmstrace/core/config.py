"""The trace configuration and the trace schema, parsed from text. Pure: no file is opened here.

Three levels, three owners. A **profile** is the standard's catalogue. A **trace schema** is one
project's declaration — link types, coverage rules, required fields, where the agreement and
the change requests live, which tags are baselines. A **trace configuration** is one product
repo's own file: what is local to it, plus the project's trace schema in one of three forms —

- *by path*: `[schema] path = "…"`, for repos that sit side by side;
- *a generated, verified copy*: `[schema] digest = "sha256:…"` followed by the schema's
  content, which is never edited by hand and is checked against its digest here;
- *the repo's own*: the schema's content with no digest, for a repo that has no ledger.

An unknown key anywhere is an error: a mistyped `requird` would be a hidden rule.
"""

from __future__ import annotations

import hashlib
import json
import re
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import Final, cast

from qmstrace.core.errors import CouldNotJudge

SUPPORTED_VERSION: Final = 1
_REGEX_META: Final = set("\\()[].*+?{|$")
_FIX_UNKNOWN: Final = (
    "Fix: correct or remove the key — an unknown key is an error because a mistyped one "
    "would be a rule nobody can see."
)


class SchemaForm(Enum):
    """How a product repo holds the project's trace schema."""

    BY_PATH = "by path"
    VERIFIED_COPY = "a generated, verified copy"
    OWN = "the repo's own"


@dataclass(frozen=True, slots=True)
class ItemType:
    """One kind of item: what the project requires of it, and where this repo declares it."""

    name: str
    required: tuple[str, ...]
    values: Mapping[str, tuple[str, ...]]
    levels: tuple[str, ...]
    extractor: str | None
    id_pattern: re.Pattern[str] | None
    id_prefix: str | None
    files: tuple[str, ...]
    ignore: tuple[str, ...]

    @property
    def declared_here(self) -> bool:
        """Whether this repo scans for items of this type at all."""
        return bool(self.files)

    @property
    def fields(self) -> frozenset[str]:
        """Every field name the project declares for this type."""
        return frozenset(self.required) | frozenset(self.values)


@dataclass(frozen=True, slots=True)
class LinkType:
    """A marker, who may carry it, and what it may point at."""

    marker: str
    sources: tuple[str, ...]
    targets: tuple[str, ...]
    counts_for_coverage: bool


@dataclass(frozen=True, slots=True)
class CoverageRule:
    """Which link an item type must have; an unmet rule is a gap."""

    code: str
    item_type: str
    direction: str  # "incoming" | "outgoing"
    marker: str
    where: Mapping[str, str]
    text: str


@dataclass(frozen=True, slots=True)
class ExternalSource:
    """Items declared outside any product repo — cited there, declared in the ledger."""

    name: str
    item_type: str
    prefix: str
    source: str
    declared_as: re.Pattern[str]


@dataclass(frozen=True, slots=True)
class ChangeRequests:
    """Where the project's change requests are, and which state licenses a change."""

    prefix: str
    source: str
    accepted: str


@dataclass(frozen=True, slots=True)
class BaselineScope:
    """Which tags are baselines, and which item types each freezes.

    `subject` is `"*"` for every subject, a subject's name, or `None` when the tag pattern
    itself names the subject through a `(?P<subject>…)` group.
    """

    name: str
    tag: re.Pattern[str]
    covers: tuple[str, ...]
    subject: str | None


@dataclass(frozen=True, slots=True)
class Subject:
    """A named body of requirements, and the key inside its item IDs."""

    name: str
    key: str


@dataclass(frozen=True, slots=True)
class TraceConfig:
    """Everything in force in one product repo: the project's schema and the repo's own part."""

    project: str
    profile: str | None
    ledger: str | None
    schema_form: SchemaForm
    schema_path: str | None
    schema_digest: str
    subjects: Mapping[str, Subject]
    item_types: Mapping[str, ItemType]
    links: Mapping[str, LinkType]
    rules: tuple[CoverageRule, ...]
    externals: Mapping[str, ExternalSource]
    change_requests: ChangeRequests | None
    baselines: Mapping[str, BaselineScope]
    repos: Mapping[str, str]

    @staticmethod
    def schema_reference(local_text: str, *, local_name: str = "qmstrace.toml") -> str | None:
        """The path a trace configuration gives for its schema, or `None` if it carries one.

        The caller reads that file and hands its text to `parse`; nothing is opened here.
        """
        schema = _load(local_text, local_name).get("schema")
        path = schema.get("path") if isinstance(schema, dict) else None
        return path if isinstance(path, str) else None

    @classmethod
    def parse(
        cls,
        local_text: str,
        schema_text: str | None = None,
        *,
        local_name: str = "qmstrace.toml",
        schema_name: str = "qmstrace.schema.toml",
    ) -> TraceConfig:
        """Validate and merge a repo's trace configuration with the project's trace schema.

        Parameters
        ----------
        local_text
            The repo's `qmstrace.toml`.
        schema_text
            The project's trace schema, when the configuration refers to it by path.

        Raises
        ------
        CouldNotJudge
            For any configuration that cannot be trusted: an unknown key, a wrong type, an
            edited copy, a rule that needs a link which counts toward no coverage. The
            message names the file and the key, and says what to do.

        Examples
        --------
        ```python
        path = TraceConfig.schema_reference(local_text)       # "../ledger/qmstrace.schema.toml"
        config = TraceConfig.parse(local_text, schema_text)
        config.item_types["requirement"].required              # ('Category', 'Origin', 'Verify-by')
        ```
        """
        local = _Table(_load(local_text, local_name), "", local_name)
        _version(local)
        ledger = local.opt_text("ledger")

        holder = local.table("schema", required=True)
        path = holder.opt_text("path")
        digest = holder.opt_text("digest")
        if path is not None:
            if digest is not None or holder.remaining():
                raise CouldNotJudge(
                    f"{local_name}: [schema] gives a path and also carries a digest or content.",
                    "Fix: a [schema] table is either a path to the project's trace schema or "
                    "a copy of it — never both.",
                )
            if schema_text is None:
                raise CouldNotJudge(
                    f"{local_name}: the project's trace schema at '{path}' could not be read.",
                    "Fix: check the project's ledger repo out where that path points, or ask "
                    "the project side for a generated copy of the schema.",
                )
            schema = _Table(_load(schema_text, schema_name), "", schema_name)
            form, stated = SchemaForm.BY_PATH, schema_digest(schema.raw)
        else:
            schema = _Table(holder.raw, "schema", local_name, skip=frozenset({"digest"}))
            stated = schema_digest(holder.raw)
            form = SchemaForm.OWN
            if digest is not None:
                form = SchemaForm.VERIFIED_COPY
                if digest != stated:
                    raise CouldNotJudge(
                        f"{local_name}: the copy of the project's trace schema under [schema] "
                        f"no longer matches its digest — it was edited by hand.",
                        "Fix: restore the generated block; to change a rule, tell the project "
                        "side and have the copy generated again.",
                    )
            holder.consume_all()

        _version(schema)
        config = cls(
            project=schema.text("project"),
            profile=schema.opt_text("profile"),
            ledger=ledger,
            schema_form=form,
            schema_path=path,
            schema_digest=stated,
            subjects=_subjects(local),
            item_types=_item_types(schema, local),
            links=_links(schema),
            rules=_rules(schema),
            externals=_externals(schema),
            change_requests=_change_requests(schema),
            baselines=_baselines(schema),
            repos=_repos(schema),
        )
        schema.done()
        local.done()
        _cross_check(config, schema.file)
        return config


def schema_digest(schema: Mapping[str, object]) -> str:
    """The digest of a trace schema's content — independent of key order, comments and layout.

    `digest` and `path` are not part of the content, so the same function serves the ledger's
    file and a product repo's copy of it.
    """
    content = {k: v for k, v in schema.items() if k not in {"digest", "path"}}
    canonical = json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ── reading TOML, strictly ──────────────────────────────────────────────────────────────────


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


# ── the parts ───────────────────────────────────────────────────────────────────────────────


def _subjects(local: _Table) -> dict[str, Subject]:
    found: dict[str, Subject] = {}
    for name, table in local.tables("subjects").items():
        key = table.text("key")
        if not re.fullmatch(r"[A-Z][A-Z0-9]*", key):
            raise CouldNotJudge(
                f"{table.file}: subject '{name}' has key '{key}'.",
                "Fix: a subject's key is capital letters and digits — it appears inside item "
                "IDs, as in REQ-SVC-01.",
            )
        table.done()
        found[name] = Subject(name, key)
    return found


def _literal_prefix(pattern: str) -> str:
    """The literal text an ID pattern starts with: `^REQ-SVC-\\d{2}$` → `REQ-SVC-`."""
    literal = []
    for char in pattern.removeprefix("^"):
        if char in _REGEX_META:
            break
        literal.append(char)
    return "".join(literal)


def _item_types(schema: _Table, local: _Table) -> dict[str, ItemType]:
    declared = schema.tables("item_types")
    locals_ = local.tables("items")
    for name, table in locals_.items():
        if name not in declared:
            raise CouldNotJudge(
                f"{table.file}: [items.{name}] is not an item type the project knows "
                f"(it knows: {', '.join(declared) or 'none'}).",
                "Fix: use one of those, or ask the project side to add the type to the schema.",
            )
    found: dict[str, ItemType] = {}
    for name, table in declared.items():
        values_table = table.table("values")
        values = {key: values_table.texts(key) for key in values_table.raw}
        values_table.done()
        required, levels = table.texts("required"), table.texts("levels")
        table.done()

        here = locals_.get(name)
        extractor: str | None = None
        pattern: re.Pattern[str] | None = None
        prefix: str | None = None
        files: tuple[str, ...] = ()
        ignore: tuple[str, ...] = ()
        if here is not None:
            extractor = here.text("extractor")
            pattern = here.pattern("id_pattern")
            prefix = here.opt_text("id_prefix")
            files, ignore = here.texts("files"), here.texts("ignore")
            if not files:
                raise CouldNotJudge(
                    f"{here.file}: [items.{name}] names no files to scan.",
                    'Fix: add files = ["…"] — one or more glob patterns.',
                )
            if pattern is not None and prefix is None:
                prefix = _literal_prefix(pattern.pattern)
                if not prefix:
                    raise CouldNotJudge(
                        f"{here.file}: the ID pattern of [items.{name}] starts with no literal "
                        "text, so a malformed ID cannot be told from prose.",
                        'Fix: add id_prefix = "…" — the text every ID of this type starts with.',
                    )
            here.done()
        found[name] = ItemType(
            name, required, values, levels, extractor, pattern, prefix, files, ignore
        )
    return found


def _links(schema: _Table) -> dict[str, LinkType]:
    found: dict[str, LinkType] = {}
    for marker, table in schema.tables("links").items():
        found[marker] = LinkType(
            marker,
            table.texts("from"),
            table.texts("to"),
            table.flag("coverage", default=True),
        )
        table.done()
    return found


def _rules(schema: _Table) -> tuple[CoverageRule, ...]:
    found: list[CoverageRule] = []
    for table in schema.array("rules"):
        code, needs = table.text("code"), table.text("needs")
        direction, _, marker = needs.partition(":")
        if direction not in {"incoming", "outgoing"} or not marker:
            raise CouldNotJudge(
                f"{table.file}: rule {code} has needs = '{needs}'.",
                'Fix: write "incoming:<marker>" or "outgoing:<marker>".',
            )
        where_table = table.table("where")
        where = {key: where_table.text(key) for key in where_table.raw}
        found.append(
            CoverageRule(code, table.text("item"), direction, marker, where, table.text("text"))
        )
        table.done()
    return tuple(found)


def _externals(schema: _Table) -> dict[str, ExternalSource]:
    found: dict[str, ExternalSource] = {}
    for name, table in schema.tables("externals").items():
        declared_as = table.pattern("declared_as")
        if declared_as is None or declared_as.groups != 1:
            raise CouldNotJudge(
                f"{table.file}: 'externals.{name}.declared_as' must be a regular expression "
                "with exactly one group — the ID.",
                "Fix: put the ID, and nothing else, in parentheses.",
            )
        found[name] = ExternalSource(
            name, table.text("item_type"), table.text("prefix"), table.text("source"), declared_as
        )
        table.done()
    return found


def _change_requests(schema: _Table) -> ChangeRequests | None:
    table = schema.table("change_requests")
    if not table.raw:
        return None
    found = ChangeRequests(table.text("prefix"), table.text("source"), table.text("accepted"))
    table.done()
    return found


def _baselines(schema: _Table) -> dict[str, BaselineScope]:
    found: dict[str, BaselineScope] = {}
    for name, table in schema.tables("baselines").items():
        tag = table.pattern("tag")
        if tag is None:
            raise CouldNotJudge(
                f"{table.file}: 'baselines.{name}.tag' is missing.",
                "Fix: give the pattern of the tags this project already cuts as that baseline.",
            )
        subject = table.opt_text("subject")
        if subject is None and "subject" not in tag.groupindex:
            raise CouldNotJudge(
                f"{table.file}: baseline '{name}' does not say which subject it freezes.",
                "Fix: name the subject in the tag pattern with (?P<subject>…), or set "
                'subject = "*" for a baseline — such as a release — that freezes them all.',
            )
        found[name] = BaselineScope(name, tag, table.texts("covers"), subject)
        table.done()
    return found


def _repos(schema: _Table) -> dict[str, str]:
    table = schema.table("repos")
    found = {name: table.text(name) for name in table.raw}
    table.done()
    return found


# ── the parts, against each other ───────────────────────────────────────────────────────────


def _cross_check(config: TraceConfig, schema_file: str) -> None:
    item_types = set(config.item_types)
    known = item_types | {external.item_type for external in config.externals.values()}

    def unknown_type(where: str, name: str) -> CouldNotJudge:
        return CouldNotJudge(
            f"{schema_file}: {where} names '{name}', which is not an item type "
            f"(known: {', '.join(sorted(known))}).",
            "Fix: correct the name, or declare the item type.",
        )

    for link in config.links.values():
        for name in (*link.sources, *link.targets):
            if name not in known:
                raise unknown_type(f"link '{link.marker}'", name)

    codes: set[str] = set()
    for rule in config.rules:
        if not re.fullmatch(r"G\d{2}", rule.code) or rule.code in codes:
            raise CouldNotJudge(
                f"{schema_file}: rule code '{rule.code}' is malformed or used twice.",
                "Fix: give every coverage rule its own code, G followed by two digits.",
            )
        codes.add(rule.code)
        if rule.item_type not in item_types:
            raise unknown_type(f"rule {rule.code}", rule.item_type)
        link_type = config.links.get(rule.marker)
        if link_type is None:
            raise CouldNotJudge(
                f"{schema_file}: rule {rule.code} needs the link '{rule.marker}', which the "
                f"schema does not declare (it declares: {', '.join(config.links)}).",
                "Fix: correct the marker's name.",
            )
        if not link_type.counts_for_coverage:
            raise CouldNotJudge(
                f"{schema_file}: rule {rule.code} needs '{rule.marker}', a link that counts "
                "toward no coverage.",
                "Fix: remove the rule — such a link carries suspicion and impact only.",
            )
        item_type = config.item_types[rule.item_type]
        for key, value in rule.where.items():
            allowed = item_type.values.get(key)
            if key not in item_type.fields or (allowed is not None and value not in allowed):
                raise CouldNotJudge(
                    f"{schema_file}: rule {rule.code} narrows by {key} = '{value}', which "
                    f"'{rule.item_type}' does not declare.",
                    "Fix: use a field and a value the item type lists.",
                )

    for scope in config.baselines.values():
        for name in scope.covers:
            if name not in item_types:
                raise unknown_type(f"baseline '{scope.name}'", name)
