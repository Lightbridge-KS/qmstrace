"""Coverage rules and the next move for each unmet rule. Pure: data in, gaps out.

Implements: DSN-QMT-06, DSN-QMT-14
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
    homes: Mapping[str, tuple[str, ...]] | None = None,
) -> list[Finding]:
    """Every unmet coverage rule on the judged items, sorted by file, line and code.

    Parameters
    ----------
    violations
        What the graph refused — a gap whose needed link was refused points at it.
    strays
        Markers written where they are not read.
    forms
        For each item type that is scanned, how its items write a link.
    homes
        In the ledger's check, the repos that declare each item type — a next move then names
        where to write the link, and no gap is sent on to another repo.
    """
    refused = list(violations)
    stray_list = list(strays)
    gaps: list[Finding] = []
    for rule in config.rules:
        for item in graph.items(rule.item_type):
            if item.fields.get("Status") == "withdrawn":
                continue
            if any(item.fields.get(key) != value for key, value in rule.where.items()):
                continue
            links = (
                graph.incoming(item.id, rule.marker)
                if rule.direction == "incoming"
                else graph.outgoing(item.id, rule.marker)
            )
            active = [
                link
                for link in links
                if all(
                    graph.nodes[node].fields.get("Status") != "withdrawn"
                    for node in (link.src, link.dst)
                )
            ]
            if not active:
                fix = _fix(config, rule, item, refused, stray_list, forms or {}, homes)
                gaps.append(findings.unmet_rule(rule.code, item, rule.text, fix))
    return sorted(gaps, key=lambda f: (f.file, f.line, f.code))


def _fix(
    config: TraceConfig,
    rule: CoverageRule,
    item: Item,
    refused: list[Finding],
    strays: list[Stray],
    forms: Mapping[str, Form],
    homes: Mapping[str, tuple[str, ...]] | None = None,
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
        if stray.marker != rule.marker:
            continue
        if incoming:
            meant = item.id in stray.targets
        elif stray.item is not None:  # in an item's section: only that item's gap
            meant = stray.item == item.id
        else:
            meant = stray.file == item.file
        if meant:
            return findings.fix_stray(stray)

    words = item.type.replace("_", " ")
    if incoming:
        here = [t for t in link.sources if t in forms]
        if not here:
            kinds = " or ".join(t.replace("_", " ") for t in link.sources)
            if homes is not None:
                return findings.fix_none_in_project(kinds, item.id)
            return findings.fix_none_here(kinds, item.id)
        source = here[0].replace("_", " ")
        fact = f"the {source} {rule.marker.lower()} {item.id}"
        on = source if homes is None else f"{source} in {' or '.join(homes[here[0]])}"
        return findings.fix_write(forms[here[0]](rule.marker, item.id), fact, on=on)
    target = " or ".join(t.replace("_", " ") for t in link.targets)
    form = forms.get(item.type)
    written = form(rule.marker, f"<{target} ID>") if form else f"'{rule.marker}: <{target} ID>'"
    if not any(t in forms for t in link.targets):
        return findings.fix_no_target(target, written, whole_project=homes is not None)
    return findings.fix_write(written, f"this {words} {rule.marker.lower()} that {target}")
