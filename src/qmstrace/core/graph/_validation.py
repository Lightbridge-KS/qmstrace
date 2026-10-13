"""Schema admission: resolve link targets and report refused declarations.

Implements: DSN-QMT-05, DSN-QMT-14
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping

from qmstrace.core import findings
from qmstrace.core.config import ItemType, TraceConfig
from qmstrace.core.graph._nodes import Home, Node, Surroundings
from qmstrace.core.model import Finding, Item, Lead, Link, Mention


def _resolve(
    config: TraceConfig,
    around: Surroundings,
    nodes: Mapping[str, Node],
    foreign: Mapping[str, tuple[str, str]],
    link: Link,
) -> tuple[Node | None, Finding | None]:
    """The node a link points at, or the finding that keeps the link out."""
    link_type = config.links[link.marker]
    source_type = nodes[link.src].type or ""
    if source_type not in link_type.sources:
        return None, findings.wrong_carrier(link, source_type, link_type.sources)

    target: Node
    if link.dst in nodes and nodes[link.dst].home in (Home.LOCAL, Home.SIBLING):
        target = nodes[link.dst]
    elif external := next(
        (e for e in config.externals.values() if link.dst.startswith(e.prefix)), None
    ):
        declared = around.externals.get(external.name)
        if declared is not None and link.dst not in declared:
            listing = sorted(declared, key=_numbered)
            return None, findings.undeclared_external(link, external.name, listing)
        target = nodes.get(link.dst) or Node(
            link.dst, Home.EXTERNAL, external.item_type, repo=external.name
        )
    else:
        own = _own_type(config, link.dst)
        if own is not None or around.every_sibling_read:
            home = ", ".join(own.files) if own is not None else None
            return None, findings.no_such_item(
                link,
                home=home,
                siblings_read=bool(config.repos) and around.every_sibling_read,
                whole_project=around.whole_project,
            )
        return Node(link.dst, Home.UNVERIFIED, None), None

    if target.type not in link_type.targets:
        return None, findings.wrong_target(link, target.type or "?", link_type.targets)
    return target, None


def _own_type(config: TraceConfig, item_id: str) -> ItemType | None:
    """The type this repo would declare an ID as, if it matches one of its own patterns."""
    return next(
        (
            t
            for t in config.item_types.values()
            if t.id_pattern is not None and t.declared_here and t.id_pattern.fullmatch(item_id)
        ),
        None,
    )


def _fields(config: TraceConfig, items: Iterable[Item]) -> list[Finding]:
    """V05 — required fields, and values from their lists, spelled exactly."""
    wrong: list[Finding] = []
    for item in items:
        item_type = config.item_types[item.type]
        for key in item_type.required:
            if key not in item.fields:
                wrong.append(findings.missing_field(item, key, item_type.values.get(key, ())))
        for key, allowed in item_type.values.items():
            value = item.fields.get(key)
            if value is not None and value not in allowed:
                wrong.append(findings.value_not_allowed(item, key, value, allowed))
    return wrong


def _leads(
    config: TraceConfig, leads: Iterable[Lead], foreign: Mapping[str, tuple[str, str]]
) -> list[Finding]:
    """Judge headings that start with an ID but declared nothing.

    A sibling's item declared again is V01; an ID of this type's kind that fails the pattern is
    V02. An ID matching another of this repo's types is left to V07; anything else is prose.
    """
    wrong: list[Finding] = []
    for lead in leads:
        item_type = config.item_types[lead.item_type]
        prefix = item_type.id_prefix or ""
        if lead.token in foreign:
            repo = foreign[lead.token][0]
            wrong.append(findings.declared_in_sibling(lead.token, repo, lead.file, lead.line))
        elif _own_type(config, lead.token) is not None:
            continue
        elif prefix and (lead.token.startswith(prefix) or _stem(lead.token) == _stem(prefix)):
            pattern = item_type.id_pattern.pattern if item_type.id_pattern else prefix
            wrong.append(
                findings.malformed_id(lead.token, lead.item_type, pattern, lead.file, lead.line)
            )
    return wrong


def _mentions(
    config: TraceConfig, mentions: Iterable[Mention], declared: set[str]
) -> list[Finding]:
    """V16 — an ID of this repo's kind, declared nowhere, where it declares nothing: later in a
    heading, or as a table row's first cell. A file read for two types is reported once."""
    wrong: list[Finding] = []
    seen: set[tuple[str, str, int, str]] = set()
    for mention in mentions:
        key = (mention.token, mention.file, mention.line, mention.where)
        own = _own_type(config, mention.token)
        if key in seen or own is None or mention.token in declared:
            continue
        seen.add(key)
        say = findings.id_not_first if mention.where == "heading" else findings.id_in_table
        wrong.append(say(mention.token, own.name, own.files, mention.file, mention.line))
    return wrong


def _stem(text: str) -> str:
    return text.split("-", 1)[0]


def _numbered(item_id: str) -> tuple[int, str]:
    """Sort key: AGR-2 before AGR-10."""
    number = re.search(r"\d+$", item_id)
    return (int(number.group()) if number else 0, item_id)
