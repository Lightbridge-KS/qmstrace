"""Judging the work — coverage rules applied to this repo's items. Pure: data in, gaps out.

A coverage rule is data in the project's trace schema: which link an item type must have. An
unmet rule is a **gap** — expected in the middle of the work, and failed only by the gate. No
rule is hidden: a rule with no `where` applies to every item of its type, and one with a `where`
to the items whose field has exactly that value. Rules are judged on this repo's items only;
whether an item is covered across the project is the ledger's question.

A gap's next move is built from data: the form of the marker to write comes from the extractor
that reads it (`forms`), a violation that refused the needed link is named first, and a marker
written where it is not read (a stray) is named when it is the reason.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping

from qmstrace.core import findings
from qmstrace.core.config import CoverageRule, TraceConfig
from qmstrace.core.graph import TraceGraph
from qmstrace.core.model import Finding, Item, Stray

Form = Callable[[str, str], str]


def coverage(
    config: TraceConfig,
    graph: TraceGraph,
    violations: Iterable[Finding] = (),
    strays: Iterable[Stray] = (),
    forms: Mapping[str, Form] | None = None,
) -> list[Finding]:
    """Every unmet coverage rule on this repo's items, sorted by file, line and code.

    Parameters
    ----------
    violations
        What the graph refused — a gap whose needed link was refused points at it.
    strays
        Markers written where they are not read.
    forms
        For each item type this repo scans, how its items write a link.
    """
    refused = list(violations)
    stray_list = list(strays)
    gaps: list[Finding] = []
    for rule in config.rules:
        for item in graph.items(rule.item_type):
            if any(item.fields.get(key) != value for key, value in rule.where.items()):
                continue
            links = (
                graph.incoming(item.id, rule.marker)
                if rule.direction == "incoming"
                else graph.outgoing(item.id, rule.marker)
            )
            if not links:
                fix = _fix(config, rule, item, refused, stray_list, forms or {})
                gaps.append(findings.unmet_rule(rule.code, item, rule.text, fix))
    return sorted(gaps, key=lambda f: (f.file, f.line, f.code))


def _fix(
    config: TraceConfig,
    rule: CoverageRule,
    item: Item,
    refused: list[Finding],
    strays: list[Stray],
    forms: Mapping[str, Form],
) -> str:
    """The next move for one gap — the most specific reason first."""
    link = config.links[rule.marker]
    incoming = rule.direction == "incoming"
    for violation in refused:
        if violation.marker != rule.marker:
            continue
        own = violation.item == item.id or (violation.item is None and violation.file == item.file)
        if (not incoming and own) or (incoming and violation.target == item.id):
            return findings.fix_refused(violation)
    for stray in strays:
        if stray.marker == rule.marker and (
            (not incoming and stray.file == item.file) or (incoming and item.id in stray.targets)
        ):
            return findings.fix_stray(stray.marker, stray.file, stray.line)

    words = item.type.replace("_", " ")
    if incoming:
        here = [t for t in link.sources if t in forms]
        if not here:
            kinds = " or ".join(t.replace("_", " ") for t in link.sources)
            return findings.fix_none_here(kinds, item.id)
        source = here[0].replace("_", " ")
        fact = f"the {source} {rule.marker.lower()} {item.id}"
        return findings.fix_write(forms[here[0]](rule.marker, item.id), fact, on=source)
    target = " or ".join(t.replace("_", " ") for t in link.targets)
    form = forms.get(item.type)
    written = form(rule.marker, f"<{target} ID>") if form else f"'{rule.marker}: <{target} ID>'"
    if not any(t in forms for t in link.targets):
        return findings.fix_no_target(target, written)
    return findings.fix_write(written, f"this {words} {rule.marker.lower()} that {target}")
