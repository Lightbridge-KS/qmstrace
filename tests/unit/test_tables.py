"""The ledger's tables — derived from the schema, so a project whose chain differs gets its own
columns with no engine change (ADR-0005).

The load-bearing claims, each pinned by a test:

1. Columns come from the schema: test cases are what `verifies` both leaves and reaches,
   automated tests what it only leaves; the other coverage links walked from the requirement
   give the chain, each column named after its item type.
2. The matrix has one row per requirement, design element and test case. A test that verifies
   directly has a row of its own, a case nothing runs still has one, a requirement-level case
   repeats on each design row, a case run through another case lists that case's tests, and a
   requirement with nothing below it still has its row. Withdrawn items are in no row.
3. The register has every requirement, withdrawn ones included; the coverage summary counts
   each tier against the rules that ask for it, their `where` included.
"""

from collections.abc import Mapping, Sequence
from dataclasses import replace
from types import SimpleNamespace

import pytest

from qmstrace.core.config import TraceConfig
from qmstrace.core.errors import CouldNotJudge
from qmstrace.core.graph import Surroundings, TraceGraph
from qmstrace.core.model import Extracted, Item, Link
from qmstrace.core.results import Report, ReportEntry, ReportSource, Results, summarize
from qmstrace.core.tables import VerdictCell, coverage, matrix, requirements

TYPES = """\
version = 1
project = "T"

[item_types.requirement]
[item_types.requirement.values]
"Verify-by" = ["test", "inspection"]
[item_types.design_element]
[item_types.component]
[item_types.test_case]
[item_types.automated_test]
"""
CHAIN = """\
[links]
Origin     = { from = ["requirement"],    to = ["origin_clause"] }
Satisfies  = { from = ["design_element"], to = ["requirement"] }
Implements = { from = ["component"],      to = ["design_element"] }
Assumes    = { from = ["requirement"],    to = ["requirement"], coverage = false }
"""
VERIFIES = (
    'verifies   = { from = ["automated_test", "test_case"], '
    'to = ["requirement", "design_element", "test_case"] }\n'
)
RULES = """\
[[rules]]
code  = "G02"
item  = "requirement"
where = { "Verify-by" = "test" }
needs = "incoming:verifies"
text  = "no test verifies it yet."
"""
EXTERNALS = """\
[externals.agreement]
item_type   = "origin_clause"
prefix      = "AGR-"
source      = "agreement.md"
declared_as = '^- \\*\\*(AGR-\\d+)\\*\\*'
"""
CASES = TYPES + CHAIN + VERIFIES + "\n" + RULES + "\n" + EXTERNALS
NO_CASES = (
    TYPES.replace("[item_types.test_case]\n", "")
    + CHAIN
    + ('verifies   = { from = ["automated_test"], to = ["requirement", "design_element"] }\n')
    + "\n"
    + EXTERNALS
)
NO_VERIFIES = TYPES + CHAIN + "\n" + EXTERNALS
RENAMED = (
    CASES.replace("design_element", "design")
    .replace("component", "module")
    .replace("automated_test", "check")
)
AGREEMENT = Surroundings(externals={"agreement": frozenset({"AGR-1"})})


def item(item_id: str, kind: str, **fields: str) -> Item:
    return Item(item_id, kind, "x.md", 1, item_id.lower(), "d", fields)


def link(src: str, marker: str, dst: str) -> Link:
    return Link(src, dst, marker, "x.md", 1)


def graph_of(
    schema: str, items: Sequence[Item], links: Sequence[Link]
) -> tuple[TraceConfig, TraceGraph]:
    config = TraceConfig.of_schema(schema)
    part = Extracted(items=tuple(items), links=tuple(links))
    graph, wrong = TraceGraph.build(config, [part], AGREEMENT)
    assert not wrong, wrong
    return config, graph


def cases_graph(
    extra_items: Sequence[Item] = (),
    extra_links: Sequence[Link] = (),
    *,
    schema: str = "",
    levels: Mapping[str, str] | None = None,
    case_levels: Mapping[str, str] | None = None,
) -> tuple[TraceConfig, TraceGraph]:
    items = [
        item("REQ-T-01", "requirement", **{"Verify-by": "test"}),
        item("REQ-T-02", "requirement", **{"Verify-by": "inspection"}),
        item("DSN-T-01", "design_element"),
        item("DSN-T-02", "design_element"),
        item("src/a.py", "component"),
        item("TC-T-01.1", "test_case"),
        item("TC-T-01.2", "test_case"),
        item("TC-T-01.3", "test_case"),
        item("t::one", "automated_test"),
        item("t::two", "automated_test"),
        item("t::direct", "automated_test"),
        *extra_items,
    ]
    links = [
        link("REQ-T-01", "Origin", "AGR-1"),
        link("DSN-T-01", "Satisfies", "REQ-T-01"),
        link("DSN-T-02", "Satisfies", "REQ-T-01"),
        link("src/a.py", "Implements", "DSN-T-01"),
        link("TC-T-01.1", "verifies", "REQ-T-01"),  # requirement-level: repeats on each design row
        link("TC-T-01.2", "verifies", "DSN-T-01"),
        link("TC-T-01.3", "verifies", "TC-T-01.2"),  # a case run through another case
        link("t::one", "verifies", "TC-T-01.1"),
        link("t::two", "verifies", "TC-T-01.3"),
        link("t::direct", "verifies", "DSN-T-02"),  # no test case between
        *extra_links,
    ]
    items = [
        replace(
            i,
            level=(levels or {}).get(i.id, i.level),
            fields={
                **i.fields,
                **({"Level": case_levels[i.id]} if i.id in (case_levels or {}) else {}),
            },
        )
        for i in items
    ]
    return graph_of(schema or CASES, items, links)


# ── 1. columns come from the schema ─────────────────────────────────────────────────────────


@pytest.mark.verifies("DSN-QMT-16")
def test_the_columns_follow_the_chain_and_are_named_after_its_item_types() -> None:
    columns = matrix(*cases_graph()).columns
    assert [(c.name, c.cell, c.via) for c in columns] == [
        ("origin_clause", "ids", "Origin"),
        ("requirement", "id", None),
        ("title", "text", None),
        ("design_element", "id", "Satisfies"),
        ("component", "ids", "Implements"),
        ("test_case", "id", "verifies"),
        ("automated_test", "ids", "verifies"),
    ]


@pytest.mark.verifies("DSN-QMT-16")
def test_a_schema_with_no_test_case_has_no_test_case_column() -> None:
    config, graph = graph_of(
        NO_CASES,
        [item("REQ-T-01", "requirement"), item("t::one", "automated_test")],
        [link("t::one", "verifies", "REQ-T-01")],
    )
    table = matrix(config, graph)
    assert [c.name for c in table.columns][-2:] == ["component", "automated_test"]
    assert [r["automated_test"] for r in table.rows] == [("t::one",)]


@pytest.mark.verifies("DSN-QMT-16")
def test_renamed_types_name_their_columns() -> None:
    config, graph = graph_of(
        RENAMED,
        [item("REQ-T-01", "requirement"), item("DSN-T-01", "design"), item("t::one", "check")],
        [link("DSN-T-01", "Satisfies", "REQ-T-01"), link("t::one", "verifies", "DSN-T-01")],
    )
    names = [c.name for c in matrix(config, graph).columns]
    assert names == [
        "origin_clause",
        "requirement",
        "title",
        "design",
        "module",
        "test_case",
        "check",
    ]


@pytest.mark.verifies("DSN-QMT-16")
def test_a_schema_without_verifies_has_no_test_columns() -> None:
    config, graph = graph_of(NO_VERIFIES, [item("REQ-T-01", "requirement")], [])
    assert [c.name for c in matrix(config, graph).columns] == [
        "origin_clause",
        "requirement",
        "title",
        "design_element",
        "component",
    ]


@pytest.mark.verifies("DSN-QMT-16")
def test_a_schema_without_a_requirement_type_cannot_be_tabled() -> None:
    config = TraceConfig.of_schema('version = 1\nproject = "T"\n[item_types.component]\n')
    with pytest.raises(CouldNotJudge) as caught:
        matrix(config, TraceGraph.build(config, [])[0])
    assert "declares no requirement type" in caught.value.what


# ── 2. the matrix's rows ────────────────────────────────────────────────────────────────────


def grain(row: dict[str, object]) -> tuple[object, ...]:
    return (row["requirement"], row["design_element"], row["test_case"], row["automated_test"])


@pytest.mark.verifies("DSN-QMT-16")
def test_every_row_of_the_matrix_has_its_grain() -> None:
    table = matrix(*cases_graph())
    assert [grain(dict(r)) for r in table.rows] == [
        ("REQ-T-01", "DSN-T-01", "TC-T-01.1", ("t::one",)),  # requirement-level, on DSN-T-01
        ("REQ-T-01", "DSN-T-01", "TC-T-01.2", ("t::two",)),  # run through TC-T-01.3
        ("REQ-T-01", "DSN-T-02", "TC-T-01.1", ("t::one",)),  # the same case, on DSN-T-02
        ("REQ-T-01", "DSN-T-02", None, ("t::direct",)),  # a test with no case between
        ("REQ-T-02", None, None, ()),  # nothing below it, still a row
    ]
    assert table.rows[0]["origin_clause"] == ("AGR-1",)
    assert table.rows[0]["component"] == ("src/a.py",)
    assert table.rows[2]["component"] == ()


@pytest.mark.verifies("DSN-QMT-16")
def test_a_case_nothing_runs_still_has_a_row() -> None:
    table = matrix(
        *cases_graph([item("TC-T-02.1", "test_case")], [link("TC-T-02.1", "verifies", "REQ-T-02")])
    )
    assert ("REQ-T-02", None, "TC-T-02.1", ()) in [grain(dict(r)) for r in table.rows]


@pytest.mark.verifies("DSN-QMT-16")
def test_withdrawn_items_are_in_no_row_and_the_table_says_so() -> None:
    config, graph = cases_graph(
        [item("REQ-T-03", "requirement", Status="withdrawn"), item("t::stray", "automated_test")]
    )
    table = matrix(config, graph)
    assert "REQ-T-03" not in {r["requirement"] for r in table.rows}
    assert table.notices == (
        "1 withdrawn requirement(s) are in no row.",
        "Items that reach no requirement are in no row: test_case 1, automated_test 1.",
    )


# ── 3. the register and the coverage summary ───────────────────────────────────────────────


@pytest.mark.verifies("DSN-QMT-16")
def test_the_register_has_every_requirement_with_its_fields_and_origins() -> None:
    config, graph = cases_graph([item("REQ-T-03", "requirement", Status="withdrawn")])
    table = requirements(config, graph)
    assert [c.name for c in table.columns] == [
        "requirement",
        "title",
        "origin_clause",
        "Verify-by",
        "Change",
        "Status",
        "repo",
        "where",
    ]
    assert [(r["requirement"], r["Status"]) for r in table.rows] == [
        ("REQ-T-01", None),
        ("REQ-T-02", None),
        ("REQ-T-03", "withdrawn"),
    ]
    assert table.rows[0]["origin_clause"] == ("AGR-1",)


@pytest.mark.verifies("DSN-QMT-16")
def test_coverage_counts_each_tier_against_the_rules_that_ask_for_it() -> None:
    rows = {r["tier"]: dict(r) for r in coverage(*cases_graph()).rows}
    # no rule asks for a design element here, so every live requirement counts
    assert (rows["design_element"]["of"], rows["design_element"]["covered"]) == (2, 1)
    assert rows["design_element"]["not_covered_ids"] == ("REQ-T-02",)
    # G02 selects Verify-by = test only: REQ-T-02 is inspected, so not counted
    assert rows["test_case"]["rules"] == ("G02",)
    assert (rows["test_case"]["of"], rows["test_case"]["covered"]) == (1, 1)
    # t::one reaches REQ-T-01 through TC-T-01.1; never through a design element
    assert (rows["automated_test"]["of"], rows["automated_test"]["covered"]) == (1, 1)


# ── 4. verdicts, one column per level (#49b) ───────────────────────────────────────────────

LEVELLED = CASES.replace(
    "[item_types.automated_test]\n",
    '[item_types.automated_test]\nlevels = ["unit", "integration"]\n',
)
FIELDED = (
    CASES.replace(
        "[item_types.test_case]\n",
        '[item_types.test_case]\n[item_types.test_case.values]\nLevel = ["unit", "integration"]\n',
    )
    + '\n[tables.matrix]\nlevel = "Level"\n'
)


def results_of(
    config: TraceConfig, graph: TraceGraph, runs: Mapping[str, list[tuple[str, str]]]
) -> Results:
    """Results for the tests given, each run as (the report's label, its verdict)."""
    by_label: dict[str, list[ReportEntry]] = {}
    for test, found in runs.items():
        for label, verdict in found:
            by_label.setdefault(label, []).append(ReportEntry(test, "t", verdict))  # type: ignore[arg-type]
    reports = {
        ReportSource(label, f"sha-{label}"): Report(tuple(entries), format="junit")
        for label, entries in by_label.items()
    }
    identities = {test: ((test, "t"),) for test in runs}
    return summarize(SimpleNamespace(config=config, graph=graph), reports, identities)  # type: ignore[arg-type]


def cell(table: object, case: str | None, column: str, design: str = "DSN-T-01") -> object:
    rows = table.rows  # type: ignore[attr-defined]
    row = next(r for r in rows if r["test_case"] == case and r["design_element"] == design)
    found = row[column]
    return (found.verdict, tuple(s.label for s in found.reports)) if found else None


@pytest.mark.verifies("DSN-QMT-16")
def test_a_tests_verdict_lands_in_the_column_of_the_level_it_sits_at() -> None:
    config, graph = cases_graph(schema=LEVELLED, levels={"t::one": "unit"})
    table = matrix(config, graph, results_of(config, graph, {"t::one": [("a", "pass")]}))
    assert [c.name for c in table.columns][-3:] == [
        "verdict_unit",
        "verdict_integration",
        "verdict",
    ]
    assert cell(table, "TC-T-01.1", "verdict_unit") == ("pass", ("a",))
    assert cell(table, "TC-T-01.1", "verdict_integration") is None
    assert cell(table, "TC-T-01.1", "verdict") == ("pass", ("a",))


@pytest.mark.verifies("DSN-QMT-16")
def test_with_no_level_on_the_test_the_test_cases_field_names_it() -> None:
    config, graph = cases_graph(schema=FIELDED, case_levels={"TC-T-01.1": "integration"})
    table = matrix(config, graph, results_of(config, graph, {"t::one": [("a", "fail")]}))
    assert cell(table, "TC-T-01.1", "verdict_integration") == ("fail", ("a",))
    assert cell(table, "TC-T-01.1", "verdict_unit") is None


@pytest.mark.verifies("DSN-QMT-16")
def test_where_the_test_sits_wins_over_its_test_cases_level() -> None:
    schema = FIELDED.replace(
        "[item_types.automated_test]\n",
        '[item_types.automated_test]\nlevels = ["unit", "integration"]\n',
    )
    config, graph = cases_graph(
        schema=schema, levels={"t::one": "unit"}, case_levels={"TC-T-01.1": "integration"}
    )
    table = matrix(config, graph, results_of(config, graph, {"t::one": [("a", "pass")]}))
    assert cell(table, "TC-T-01.1", "verdict_unit") == ("pass", ("a",))
    assert cell(table, "TC-T-01.1", "verdict_integration") is None
    assert any("sits at another level than its test case names" in n for n in table.notices)


@pytest.mark.verifies("DSN-QMT-16")
def test_a_test_with_no_level_reaches_only_the_overall_verdict() -> None:
    config, graph = cases_graph(schema=LEVELLED)
    table = matrix(config, graph, results_of(config, graph, {"t::direct": [("a", "skip")]}))
    assert cell(table, None, "verdict_unit", "DSN-T-02") is None
    assert cell(table, None, "verdict", "DSN-T-02") == ("skip", ("a",))
    assert any("have no level" in n for n in table.notices)


@pytest.mark.verifies("DSN-QMT-16")
def test_a_row_no_test_runs_is_untested_and_a_test_with_no_run_has_no_result() -> None:
    config, graph = cases_graph(schema=LEVELLED, levels={"t::one": "unit"})
    table = matrix(
        config, graph, results_of(config, graph, {"t::one": [("a", "pass")], "t::two": []})
    )
    no_test = next(r for r in table.rows if r["requirement"] == "REQ-T-02")
    assert no_test["verdict"] == VerdictCell("untested")
    assert cell(table, "TC-T-01.2", "verdict") == ("no-result", ())


@pytest.mark.verifies("DSN-QMT-16")
def test_a_cell_is_its_tests_worst_verdict_and_names_every_report() -> None:
    config, graph = cases_graph(
        extra_links=[link("t::two", "verifies", "TC-T-01.1")],
        schema=LEVELLED,
        levels={"t::one": "unit", "t::two": "unit"},
    )
    runs = {"t::one": [("a", "pass")], "t::two": [("b", "fail"), ("a", "pass")]}
    table = matrix(config, graph, results_of(config, graph, runs))
    assert cell(table, "TC-T-01.1", "verdict_unit") == ("fail", ("a", "b"))
    # the same verdicts whatever order the reports come in
    flipped = {k: list(reversed(v)) for k, v in reversed(runs.items())}
    assert matrix(config, graph, results_of(config, graph, flipped)).rows == table.rows
