"""Coverage — the project's rules, as data, judged on this repo's items.

The load-bearing claims, each pinned by a test:

1. An unmet rule is a gap: `incoming:M` needs a link M pointing at the item, `outgoing:M` one it
   declares. `where` narrows by an exact field value; an item missing the field gets V05 and no
   gap. No other exemption exists.
2. A link to an item not verified here counts; an `Assumes` link counts toward nothing; only this
   repo's items are judged.
3. A gap's next move is specific: the violation that refused the link first, then a stray marker,
   then — when no item type here can carry the marker — that, else the marker's own form.
4. Gaps come back sorted by file, line and code.
"""

from pathlib import Path

from qmstrace.core.config import TraceConfig
from qmstrace.core.graph import Surroundings, TraceGraph
from qmstrace.core.judge import coverage
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
    forms = {t.name: FORMS[t.extractor] for t in config.item_types.values() if t.extractor}
    return violations + coverage(config, graph, violations, strays, forms)


def gaps(found: list[Finding]) -> list[tuple[str, str | None]]:
    return [(f.code, f.item) for f in found if f.code.startswith("G")]


# ── 1. rules as data ───────────────────────────────────────────────────────────────────────


def test_every_unmet_rule_is_a_gap(service: TraceConfig) -> None:
    assert gaps(judged(service)) == [
        ("G03", "DSN-SVC-02"),
        ("G04", "DSN-SVC-02"),
        ("G02", "REQ-SVC-02"),
    ]


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


def test_the_form_to_write_comes_from_the_extractor_that_reads_it(service: TraceConfig) -> None:
    fix = fix_of(judged(service), "G02", "REQ-SVC-02")
    assert 'on the test case, write `@pytest.mark.verifies("REQ-SVC-02")` on the test' in fix
    assert "only if it is true" in fix


def test_a_rule_no_type_here_can_meet_says_so(project: Path) -> None:
    from qmstrace.workspace import Workspace

    found = Workspace.open(project / "client").assessment()
    graph, config = found.graph, found.config
    forms = {t.name: FORMS[t.extractor] for t in config.item_types.values() if t.extractor}
    client_gaps = coverage(config, graph, found.violations, (), forms)
    assert "this repo declares no design element" in fix_of(client_gaps, "G01", "REQ-CLT-01")
    assert "for it to point at" in fix_of(client_gaps, "G06", "src/client/api.py")


# ── 4. order ───────────────────────────────────────────────────────────────────────────────


def test_gaps_come_back_sorted(service: TraceConfig) -> None:
    found = [f for f in judged(service) if f.code.startswith("G")]
    assert found == sorted(found, key=lambda f: (f.file, f.line, f.code))
