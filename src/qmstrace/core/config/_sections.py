"""Read the schema and local declaration sections, preserving authored order.

Implements: DSN-QMT-03
"""

from __future__ import annotations

import re
from typing import Final

from qmstrace.core.config._prefix import common_prefix
from qmstrace.core.config._schema import (
    EXTRACTORS,
    BaselineScope,
    ChangeRequests,
    CoverageRule,
    ExternalSource,
    ItemType,
    LinkType,
    Subject,
    Tables,
)
from qmstrace.core.config._toml import _Table
from qmstrace.core.errors import CouldNotJudge

_GLOB: Final = set("*?[")  # what makes a path a pattern
# Any start of the one shape every ID has (`model.ID_TOKEN`): capitals and digits in
# hyphen-joined segments, a number with dotted parts. A pattern or prefix that starts otherwise
# can never match an ID.
_ID_START: Final = re.compile(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]*(?:\.\d*)*)*")
_ID_SHAPE: Final = (
    "an ID is capital letters and digits in hyphen-joined segments, ending in a number that "
    "may carry dotted parts, such as REQ-SVC-01 or TC-SVC-04.1-01"
)


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


def _id_start(start: str, what: str, fix: str) -> None:
    """Refuse a pattern or prefix that no ID can start with — it would match nothing, silently."""
    if not _ID_START.fullmatch(start):
        raise CouldNotJudge(
            f"{what} starts with '{start}', which no ID can start with — {_ID_SHAPE}.", fix
        )


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
            extractor = _extractor(here, name)
            pattern = here.pattern("id_pattern")
            prefix = here.opt_text("id_prefix")
            files, ignore = here.texts("files"), here.texts("ignore")
            if not files:
                raise CouldNotJudge(
                    f"{here.file}: [items.{name}] names no files to scan.",
                    'Fix: add files = ["…"] — one or more glob patterns.',
                )
            if EXTRACTORS[extractor] and pattern is None:
                raise CouldNotJudge(
                    f"{here.file}: [items.{name}] is read by '{extractor}', which reads IDs "
                    "someone wrote, but gives no id_pattern.",
                    "Fix: add id_pattern = '^…$' — what an ID of this type looks like.",
                )
            if not EXTRACTORS[extractor] and (pattern is not None or prefix is not None):
                raise CouldNotJudge(
                    f"{here.file}: [items.{name}] is read by '{extractor}', which derives each "
                    "ID from where the item is — an ID pattern would never be applied.",
                    "Fix: remove id_pattern and id_prefix from this table.",
                )
            if pattern is not None:
                start = common_prefix(pattern)
                if not start:
                    raise CouldNotJudge(
                        f"{here.file}: the ID pattern of [items.{name}] has no provable "
                        "common literal start shared by every branch; id_prefix cannot make "
                        "an unproved start safe.",
                        "Fix: write one ID-shaped literal start common to every branch, or "
                        "use separate item types for separate ID families.",
                    )
                _id_start(
                    start,
                    f"{here.file}: the ID pattern of [items.{name}]",
                    "Fix: write the pattern in that shape, e.g. "
                    r"id_pattern = '^REQ-SVC-\d{2}$'.",
                )
                if prefix is None:
                    prefix = start
                else:
                    _id_start(
                        prefix,
                        f"{here.file}: the id_prefix of [items.{name}]",
                        'Fix: write the prefix in that shape, e.g. id_prefix = "REQ-".',
                    )
                    if not start.startswith(prefix):
                        raise CouldNotJudge(
                            f"{here.file}: the id_prefix '{prefix}' of [items.{name}] "
                            f"does not cover every ID in its pattern (proved common start: "
                            f"'{start}').",
                            "Fix: use a prefix of the proved common start, or rewrite the "
                            "pattern so every branch shares the intended prefix.",
                        )
            here.done()
        found[name] = ItemType(
            name, required, values, levels, extractor, pattern, prefix, files, ignore
        )
    return found


def _extractor(here: _Table, name: str) -> str:
    extractor = here.text("extractor")
    if extractor not in EXTRACTORS:
        raise CouldNotJudge(
            f"{here.file}: [items.{name}] names the extractor '{extractor}', which this "
            f"qmstrace does not have (it has: {', '.join(EXTRACTORS)}).",
            "Fix: use one of those.",
        )
    return extractor


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
        prefix = table.text("prefix")
        _id_start(
            prefix,
            f"{table.file}: 'externals.{name}.prefix'",
            'Fix: write the prefix in that shape, e.g. prefix = "AGR-".',
        )
        source = table.text("source")
        # One file: a pattern would read as a file that is not there — every citation of the
        # family then passing as *not verified*, without a word.
        if _GLOB & set(source):
            raise CouldNotJudge(
                f"{table.file}: 'externals.{name}.source' is '{source}', a pattern — an "
                "external reads one file.",
                'Fix: name one file, e.g. source = "eng1/agreement.md"; an ID family kept in '
                "several files takes one [externals.*] table per file, each with its own prefix.",
            )
        # A citation goes to the first external its ID starts with, so no prefix may start
        # another: the second table's clauses would be judged against the first table's file.
        for other in found.values():
            (short_name, short), (long_name, long) = sorted(
                ((other.name, other.prefix), (name, prefix)), key=lambda pair: len(pair[1])
            )
            if not long.startswith(short):
                continue
            if short == long:
                what = (
                    f"[externals.{other.name}] and [externals.{name}] have the same prefix, "
                    f"'{short}'"
                )
            else:
                what = (
                    f"the prefix of [externals.{long_name}], '{long}', starts with that of "
                    f"[externals.{short_name}], '{short}'"
                )
            raise CouldNotJudge(
                f"{table.file}: {what}, so a citation of {long}… could be judged against "
                "the wrong file.",
                "Fix: give each external a prefix no other external's starts with — "
                f"engagement-qualified, such as '{short}E1-' and '{short}E2-'.",
            )
        found[name] = ExternalSource(name, table.text("item_type"), prefix, source, declared_as)
        table.done()
    return found


def _change_requests(schema: _Table) -> ChangeRequests | None:
    table = schema.table("change_requests")
    if not table.raw:
        return None
    prefix = table.text("prefix")
    _id_start(
        prefix,
        f"{table.file}: 'change_requests.prefix'",
        'Fix: write the prefix in that shape, e.g. prefix = "CR-".',
    )
    found = ChangeRequests(prefix, table.text("source"), table.text("accepted"))
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


def _tables(schema: _Table) -> Tables:
    """`[tables.matrix]` — the requirement fields the traceability matrix carries, and the
    test-case field that names a level (ADR-0005)."""
    tables = schema.table("tables")
    matrix = tables.table("matrix")
    found = Tables(matrix.texts("fields"), matrix.opt_text("level"))
    matrix.done()
    tables.done()
    return found


def _repos(schema: _Table, version: int = 1) -> tuple[dict[str, str], str | None]:
    table = schema.table("repos")
    if version == 1:
        found = {name: table.text(name) for name in table.raw}
        ledger = None
    else:
        ledger = table.text("ledger_repo")
        names = table.texts("members")
        if not names or len(set(names)) != len(names):
            raise CouldNotJudge(
                f"{schema.file}: repos.members must contain unique repository names "
                "and cannot be empty.",
                "Fix: list each traced member once; include the ledger role "
                "when it holds documents.",
            )
        for name in (*names, ledger):
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", name) or name in (".", ".."):
                raise CouldNotJudge(
                    f"{schema.file}: invalid repository identity {name!r}.",
                    "Fix: use portable names without path separators, colons or whitespace.",
                )
        # Compatibility mapping: v2 values carry no filesystem defaults. All v2 readers
        # resolve members through a selected map, never by joining these empty values.
        found = dict.fromkeys(sorted(names), "")
    table.done()
    return found, ledger
