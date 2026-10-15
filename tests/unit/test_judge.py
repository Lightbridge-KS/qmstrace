"""Coverage — the project's rules, as data, judged on this repo's items.

The load-bearing claims, each pinned by a test:

1. An unmet rule is a gap: `incoming:M` needs a link M pointing at the item, `outgoing:M` one it
   declares. `where` narrows by an exact field value; an item missing the field gets V05 and no
   gap. No other exemption exists.
2. A link to an item not verified here counts; an `Assumes` link counts toward nothing; only this
   repo's items are judged.
3. A gap's next move is specific: the violation that refused the link first, then a stray marker,
   then — when no item type here can carry the marker — that, else the marker's own form. A link
   no item here can be the target of names the siblings that declare one, if any — still only
   if it is true; with none, it says to write the design here.
4. Gaps come back sorted by file, line and code.
"""

from pathlib import Path

import pytest

from qmstrace.core.config import TraceConfig
from qmstrace.core.graph import Surroundings, TraceGraph
from qmstrace.core.judge import Way, coverage
from qmstrace.core.judge._coverage import _fix
from qmstrace.core.model import Extracted, Finding, Item
from qmstrace.extract.base import FORMS, REGISTRY

SRS = """\
### REQ-SVC-01 — A call carries a key
Statement.
- Category: security
- Origin: AGR-1
- Verify-by: test

### REQ-SVC-02 — Records survive a restart
Statement.
- Category: reliability
- Origin: AGR-2
- Verify-by: test
"""
DESIGN = """\
## DSN-SVC-01 — Key check
Satisfies: REQ-SVC-01

## DSN-SVC-02 — Store
Satisfies: REQ-SVC-02
"""
KEYS = '"""Key check.\n\nImplements: DSN-SVC-01\n"""\n'
TESTS = '@pytest.mark.verifies("REQ-SVC-01", "DSN-SVC-01")\ndef test_x():\n    pass\n'
FILES = {
    "docs/req/service-srs.md": SRS,
    "docs/design/service-design.md": DESIGN,
    "src/service/keys.py": KEYS,
    "tests/unit/test_keys.py": TESTS,
}
AGREED = Surroundings(externals={"agreement": frozenset({"AGR-1", "AGR-2", "AGR-3"})})


def judged(
    config: TraceConfig, changes: dict[str, str] | None = None, around: Surroundings = AGREED
) -> list[Finding]:
    from qmstrace.infra.globbing import matches

    parts: list[Extracted] = []
    for path, text in (FILES | (changes or {})).items():
        (item_type,) = [t for t in config.item_types.values() if t.files and matches(path, t.files)]
        assert item_type.extractor is not None
        parts.append(REGISTRY[item_type.extractor](path, text, item_type, config))
    graph, violations = TraceGraph.build(config, parts, around)
    strays = [s for part in parts for s in part.strays]
    ways = {t.name: (Way(FORMS[t.extractor]),) for t in config.item_types.values() if t.extractor}
    return violations + coverage(config, graph, violations, strays, ways)


def gaps(found: list[Finding]) -> list[tuple[str, str | None]]:
    return [(f.code, f.item) for f in found if f.code.startswith("G")]


# ── 1. rules as data ───────────────────────────────────────────────────────────────────────


@pytest.mark.verifies("DSN-QMT-06")
def test_every_unmet_rule_is_a_gap(service: TraceConfig) -> None:
    assert gaps(judged(service)) == [
        ("G03", "DSN-SVC-02"),
        ("G04", "DSN-SVC-02"),
        ("G02", "REQ-SVC-02"),
    ]


@pytest.mark.verifies("DSN-QMT-06")
def test_where_narrows_by_an_exact_value(service: TraceConfig) -> None:
    inspected = SRS.replace("- Verify-by: test\n", "- Verify-by: inspection\n")
    assert ("G02", "REQ-SVC-02") not in gaps(
        judged(service, {"docs/req/service-srs.md": inspected})
    )
    wrong_case = SRS.replace("Origin: AGR-2\n- Verify-by: test", "Origin: AGR-2\n- Verify-by: Test")
    found = judged(service, {"docs/req/service-srs.md": wrong_case})
    assert ("V05", "REQ-SVC-02") in [(f.code, f.item) for f in found]
    assert ("G02", "REQ-SVC-02") not in gaps(found)  # no rule matches a misspelled value


def test_an_item_missing_the_where_field_gets_v05_and_no_gap(service: TraceConfig) -> None:
    missing = SRS[: SRS.index("### REQ-SVC-02")] + SRS[SRS.index("### REQ-SVC-02") :].replace(
        "- Verify-by: test\n", ""
    )
    found = judged(service, {"docs/req/service-srs.md": missing})
    assert ("V05", "REQ-SVC-02") in [(f.code, f.item) for f in found]
    assert ("G02", "REQ-SVC-02") not in gaps(found)


# ── 2. what counts, and whose items ────────────────────────────────────────────────────────


def test_a_link_to_an_item_not_verified_here_counts(service: TraceConfig) -> None:
    cites = '@pytest.mark.verifies("REQ-CLT-01")\ndef test_y():\n    pass\n'
    around = Surroundings(every_sibling_read=False, externals=AGREED.externals)
    found = judged(service, {"tests/unit/test_other.py": cites}, around)
    assert not [g for g in gaps(found) if g[0] == "G07"]


def test_an_assumption_counts_toward_nothing(service: TraceConfig) -> None:
    assuming = DESIGN + "\n## DSN-SVC-03 — Cache\nAssumes: DSN-SVC-01\n"
    assert ("G05", "DSN-SVC-03") in gaps(
        judged(service, {"docs/design/service-design.md": assuming})
    )


def test_being_assumed_is_not_being_satisfied(service: TraceConfig) -> None:
    """G01 needs an incoming Satisfies; an incoming Assumes does not count."""
    srs = SRS + "\n### REQ-SVC-03 — Assumed only\nStatement.\n- Category: security\n"
    srs += "- Origin: AGR-3\n- Verify-by: inspection\n"
    design = DESIGN.replace(
        "Satisfies: REQ-SVC-02\n", "Satisfies: REQ-SVC-02\nAssumes: REQ-SVC-03\n"
    )
    found = judged(
        service, {"docs/req/service-srs.md": srs, "docs/design/service-design.md": design}
    )
    assert ("G01", "REQ-SVC-03") in gaps(found)


def test_only_this_repos_items_are_judged(service: TraceConfig) -> None:
    sibling = {
        "REQ-CLT-09": Item("REQ-CLT-09", "requirement", "../client/x.md", 1, "X", "sha256:0")
    }
    around = Surroundings(siblings={"client": sibling}, externals=AGREED.externals)
    assert "REQ-CLT-09" not in [item for _, item in gaps(judged(service, around=around))]


# ── 3. the next move ───────────────────────────────────────────────────────────────────────


def fix_of(found: list[Finding], code: str, item: str) -> str:
    return next(f.next_move for f in found if (f.code, f.item) == (code, item))


def test_a_gap_names_the_violation_that_refused_its_link(service: TraceConfig) -> None:
    dangling = DESIGN.replace("Satisfies: REQ-SVC-02", "Satisfies: REQ-SVC-09")
    found = judged(service, {"docs/design/service-design.md": dangling})
    fix = fix_of(found, "G05", "DSN-SVC-02")
    assert "first fix V03 at docs/design/service-design.md:5" in fix
    assert "Do not add a second line" in fix


def test_a_stray_marker_is_named_on_the_module_and_on_the_element(service: TraceConfig) -> None:
    store = '"""Keeps records."""\n\n# Implements: DSN-SVC-02\n'
    found = judged(service, {"src/service/store.py": store})
    assert "'Implements:' line at src/service/store.py:3 is outside the module docstring" in fix_of(
        found, "G06", "src/service/store.py"
    )
    assert "src/service/store.py:3" in fix_of(found, "G03", "DSN-SVC-02")


@pytest.mark.verifies("DSN-QMT-06")
def test_the_form_to_write_comes_from_the_extractor_that_reads_it(service: TraceConfig) -> None:
    fix = fix_of(judged(service), "G02", "REQ-SVC-02")
    assert 'on the automated test, write `@pytest.mark.verifies("REQ-SVC-02")` on the test' in fix
    assert "only if it is true" in fix


@pytest.mark.verifies("DSN-QMT-14")
def test_in_the_ledgers_check_a_next_move_names_the_repos_to_write_in(
    service: TraceConfig,
) -> None:
    rule = next(r for r in service.rules if r.code == "G02")
    requirement = Item("REQ-SVC-01", "requirement", "docs/req/srs.md", 1, "r", "d")
    homes = {"automated_test": ("client", "service"), "requirement": ("ledger",)}
    ways = {
        t.name: (Way(FORMS[t.extractor], homes.get(t.name, ())),)
        for t in service.item_types.values()
        if t.extractor
    }
    said = _fix(service, rule, requirement, [], [], ways, whole_project=True)
    assert said.startswith("on the automated test in client or service, write")
    nobody = _fix(service, rule, requirement, [], [], {}, whole_project=True)
    assert nobody.startswith("no repo of the project declares an automated test")


def test_a_rule_no_type_here_can_meet_says_so(project: Path) -> None:
    from qmstrace.workspace import Workspace

    found = Workspace.open(project / "client").assessment()
    graph, config = found.graph, found.config
    ways = {t.name: (Way(FORMS[t.extractor]),) for t in config.item_types.values() if t.extractor}
    client_gaps = coverage(config, graph, found.violations, (), ways)
    assert "this repo declares no design element" in fix_of(client_gaps, "G01", "REQ-CLT-01")
    # The service, beside it, declares design elements: the next move names it, hedged.
    assert fix_of(client_gaps, "G06", "src/client/api.py") == (
        "Fix: this repo declares no design element for it to point at, but service does: write "
        "`Implements: <design element ID>` in its docstring, citing an item of service — only if "
        "it is true: the link states that this component implements that design element. If "
        "none is, declare the right one where the project keeps them, then write the link."
    )


@pytest.mark.verifies("DSN-QMT-06")
def test_a_link_no_repo_read_can_point_at_keeps_the_write_it_here_move(project: Path) -> None:
    """With no sibling declaring a target, the move is today's, byte for byte."""
    from qmstrace.workspace import Workspace

    found = Workspace.open(project / "client").assessment()
    config = found.config
    rule = next(r for r in config.rules if r.code == "G06")
    module = next(i for i in found.graph.items("component"))
    ways = {t.name: (Way(FORMS[t.extractor]),) for t in config.item_types.values() if t.extractor}
    alone = _fix(config, rule, module, [], [], ways)
    assert alone == (
        "this repo declares no design element for it to point at — write the design here and "
        "add `Implements: <design element ID>` in its docstring, or cite another repo's only if "
        "this item really serves it."
    )
    # Siblings that hold other types only change nothing; two that hold the type are both named.
    assert _fix(config, rule, module, [], [], ways, held={"requirement": {"service"}}) == alone
    both = _fix(config, rule, module, [], [], ways, held={"design_element": {"service", "ledger"}})
    assert (
        "but ledger and service do: write" in both and "citing an item of ledger or service" in both
    )


# ── 4. order ───────────────────────────────────────────────────────────────────────────────


def test_gaps_come_back_sorted(service: TraceConfig) -> None:
    found = [f for f in judged(service) if f.code.startswith("G")]
    assert found == sorted(found, key=lambda f: (f.file, f.line, f.code))


def test_a_table_row_is_named_only_on_its_own_items_gap(service: TraceConfig) -> None:
    tabled = DESIGN.replace(
        "Satisfies: REQ-SVC-01", "| Link | Target |\n|---|---|\n| Satisfies | REQ-SVC-01 |"
    ).replace("Satisfies: REQ-SVC-02", "Body.")
    found = judged(service, {"docs/design/service-design.md": tabled})
    assert "'Satisfies' table row at docs/design/service-design.md:4 is not read" in fix_of(
        found, "G05", "DSN-SVC-01"
    )
    assert "table row" not in fix_of(found, "G05", "DSN-SVC-02")
    assert "docs/design/service-design.md:4" in fix_of(found, "G01", "REQ-SVC-01")


def test_a_line_outside_every_section_is_named_on_the_files_items(service: TraceConfig) -> None:
    loose = "Satisfies: REQ-SVC-01\n\n" + DESIGN.replace("Satisfies: REQ-SVC-01\n", "")
    found = judged(service, {"docs/design/service-design.md": loose})
    assert "is outside every item's section" in fix_of(found, "G05", "DSN-SVC-01")
    assert "docs/design/service-design.md:1" in fix_of(found, "G01", "REQ-SVC-01")


def test_compatibility_exports_are_the_original_objects() -> None:
    from qmstrace.core import judge
    from qmstrace.core.judge import _baselines, _coverage, _suspects

    for owner, names in (
        (_coverage, ("Form", "coverage")),
        (_baselines, ("resolve_baselines", "guard")),
        (_suspects, ("suspects",)),
    ):
        for name in names:
            assert getattr(judge, name) is getattr(owner, name)


# ── every way a link can be made (ADR-0003) ────────────────────────────────────────────────

CASES_SCHEMA = Path(__file__).parents[1] / "fixtures" / "cases" / "ledger" / "qmstrace.schema.toml"
CASES_LEDGER = CASES_SCHEMA.parent / "qmstrace.toml"


def _xunit_like(marker: str, target: str) -> str:
    return f'`[Fact(DisplayName = "{target} …")]` on the test method'


@pytest.fixture(scope="module")
def cases_config() -> TraceConfig:
    return TraceConfig.parse(CASES_LEDGER.read_text("utf-8"), CASES_SCHEMA.read_text("utf-8"))


@pytest.mark.verifies("DSN-QMT-06", "DSN-QMT-14")
def test_a_gap_that_several_ways_can_meet_names_them_all(cases_config: TraceConfig) -> None:
    rule = next(r for r in cases_config.rules if r.code == "G02")
    requirement = Item("REQ-SVC-01", "requirement", "docs/req/service-srs.md", 5, "r", "d")
    ways = {
        "test_case": (Way(FORMS["markdown"], ("ledger",)),),
        "automated_test": (Way(_xunit_like, ("agent",)), Way(FORMS["pytest"], ("service",))),
    }
    said = _fix(cases_config, rule, requirement, [], [], ways, whole_project=True)
    assert said == (
        "write one of these — on the automated test in agent, "
        '`[Fact(DisplayName = "REQ-SVC-01 …")]` on the test method; on the automated test in '
        'service, `@pytest.mark.verifies("REQ-SVC-01")` on the test; on the test case in '
        "ledger, `verifies: REQ-SVC-01` under its heading — only if it is true: the link states "
        "that the automated test or test case verifies REQ-SVC-01."
    )


@pytest.mark.verifies("DSN-QMT-06")
def test_one_repos_check_names_a_source_another_repo_reads(cases_config: TraceConfig) -> None:
    rule = next(r for r in cases_config.rules if r.code == "G02")
    requirement = Item("REQ-SVC-01", "requirement", "docs/req/service-srs.md", 5, "r", "d")
    said = _fix(cases_config, rule, requirement, [], [], {"test_case": (Way(FORMS["markdown"]),)})
    assert said.startswith("on the test case, write `verifies: REQ-SVC-01` under its heading")
    assert said.endswith(
        " Or another repo of the project meets REQ-SVC-01 with a link from its automated test: "
        "qmstrace ledger check, run in the ledger, judges that."
    )


@pytest.mark.verifies("DSN-QMT-14")
def test_an_items_own_gap_is_written_the_way_its_own_repo_reads_it(
    cases_config: TraceConfig,
) -> None:
    rule = next(r for r in cases_config.rules if r.code == "G07")
    test = Item(
        "agent:tests/Unit/KeyTests.cs::KeyTests::Refused", "automated_test", "f", 1, "t", "d"
    )
    ways = {
        "automated_test": (Way(_xunit_like, ("agent",)), Way(FORMS["pytest"], ("service",))),
        "requirement": (Way(FORMS["markdown"], ("ledger",)),),
    }
    agent = _fix(cases_config, rule, test, [], [], ways, whole_project=True, repo="agent")
    service = _fix(cases_config, rule, test, [], [], ways, whole_project=True, repo="service")
    assert agent.startswith('write `[Fact(DisplayName = "<requirement or design element or ')
    assert service.startswith("write `@pytest.mark.verifies(")
