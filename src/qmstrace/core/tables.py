"""The ledger's tables — the traceability matrix, the requirements register and the coverage
summary — derived from the project's graph and its schema (ADR-0005).

Two names are fixed, as in `results`: the `requirement` type every table starts from, and the
`verifies` link tests make. The rest is the schema's: a type that is both a source and a target
of `verifies` is a test case, a source only an automated test, and the other coverage links,
walked from the requirement, give the rest of the chain. Each column is named after the item
type it holds. Verdicts are not here: they join from test reports.

Implements: DSN-QMT-16
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Literal

from qmstrace.core.config import TraceConfig
from qmstrace.core.errors import CouldNotJudge
from qmstrace.core.graph import TraceGraph
from qmstrace.core.model import Item, id_order
from qmstrace.core.results import ReportSource, Results, Verdict, worst

REQUIREMENT = "requirement"
VERIFIES = "verifies"
WITHDRAWN = "withdrawn"

Kind = Literal["id", "ids", "text", "count", "verdict"]


@dataclass(frozen=True, slots=True)
class VerdictCell:
    """A verdict, and every report it came from — the evidence a reader can open (AGR-8)."""

    verdict: Verdict
    reports: tuple[ReportSource, ...] = ()


Cell = str | int | tuple[str, ...] | VerdictCell | None


@dataclass(frozen=True, slots=True)
class Column:
    """One column: its name, the kind of value its cells hold, the item type those values are,
    and the link that reaches them from the row."""

    name: str
    cell: Kind
    type: str | None = None
    via: str | None = None


@dataclass(frozen=True, slots=True)
class Table:
    """One table: its columns in order, its rows keyed by column name, and what a reader must
    know that no row says."""

    name: str
    columns: tuple[Column, ...]
    rows: tuple[Mapping[str, Cell], ...]
    notices: tuple[str, ...] = ()


def table(
    name: str, config: TraceConfig, graph: TraceGraph, results: Results | None = None
) -> Table:
    """The table named — `matrix`, `requirements` or `coverage` — of the project's graph; the
    matrix carries verdicts when test results are given."""
    if name == "matrix":
        return matrix(config, graph, results)
    return {"requirements": requirements, "coverage": coverage}[name](config, graph)


def matrix(config: TraceConfig, graph: TraceGraph, results: Results | None = None) -> Table:
    """One row per requirement, design element and test case, requirement-major.

    An automated test that verifies directly, with no test case between, has a row of its own; a
    test case nothing runs still has one; a test case that verifies the requirement itself
    repeats on each of its design rows. Withdrawn items are in no row. Given test results, each
    row also carries a verdict per level and an overall one, each naming its reports.
    """
    chain = _Chain.of(config)
    fields = config.tables.matrix_fields
    columns = [
        *(Column(t, "ids", t, marker) for t, marker in chain.upstream),
        Column(REQUIREMENT, "id", REQUIREMENT),
        Column("title", "text"),
        *(Column(name, "text") for name in fields),
        *([Column(chain.design[0], "id", *chain.design)] if chain.design else []),
        *(Column(t, "ids", t, marker) for t, marker, _ in chain.deeper),
        *(Column(t, "id", t, VERIFIES) for t in chain.cases),
        *(Column(t, "ids", t, VERIFIES) for t in chain.tests),
    ]
    rows: list[dict[str, Cell]] = []
    shown: set[str] = set()
    withdrawn = 0
    for req in _sorted(graph.items(REQUIREMENT)):
        if req.fields.get("Status") == WITHDRAWN:
            withdrawn += 1
            continue
        base: dict[str, Cell] = {
            t: _upstream(graph, req.id, marker, t) for t, marker in chain.upstream
        }
        base |= {REQUIREMENT: req.id, "title": req.title}
        base |= {name: req.fields.get(name) for name in fields}
        designs = _into(graph, req.id, *chain.design) if chain.design else ()
        for design in designs or (None,):
            row = dict(base)
            held: dict[str, tuple[str, ...]] = {REQUIREMENT: (req.id,)}
            if chain.design:
                row[chain.design[0]] = design
                held[chain.design[0]] = (design,) if design else ()
            for t, marker, parent in chain.deeper:
                ids = _ordered(s for p in held.get(parent, ()) for s in _into(graph, p, t, marker))
                row[t] = held[t] = ids
            anchors = [a for ids in held.values() for a in ids]
            grains: list[tuple[str | None, tuple[str, ...]]] = [
                (case, chain.runs(graph, case)) for case in chain.verifying(graph, anchors)
            ]
            grains += [(None, (test,)) for test in chain.verifying(graph, anchors, tests=True)]
            for case, runs in grains or [(None, ())]:
                emitted = dict(row)
                for t in chain.cases:
                    emitted[t] = case if case is not None and _type(graph, case) == t else None
                for t in chain.tests:
                    emitted[t] = tuple(r for r in runs if _type(graph, r) == t)
                rows.append(emitted)
                shown.update(i for i in (case, *runs) if i)
            shown.update(a for a in anchors)
    notices = []
    if withdrawn:
        notices.append(f"{withdrawn} withdrawn requirement(s) are in no row.")
    unshown = [
        f"{t} {n}"
        for t in (
            *(d[0] for d in [chain.design] if d),
            *chain.deeper_types,
            *chain.cases,
            *chain.tests,
        )
        if (n := sum(1 for i in graph.items(t) if _live(i) and i.id not in shown))
    ]
    if unshown:
        notices.append(f"Items that reach no requirement are in no row: {', '.join(unshown)}.")
    if results is not None:
        columns, notices = _verdicts(config, graph, chain, results, columns, rows, notices)
    return Table("matrix", tuple(columns), tuple(rows), tuple(notices))


def requirements(config: TraceConfig, graph: TraceGraph) -> Table:
    """One row per requirement, withdrawn ones included: its title, origins, declared fields,
    change, status and where it is declared."""
    chain = _Chain.of(config)
    declared = config.item_types[REQUIREMENT]
    fields = [
        name
        for name in dict.fromkeys((*declared.required, *declared.values))
        if name not in config.links and name not in ("Change", "Status")
    ]
    columns = [
        Column(REQUIREMENT, "id", REQUIREMENT),
        Column("title", "text"),
        *(Column(t, "ids", t, marker) for t, marker in chain.upstream),
        *(Column(name, "text") for name in fields),
        Column("Change", "text"),
        Column("Status", "text"),
        Column("repo", "text"),
        Column("where", "text"),
    ]
    rows: list[dict[str, Cell]] = []
    for req in _sorted(graph.items(REQUIREMENT)):
        node = graph.nodes[req.id]
        row: dict[str, Cell] = {REQUIREMENT: req.id, "title": req.title}
        row |= {t: _upstream(graph, req.id, marker, t) for t, marker in chain.upstream}
        row |= {name: req.fields.get(name) for name in (*fields, "Change", "Status")}
        row |= {"repo": node.repo, "where": node.where}
        rows.append(row)
    return Table("requirements", tuple(columns), tuple(rows))


def coverage(config: TraceConfig, graph: TraceGraph) -> Table:
    """One row per tier that reaches a requirement — its design, its test cases, its automated
    tests — counted against the rules that ask for it. Links are counted, not verdicts."""
    chain = _Chain.of(config)
    columns = (
        Column("tier", "text"),
        Column("via", "text"),
        Column("rules", "ids"),
        Column("of", "count"),
        Column("covered", "count"),
        Column("not_covered", "count"),
        Column("not_covered_ids", "ids", REQUIREMENT),
    )
    live = [r for r in _sorted(graph.items(REQUIREMENT)) if _live(r)]
    tiers = [*([chain.design] if chain.design else []), *((t, VERIFIES) for t in chain.cases)]
    tiers += [(t, VERIFIES) for t in chain.tests]
    rows: list[dict[str, Cell]] = []
    for tier, via in tiers:
        rules = [
            rule
            for rule in config.rules
            if rule.item_type == REQUIREMENT and rule.direction == "incoming"
            if rule.marker == via
        ]
        selected = [
            req for req in live if not rules or any(_selects(rule.where, req) for rule in rules)
        ]
        if tier in chain.tests:
            reached = {r.id for r in selected if chain.tests_reaching(graph, r.id, tier)}
        else:
            reached = {r.id for r in selected if _into(graph, r.id, tier, via)}
        missing = tuple(r.id for r in selected if r.id not in reached)
        rows.append(
            {
                "tier": tier,
                "via": via,
                "rules": tuple(rule.code for rule in rules),
                "of": len(selected),
                "covered": len(reached),
                "not_covered": len(missing),
                "not_covered_ids": missing,
            }
        )
    notices = ("Coverage counts links, not passing tests: no verdict is in this table.",)
    return Table("coverage", columns, tuple(rows), notices)


@dataclass(frozen=True, slots=True)
class _Chain:
    """The schema's chain as the tables read it: what hangs off a requirement, and how."""

    upstream: tuple[tuple[str, str], ...]  # (item type, marker), the requirement points at it
    design: tuple[str, str] | None  # (item type, marker): the row grain's design tier
    deeper: tuple[tuple[str, str, str], ...]  # (item type, marker, the type it points at)
    cases: tuple[str, ...]  # test-case types: sources and targets of `verifies`
    tests: tuple[str, ...]  # automated-test types: sources of `verifies` only

    @classmethod
    def of(cls, config: TraceConfig) -> _Chain:
        if REQUIREMENT not in config.item_types:
            raise CouldNotJudge(
                "The project's trace schema declares no requirement type, so a table has "
                "nothing to start from.",
                "Fix: declare [item_types.requirement] in the ledger's schema — every table "
                "is requirement-major.",
            )
        links = [k for k in config.links.values() if k.counts_for_coverage]
        others = [k for k in links if k.marker != VERIFIES]
        verifies = config.links.get(VERIFIES)
        sources = verifies.sources if verifies else ()
        targets = set(verifies.targets) if verifies else set()
        cases = tuple(t for t in sources if t in targets)
        tests = tuple(t for t in sources if t not in targets)
        placed = {REQUIREMENT, *cases, *tests}
        upstream: list[tuple[str, str]] = []
        for link in others:
            if REQUIREMENT in link.sources:
                for t in link.targets:
                    if t not in placed:
                        placed.add(t)
                        upstream.append((t, link.marker))
        design: tuple[str, str] | None = None
        deeper: list[tuple[str, str, str]] = []
        frontier = [REQUIREMENT]
        while frontier:
            reached: list[str] = []
            for parent in frontier:
                for link in others:
                    if parent not in link.targets:
                        continue
                    for t in link.sources:
                        if t in placed:
                            continue
                        placed.add(t)
                        reached.append(t)
                        if parent == REQUIREMENT and design is None:
                            design = (t, link.marker)
                        else:
                            deeper.append((t, link.marker, parent))
            frontier = reached
        return cls(tuple(upstream), design, tuple(deeper), cases, tests)

    @property
    def deeper_types(self) -> tuple[str, ...]:
        return tuple(t for t, _, _ in self.deeper)

    def verifying(
        self, graph: TraceGraph, anchors: Iterable[str], *, tests: bool = False
    ) -> tuple[str, ...]:
        """The test cases — or, with `tests`, the automated tests — that verify an anchor
        directly."""
        kinds = self.tests if tests else self.cases
        return _ordered(
            k.src
            for anchor in anchors
            for k in graph.incoming(anchor, VERIFIES)
            if _type(graph, k.src) in kinds and _live_id(graph, k.src)
        )

    def runs(self, graph: TraceGraph, case: str) -> tuple[str, ...]:
        """The automated tests that reach a test case along `verifies`, through other test
        cases too — each once, a cycle ending the walk."""
        seen, frontier, found = {case}, [case], set()
        while frontier:
            reached = []
            for current in frontier:
                for link in graph.incoming(current, VERIFIES):
                    if not _live_id(graph, link.src):
                        continue
                    kind = _type(graph, link.src)
                    if kind in self.tests:
                        found.add(link.src)
                    elif kind in self.cases and link.src not in seen:
                        seen.add(link.src)
                        reached.append(link.src)
            frontier = reached
        return _ordered(found)

    def tests_reaching(self, graph: TraceGraph, req: str, tier: str) -> bool:
        """Whether an automated test of `tier` reaches a requirement — directly, or through the
        test cases that verify it. Never through a design element (ADR-0003)."""
        direct = self.verifying(graph, [req], tests=True)
        through = (t for case in self.verifying(graph, [req]) for t in self.runs(graph, case))
        return any(_type(graph, t) == tier for t in (*direct, *through))


def _into(graph: TraceGraph, target: str, kind: str, marker: str) -> tuple[str, ...]:
    """The live items of one type that point at `target` with `marker`."""
    return _ordered(
        k.src
        for k in graph.incoming(target, marker)
        if _type(graph, k.src) == kind and _live_id(graph, k.src)
    )


def _upstream(graph: TraceGraph, source: str, marker: str, kind: str) -> tuple[str, ...]:
    """What a requirement points at with `marker` — an origin clause, say — of one type."""
    return _ordered(
        k.dst for k in graph.outgoing(source, marker) if _type(graph, k.dst) in (kind, None)
    )


def _type(graph: TraceGraph, item_id: str) -> str | None:
    node = graph.nodes.get(item_id)
    return node.type if node is not None else None


def _live(item: Item) -> bool:
    return item.fields.get("Status") != WITHDRAWN


def _live_id(graph: TraceGraph, item_id: str) -> bool:
    node = graph.nodes.get(item_id)
    return node is None or node.fields.get("Status") != WITHDRAWN


def _selects(where: Mapping[str, str], item: Item) -> bool:
    return all(item.fields.get(key) == value for key, value in where.items())


def _sorted(items: Iterable[Item]) -> list[Item]:
    return sorted(items, key=lambda item: id_order(item.id))


def _ordered(ids: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(set(ids), key=id_order))


def _verdicts(
    config: TraceConfig,
    graph: TraceGraph,
    chain: _Chain,
    results: Results,
    columns: list[Column],
    rows: list[dict[str, Cell]],
    notices: list[str],
) -> tuple[list[Column], list[str]]:
    """Add one verdict column per level, then an overall one, to every row.

    An automated test's level is where it sits, when its type declares levels; otherwise the
    level its test case names, in the field `[tables.matrix] level` names. Where both are known
    and differ, where the test sits wins, and a notice counts it.
    """
    field = config.tables.matrix_level
    levels = list(
        dict.fromkeys(
            [
                *(lv for t in chain.tests for lv in config.item_types[t].levels),
                *(
                    v
                    for case in chain.cases
                    for v in (config.item_types[case].values.get(field, ()) if field else ())
                ),
            ]
        )
    )
    columns = [
        *columns,
        *(Column(f"verdict_{level}", "verdict") for level in levels),
        Column("verdict", "verdict"),
    ]
    disagree = 0
    unlevelled: set[str] = set()
    for row in rows:
        case = next((c for t in chain.cases if isinstance(c := row.get(t), str)), None)
        planned = graph.nodes[case].fields.get(field) if case and field else None
        tests = [t for kind in chain.tests for t in _ids(row.get(kind))]
        placed: dict[str, list[str]] = {}
        for test in tests:
            node = graph.nodes.get(test)
            sits = (
                node.item.level if node and node.item and _has_levels(config, node.type) else None
            )
            if sits and planned and sits != planned:
                disagree += 1
            level = sits or (None if node and _has_levels(config, node.type) else planned)
            if level is None:
                unlevelled.add(test)
            else:
                placed.setdefault(level, []).append(test)
        for level in levels:
            row[f"verdict_{level}"] = _cell(results, placed[level]) if level in placed else None
        row["verdict"] = _cell(results, tests) if tests else VerdictCell("untested")
    notices = [
        *notices,
        "Verdicts are matched against the working trees — each report's commit NOT VERIFIED.",
    ]
    if disagree:
        notices.append(
            f"{disagree} time(s) an automated test sits at another level than its test case "
            "names; where the test sits wins."
        )
    if unlevelled and levels:
        notices.append(
            f"{len(unlevelled)} automated test(s) have no level, so their verdicts are in the "
            "overall verdict only."
        )
    unmatched: dict[str, int] = {}
    for run in results.unmatched:
        for source in run.run.sources:
            unmatched[source.repo or "this repo"] = unmatched.get(source.repo or "this repo", 0) + 1
    if unmatched:
        said = ", ".join(f"{repo} {n}" for repo, n in sorted(unmatched.items()))
        notices.append(f"Report runs that match no automated test, by repo: {said}.")
    return columns, notices


def _cell(results: Results, tests: Sequence[str]) -> VerdictCell:
    """The worst verdict of some automated tests, and every report their runs came from."""
    found = [results.tests[t] for t in tests if t in results.tests]
    verdicts = tuple(f.verdict for f in found) + (("no-result",) if len(found) < len(tests) else ())
    sources = sorted({s for f in found for run in f.runs for s in run.sources})
    return VerdictCell(worst(verdicts), tuple(sources))


def _has_levels(config: TraceConfig, kind: str | None) -> bool:
    return kind is not None and kind in config.item_types and bool(config.item_types[kind].levels)


def _ids(cell: Cell) -> tuple[str, ...]:
    return cell if isinstance(cell, tuple) else ()
