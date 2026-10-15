"""Coverage rules and the next move for each unmet rule. Pure: data in, gaps out.

Implements: DSN-QMT-06, DSN-QMT-14
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass

from qmstrace.core import findings
from qmstrace.core.config import CoverageRule, TraceConfig
from qmstrace.core.graph import TraceGraph
from qmstrace.core.model import Finding, Item, Stray

Form = Callable[[str, str], str]


@dataclass(frozen=True, slots=True)
class Way:
    """One way to write a link on an item type: the form its extractor reads, and — in the
    ledger's check — the repos whose items are read that way. An item type read by two
    extractors (pytest in one repo, xUnit in another) has two ways."""

    form: Form
    repos: tuple[str, ...] = ()


def coverage(
    config: TraceConfig,
    graph: TraceGraph,
    violations: Iterable[Finding] = (),
    strays: Iterable[Stray] = (),
    ways: Mapping[str, tuple[Way, ...]] | None = None,
    *,
    whole_project: bool = False,
) -> list[Finding]:
    """Every unmet coverage rule on the judged items, sorted by file, line and code.

    Parameters
    ----------
    violations
        What the graph refused — a gap whose needed link was refused points at it.
    strays
        Markers written where they are not read.
    ways
        For each item type that is scanned, how its items write a link — one way per extractor
        that reads the type, each with the repos that use it in the ledger's check.
    whole_project
        The ledger's check: a next move names the repos to write in, and no gap is sent on to
        another repo.
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
                node = graph.nodes.get(item.id)
                repo = node.repo if node is not None else None
                fix = _fix(config, rule, item, refused, stray_list, ways or {}, whole_project, repo)
                gaps.append(findings.unmet_rule(rule.code, item, rule.text, fix))
    return sorted(gaps, key=lambda f: (f.file, f.line, f.code))


def _fix(
    config: TraceConfig,
    rule: CoverageRule,
    item: Item,
    refused: list[Finding],
    strays: list[Stray],
    ways: Mapping[str, tuple[Way, ...]],
    whole_project: bool = False,
    repo: str | None = None,
) -> str:
    """The next move for one gap — the most specific reason first, then every way the missing
    link can be written."""
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
        # An item of the link's own source type (a test case verifying a test case) is legal
        # but never the move to suggest while another source can make the link.
        sources = [t for t in link.sources if t != item.type] or list(link.sources)
        here = [t for t in sources if t in ways]
        if not here:
            kinds = " or ".join(t.replace("_", " ") for t in sources)
            if whole_project:
                return findings.fix_none_in_project(kinds, item.id)
            return findings.fix_none_here(kinds, item.id)
        options = [
            (_on(t, way, whole_project), way.form(rule.marker, item.id))
            for t in here
            for way in ways[t]
        ]
        kinds = " or ".join(t.replace("_", " ") for t in here)
        fact = f"the {kinds} {rule.marker.lower()} {item.id}"
        elsewhere = [t.replace("_", " ") for t in sources if t not in ways]
        if len(options) == 1:
            on, form = options[0]
            said = findings.fix_write(form, fact, on=on)
        else:
            said = findings.fix_write_any(options, fact)
        if elsewhere and not whole_project:
            said += findings.fix_elsewhere(" or ".join(elsewhere), item.id)
        return said
    target = " or ".join(t.replace("_", " ") for t in link.targets)
    its_ways = ways.get(item.type, ())
    way = next((w for w in its_ways if repo in w.repos), its_ways[0] if its_ways else None)
    written = way.form(rule.marker, f"<{target} ID>") if way else f"'{rule.marker}: <{target} ID>'"
    if not any(t in ways for t in link.targets):
        return findings.fix_no_target(target, written, whole_project=whole_project)
    return findings.fix_write(written, f"this {words} {rule.marker.lower()} that {target}")


def _on(item_type: str, way: Way, whole_project: bool) -> str:
    """Which items a way writes on — in the ledger's check, with the repos that hold them."""
    words = item_type.replace("_", " ")
    return f"{words} in {' or '.join(way.repos)}" if whole_project else words
