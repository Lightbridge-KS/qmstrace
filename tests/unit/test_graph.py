"""The trace graph — built so that an illegal link never enters it.

The load-bearing claims, each pinned by a test:

1. A clean repo builds a graph with every link in it and no findings; `incoming` and
   `outgoing` read it both ways.
2. Every refused link is a finding and is *not* in the graph: an unknown ID (V03), the wrong
   kind of item at either end (V04), an external ID its source does not declare (V09).
3. An ID declared twice is V01 — twice here, or here and in a sibling; a heading with this
   repo's kind of ID that fails the pattern is V02; required fields and their values are V05,
   spelled exactly; an item where its type is not read is V07.
4. A citation this run cannot verify — a sibling not read — passes as *not verified here*;
   an ID matching this repo's own pattern never does.
"""

import pytest

from qmstrace.core.config import TraceConfig
from qmstrace.core.graph import Home, Surroundings, TraceGraph
from qmstrace.core.model import Extracted, Finding
from qmstrace.extract.base import REGISTRY

SRS = """\
### REQ-SVC-01 — A call carries a key
The service shall reject a call that carries no key.
- Category: security
- Origin: AGR-1
- Verify-by: test

### REQ-SVC-02 — Records survive a restart
The service shall keep every record across a restart.
- Category: reliability
- Origin: AGR-2, AGR-3
- Verify-by: test
"""

DESIGN = """\
## DSN-SVC-01 — Key check
Satisfies: REQ-SVC-01

## DSN-SVC-02 — Store
Satisfies: REQ-SVC-02
Assumes: DSN-SVC-01
"""

MODULE = '"""Key check.\n\nImplements: DSN-SVC-01\n"""\n'

TESTS = """\
import pytest

@pytest.mark.verifies("REQ-SVC-01", "DSN-SVC-01")
def test_a_call_without_a_key_is_refused():
    pass
"""

CLEAN = {
    ("requirement", "docs/req/service-srs.md"): SRS,
    ("design_element", "docs/design/service-design.md"): DESIGN,
    ("component", "src/service/keys.py"): MODULE,
    ("test_case", "tests/unit/test_keys.py"): TESTS,
}
AGREEMENT = Surroundings(externals={"agreement": frozenset({"AGR-1", "AGR-2", "AGR-3"})})


def extracted(config: TraceConfig, files: dict[tuple[str, str], str]) -> list[Extracted]:
    found = []
    for (type_name, path), text in files.items():
        item_type = config.item_types[type_name]
        assert item_type.extractor is not None
        found.append(REGISTRY[item_type.extractor](path, text, item_type, config))
    return found


def build(
    config: TraceConfig,
    changes: dict[tuple[str, str], str] | None = None,
    surroundings: Surroundings = AGREEMENT,
) -> tuple[TraceGraph, list[Finding]]:
    return TraceGraph.build(config, extracted(config, CLEAN | (changes or {})), surroundings)


def codes(found: list[Finding]) -> list[str]:
    return [f.code for f in found]


# ── 1. a clean repo ────────────────────────────────────────────────────────────────────────


def test_a_clean_repo_has_every_link_and_no_findings(service: TraceConfig) -> None:
    graph, found = build(service)
    assert found == []
    assert len(graph.links) == 9
    assert [i.id for i in graph.items("requirement")] == ["REQ-SVC-01", "REQ-SVC-02"]
    test = "tests/unit/test_keys.py::test_a_call_without_a_key_is_refused"
    assert [k.src for k in graph.incoming("REQ-SVC-01", "verifies")] == [test]
    assert [k.dst for k in graph.outgoing("REQ-SVC-02", "Origin")] == ["AGR-2", "AGR-3"]
    assert [k.src for k in graph.incoming("DSN-SVC-01")] == [
        "DSN-SVC-02",
        "src/service/keys.py",
        test,
    ]
    origin = graph.node("AGR-1")
    assert origin is not None and (origin.home, origin.type) == (Home.EXTERNAL, "origin_clause")
    assert graph.node("NOPE-1") is None
    assert graph.unverified() == []


# ── 2. links kept out, each reported ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("changes", "code", "said"),
    [
        (
            {
                (
                    "design_element",
                    "docs/design/service-design.md",
                ): "## DSN-SVC-01 — X\nSatisfies: DSN-SVC-02\n\n"
                "## DSN-SVC-02 — Y\nSatisfies: REQ-SVC-02\n"
            },
            "V04",
            "'Satisfies' may point at requirement, not at a design_element",
        ),
        (
            {
                (
                    "test_case",
                    "tests/unit/test_keys.py",
                ): '@pytest.mark.verifies("AGR-1")\ndef test_x():\n    pass\n'
            },
            "V04",
            "not at a origin_clause",
        ),
        (
            {("requirement", "docs/req/service-srs.md"): SRS + "- Satisfies: REQ-SVC-01\n"},
            "V04",
            "which a requirement may not carry",
        ),
        (
            {("component", "src/service/keys.py"): '"""Implements: DSN-SVC-09"""\n'},
            "V03",
            "declare it in docs/design/*.md",
        ),
        (
            {("component", "src/service/keys.py"): '"""Implements: DSN-XYZ-01"""\n'},
            "V03",
            "may belong to another repo",
        ),
        (
            {("requirement", "docs/req/service-srs.md"): SRS.replace("AGR-1", "AGR-9")},
            "V09",
            "the agreement declares no AGR-9 (it declares AGR-1, AGR-2, AGR-3)",
        ),
    ],
)
def test_a_refused_link_is_reported_and_never_enters(
    service: TraceConfig, changes: dict[tuple[str, str], str], code: str, said: str
) -> None:
    graph, found = build(service, changes)
    refused = [f for f in found if f.code == code]
    assert len(refused) == 1, found
    assert said in refused[0].what + refused[0].next_move
    assert all((k.file, k.line) != (refused[0].file, refused[0].line) for k in graph.links)


def test_an_undeclared_origin_lists_the_real_ones_in_numeric_order(service: TraceConfig) -> None:
    around = Surroundings(externals={"agreement": frozenset({"AGR-10", "AGR-2", "AGR-1"})})
    changes = {("requirement", "docs/req/service-srs.md"): SRS.replace("AGR-3", "AGR-4")}
    _, found = build(service, changes, around)
    assert "(it declares AGR-1, AGR-2, AGR-10)" in found[0].what


def test_an_origin_whose_source_was_not_reached_enters_unverified(service: TraceConfig) -> None:
    around = Surroundings(externals={"agreement": None})
    graph, found = build(
        service, {("requirement", "docs/req/service-srs.md"): SRS.replace("AGR-1", "AGR-9")}, around
    )
    assert found == []
    node = graph.node("AGR-9")
    assert node is not None and node.home is Home.EXTERNAL


# ── 3. items: twice, malformed, fields, misplaced ──────────────────────────────────────────


def test_an_id_declared_twice_names_the_first(service: TraceConfig) -> None:
    again = {("requirement", "docs/req/more-srs.md"): SRS.split("\n\n")[0] + "\n"}
    graph, found = build(service, again)
    (twice,) = found
    assert (twice.code, twice.file, twice.line) == ("V01", "docs/req/more-srs.md", 1)
    assert "first at docs/req/service-srs.md:1" in twice.what
    assert graph.node("REQ-SVC-01") is not None


def test_a_test_function_defined_twice_is_v01(service: TraceConfig) -> None:
    twice = TESTS + "\n\ndef test_a_call_without_a_key_is_refused():\n    pass\n"
    _, found = build(service, {("test_case", "tests/unit/test_keys.py"): twice})
    assert codes(found) == ["V01"]


@pytest.mark.parametrize(
    ("heading", "expected"),
    [
        ("### REQ-SVC-1 — Short number", ["V02"]),
        ("### REQ-SCV-01 — A typo in the key", ["V02"]),
        ("### ADR-01 — Prose that starts with an ID", []),
        ("### DSN-SVC-07 — A design element in the wrong file", []),  # V07's, not V02's
    ],
)
def test_a_heading_of_this_repos_kind_that_fails_the_pattern_is_v02(
    service: TraceConfig, heading: str, expected: list[str]
) -> None:
    _, found = build(service, {("requirement", "docs/req/service-srs.md"): SRS + heading + "\n"})
    assert codes(found) == expected


@pytest.mark.parametrize(
    ("old", "new", "said"),
    [
        ("- Verify-by: test\n\n", "\n", "has no 'Verify-by:' line"),
        ("- Category: security", "- Category: Security", "Category: 'Security'"),
        ("- Verify-by: test\n\n", "- Verify-by: prayer\n\n", "Verify-by: 'prayer'"),
    ],
)
def test_fields_are_required_and_spelled_exactly(
    service: TraceConfig, old: str, new: str, said: str
) -> None:
    _, found = build(
        service, {("requirement", "docs/req/service-srs.md"): SRS.replace(old, new, 1)}
    )
    (wrong,) = found
    assert wrong.code == "V05" and said in wrong.what
    assert "test, inspection, analysis" in wrong.next_move or "security" in wrong.next_move


def test_an_item_where_its_type_is_not_read_is_v07(service: TraceConfig) -> None:
    item_type = service.item_types["requirement"]
    stray = REGISTRY["markdown"]("docs/notes.md", "### REQ-SVC-05 — X\n", item_type, service)
    _, found = TraceGraph.build(
        service, extracted(service, CLEAN), AGREEMENT, misplaced=stray.items
    )
    (wrong,) = found
    assert (wrong.code, wrong.file) == ("V07", "docs/notes.md")
    assert "read from docs/req/*-srs.md; move it there" in wrong.next_move


# ── 4. siblings, read and not ──────────────────────────────────────────────────────────────

CITES_CLIENT = {
    (
        "test_case",
        "tests/unit/test_keys.py",
    ): '@pytest.mark.verifies("REQ-CLT-01")\ndef test_x():\n    pass\n'
}


def test_a_siblings_item_is_cited_like_a_local_one(service: TraceConfig) -> None:
    around = Surroundings(
        siblings={"client": {"REQ-CLT-01": "requirement"}}, externals=AGREEMENT.externals
    )
    graph, found = build(service, CITES_CLIENT, around)
    assert found == []
    node = graph.node("REQ-CLT-01")
    assert node is not None and (node.home, node.repo) == (Home.SIBLING, "client")


def test_a_siblings_item_declared_again_here_is_v01(service: TraceConfig) -> None:
    around = Surroundings(
        siblings={"client": {"REQ-SVC-02": "requirement", "REQ-CLT-01": "requirement"}},
        externals=AGREEMENT.externals,
    )
    text = SRS + "\n### REQ-CLT-01 — Copied from the client\n"
    graph, found = build(service, {("requirement", "docs/req/service-srs.md"): text}, around)
    assert codes(found) == ["V01", "V01"]
    assert all("already declared in sibling repo 'client'" in f.what for f in found)
    assert "a requirement has one home" in found[0].next_move.lower()
    assert graph.node("REQ-SVC-02") is not None and graph.node("REQ-SVC-02").home is Home.SIBLING  # type: ignore[union-attr]


def test_a_citation_this_run_cannot_verify_passes_as_not_verified(service: TraceConfig) -> None:
    around = Surroundings(every_sibling_read=False, externals=AGREEMENT.externals)
    graph, found = build(service, CITES_CLIENT, around)
    assert found == []
    assert graph.unverified() == ["REQ-CLT-01"]


def test_an_id_of_this_repos_own_kind_is_never_given_that_benefit(service: TraceConfig) -> None:
    around = Surroundings(every_sibling_read=False, externals=AGREEMENT.externals)
    cites_own = {
        (
            "test_case",
            "tests/unit/test_keys.py",
        ): '@pytest.mark.verifies("REQ-SVC-07")\ndef test_x():\n    pass\n'
    }
    graph, found = build(service, cites_own, around)
    assert codes(found) == ["V03"]
    assert "no such item in this repo." in found[0].what
    assert graph.unverified() == []


def test_findings_come_back_sorted(service: TraceConfig) -> None:
    broken = SRS.replace("- Category: reliability\n", "").replace("AGR-1", "AGR-9")
    _, found = build(service, {("requirement", "docs/req/service-srs.md"): broken})
    assert [(f.line, f.code) for f in found] == [(4, "V09"), (7, "V05")]
