"""C# source (ADR-0004) — components from `.cs` files, automated tests from xUnit methods.

The load-bearing claims, each pinned by a test:

1. A `.cs` file is a component, its ID its path; its links are field lines in the first type's
   leading `///` comment, XML tags allowed around them. The same line elsewhere is a stray; a
   mention in prose is neither.
2. A `[Fact]` or `[Theory]` method is one automated test, `path::Class::Method`; the ID that
   starts a literal DisplayName is its link, the one its type carries. Every probe shape from the
   beacon-dotnet bed reads as the bed's measure C9 expects.
3. A run's report identity is the namespace-qualified class — nested classes with `+` — and the
   method; an abstract base's test runs as each concrete subclass in the file.
4. Nothing is dropped silently: a non-literal DisplayName, a trait named after a link, a custom
   test attribute and a test inside `#if` are V15; a commented-out test attribute is a stray; a
   malformed first word is V14.
5. Syntax the grammar does not know outside what is read leaves the file readable; a parse error
   inside it is V08.
6. A level folder matches regardless of case; a type read by `xunit` carries exactly one link.
7. A file with no type to document is marked in its own leading comment (ADR-0007): a `.razor`
   page in the Razor comment at its head, read without the C# parser; a `.cs` file of top-level
   statements in the comment block it opens with. A file that has a type is never read that way.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from qmstrace.core.config import TraceConfig
from qmstrace.core.errors import CouldNotJudge
from qmstrace.core.model import Extracted
from qmstrace.extract.csharp import component, xunit

CASES = Path(__file__).parents[1] / "fixtures" / "cases"
AGENT = CASES / "agent"
SCHEMA = (CASES / "ledger" / "qmstrace.schema.toml").read_text(encoding="utf-8")
SHAPES = (AGENT / "tests" / "Agent.Probe" / "Shapes.cs").read_text(encoding="utf-8")
BLOCK = (AGENT / "tests" / "Agent.Probe" / "BlockNamespace.cs").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def agent() -> TraceConfig:
    return TraceConfig.parse((AGENT / "qmstrace.toml").read_text(encoding="utf-8"), SCHEMA)


def files(config: TraceConfig, text: str, path: str = "src/Agent/KeyCheck.cs") -> Extracted:
    return component.extract(path, text, config.item_types["component"], config)


def read_tests(
    config: TraceConfig, text: str, path: str = "tests/Agent.Probe/Shapes.cs"
) -> Extracted:
    return xunit.extract(path, text, config.item_types["automated_test"], config)


# ── 1. components ──────────────────────────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-21", "DSN-QMT-15")
def test_a_file_is_a_component_that_links_through_its_first_types_doc_comment(
    agent: TraceConfig,
) -> None:
    found = files(agent, (AGENT / "src/Agent/KeyCheck.cs").read_text(encoding="utf-8"))
    (item,) = found.items
    assert (item.id, item.title, item.line) == ("src/Agent/KeyCheck.cs", "KeyCheck", 1)
    assert [(link.marker, link.dst, link.line) for link in found.links] == [
        ("Implements", "DSN-SVC-01", 5)
    ]
    assert found.findings == () and found.strays == ()


@pytest.mark.verifies("REQ-QMT-21")
@pytest.mark.parametrize(
    "doc",
    [
        "/// Implements: DSN-SVC-01\n",
        "/// <remarks>Implements: DSN-SVC-01</remarks>\n",
        "/// <summary>Keys.</summary>\n/// <remarks>\n"
        "/// - Implements: DSN-SVC-01\n/// </remarks>\n",
    ],
)
def test_the_field_line_is_read_whatever_xml_surrounds_it(agent: TraceConfig, doc: str) -> None:
    found = files(agent, f"namespace Agent;\n\n{doc}public static class KeyCheck {{ }}\n")
    assert [link.dst for link in found.links] == ["DSN-SVC-01"]


@pytest.mark.verifies("REQ-QMT-21", "DSN-QMT-15")
def test_the_line_elsewhere_is_a_stray_and_a_mention_in_prose_is_nothing(
    agent: TraceConfig,
) -> None:
    text = (
        "namespace Agent;\n\n/// <summary>Keys (REQ-SVC-01).</summary>\npublic class KeyCheck\n{\n"
        "    // Implements: DSN-SVC-01\n    /// Implements: DSN-SVC-02\n"
        "    public void M() { }\n}\n"
    )
    found = files(agent, text)
    assert found.links == ()
    assert [(s.marker, s.targets, s.line, s.kind) for s in found.strays] == [
        ("Implements", ("DSN-SVC-01",), 6, "doccomment"),
        ("Implements", ("DSN-SVC-02",), 7, "doccomment"),
    ]


def test_a_file_with_no_type_is_a_component_with_no_link(agent: TraceConfig) -> None:
    found = files(agent, "global using System;\n")
    assert len(found.items) == 1 and found.links == () and found.strays == ()


def test_layout_and_ordinary_comments_are_not_a_change(agent: TraceConfig) -> None:
    one = files(agent, "/// Implements: DSN-SVC-01\npublic class A { int X() => 1; }\n")
    two = files(
        agent, "/// Implements: DSN-SVC-01\npublic class A\n{\n    // why\n    int X() => 1;\n}\n"
    )
    assert one.items[0].digest == two.items[0].digest
    three = files(agent, "/// Implements: DSN-SVC-01\npublic class A { int X() => 2; }\n")
    assert three.items[0].digest != one.items[0].digest


# ── 2 & 3. automated tests, the probe shapes ───────────────────────────────────────────────


def shapes(config: TraceConfig) -> tuple[dict[str, tuple[str, ...]], Extracted]:
    found = read_tests(config, SHAPES)
    linked: dict[str, tuple[str, ...]] = {}
    for item in found.items:
        linked[item.title] = tuple(link.dst for link in found.links if link.src == item.id)
    return linked, found


@pytest.mark.verifies("REQ-QMT-21", "DSN-QMT-15")
@pytest.mark.parametrize(
    ("method", "links"),
    [
        ("NoDisplayName_Runs", ()),
        ("RawString_Runs", ("TC-BAG-90.5",)),
        ("VerbatimString_Runs", ("TC-BAG-90.6",)),
        ("Skipped_IsNotRun", ("TC-BAG-90.7",)),
        ("Async_Runs", ("TC-BAG-90.8",)),
        ("WithTrait_Runs", ("TC-BAG-90.9",)),
        ("FullyQualified_Runs", ("TC-BAG-90.10",)),
        ("MemberData_Runs", ("TC-BAG-90.11",)),
        ("OneRowFails", ("TC-BAG-90.12",)),
        ("Nested_Runs", ("TC-BAG-90.16",)),
        ("Inherited_Runs", ("TC-BAG-90.17",)),
        ("ConstConcatenation_Runs", ()),
        ("ConstInterpolation_Runs", ()),
    ],
)
def test_each_probe_shape_is_an_automated_test_with_the_link_it_states(
    agent: TraceConfig, method: str, links: tuple[str, ...]
) -> None:
    linked, _ = shapes(agent)
    assert linked[method] == links


@pytest.mark.verifies("REQ-QMT-21")
@pytest.mark.parametrize("method", ["CustomAttribute_Runs", "CompiledOut", "CommentedOut"])
def test_these_probes_are_no_automated_test(agent: TraceConfig, method: str) -> None:
    linked, _ = shapes(agent)
    assert method not in linked


@pytest.mark.verifies("REQ-QMT-21", "DSN-QMT-15")
def test_nothing_is_dropped_silently(agent: TraceConfig) -> None:
    _, found = shapes(agent)
    unread = sorted(f.what.split(" — ")[0] for f in found.findings if f.code == "V15")
    assert unread == sorted(
        [
            "a 'verifies' marker given a DisplayName that is not a string literal",
            "a 'verifies' marker given a DisplayName that is not a string literal",
            "a 'verifies' marker written as a [Trait], which never reaches a test report",
            "a 'verifies' marker on [SlowFact], a test attribute this tool does not read",
            "a 'verifies' marker on a test inside conditional compilation (#if)",
        ]
    )
    assert all("[Fact(DisplayName" in f.next_move for f in found.findings if f.code == "V15")
    (stray,) = found.strays
    assert (stray.targets, stray.kind) == (("TC-BAG-90.15",), "comment")


@pytest.mark.verifies("REQ-QMT-21", "DSN-QMT-15")
def test_an_unread_marker_names_the_one_test_it_was_meant_for(agent: TraceConfig) -> None:
    """A test file holds many tests, so a finding about one must not be read as the reason
    for another's gap — even where no item is made of the method it is about."""
    _, found = shapes(agent)
    meant = sorted(f.item.rsplit("::", 1)[-1] for f in found.findings if f.code == "V15" and f.item)
    assert meant == [
        "CompiledOut",
        "ConstConcatenation_Runs",
        "ConstInterpolation_Runs",
        "CustomAttribute_Runs",
        "WithTrait_Runs",
    ]
    # A commented-out attribute was written for the method below it.
    (stray,) = found.strays
    assert stray.item == "tests/Agent.Probe/Shapes.cs::Shapes::CommentedOut"
    (alone,) = read_tests(agent, '// [Fact(DisplayName = "TC-SVC-01.1 x")]\n').strays
    assert alone.item is not None and "::" in alone.item  # no method below: no item's


@pytest.mark.verifies("REQ-QMT-21", "DSN-QMT-15")
def test_a_runs_identity_is_its_class_and_method(agent: TraceConfig) -> None:
    _, found = shapes(agent)
    by_title = {item.title: item for item in found.items}
    assert by_title["RawString_Runs"].runs_as == (("Agent.Probe.Shapes", "RawString_Runs"),)
    assert by_title["Nested_Runs"].runs_as == (("Agent.Probe.Shapes+Nested", "Nested_Runs"),)
    assert by_title["Nested_Runs"].id == "tests/Agent.Probe/Shapes.cs::Shapes::Nested::Nested_Runs"
    assert by_title["Inherited_Runs"].runs_as == (
        ("Agent.Probe.FirstDerived", "Inherited_Runs"),
        ("Agent.Probe.SecondDerived", "Inherited_Runs"),
    )
    (block,) = read_tests(agent, BLOCK, "tests/Agent.Probe/BlockNamespace.cs").items
    assert block.runs_as == (("Agent.Probe.Blocks.InABlockNamespace", "Block_Runs"),)


@pytest.mark.verifies("REQ-QMT-21")
def test_the_agents_tests_read_whole_at_their_level(agent: TraceConfig) -> None:
    path = "tests/Agent.Tests/Unit/KeyCheckTests.cs"
    found = read_tests(agent, (AGENT / path).read_text(encoding="utf-8"), path)
    assert [(i.id.rsplit("::", 1)[-1], i.level) for i in found.items] == [
        ("Admits_NoKey_IsFalse", "unit"),
        ("Admits_AnyKey_DecidesAlone", "unit"),
    ]
    assert [link.dst for link in found.links] == ["TC-SVC-01.1", "TC-SVC-01.2"]
    assert found.findings == ()


@pytest.mark.verifies("REQ-QMT-21")
@pytest.mark.parametrize(
    ("display", "link"),
    [
        ("TC-SVC-01.1 refused", "TC-SVC-01.1"),
        ("TC-SVC-01.1/O03 refused", "TC-SVC-01.1"),
        ("TC-SVC-01.1-01/O03 refused", "TC-SVC-01.1-01"),
        ("TC-SVC-01.1a refused", None),
        ("TC-SVC-01.1.2x refused", None),
        ("TC-SVC-01.1: refused", "TC-SVC-01.1"),
        ("REQ-SVC-01—x", "REQ-SVC-01"),
        # a test carries one link: a second ID is prose, as it is after a space
        ("TC-SVC-01.1/TC-SVC-01.2 refused", "TC-SVC-01.1"),
    ],
)
def test_the_leading_id_ends_where_an_id_in_prose_ends(
    agent: TraceConfig, display: str, link: str | None
) -> None:
    text = (
        f'public class T\n{{\n    [Fact(DisplayName = "{display}")]\n'
        "    public void M() { }\n}\n"
    )
    found = read_tests(agent, text, "tests/Agent.Tests/Unit/TTests.cs")
    if link is not None:
        assert [found_link.dst for found_link in found.links] == [link]
        assert found.findings == ()
        return
    assert found.links == ()
    assert [f.code for f in found.findings] == ["V14"]
    # its next move names the DisplayName, never a field line C# does not have
    assert "start the test's DisplayName with one whole ID" in found.findings[0].next_move
    assert "'/' or ':' may follow the ID directly" in found.findings[0].next_move
    assert "line" not in found.findings[0].next_move


@pytest.mark.verifies("REQ-QMT-21")
def test_a_commented_out_test_whose_id_carries_a_suffix_is_a_stray(agent: TraceConfig) -> None:
    (stray,) = read_tests(agent, '// [Fact(DisplayName = "TC-SVC-01.1/O03 x")]\n').strays
    assert (stray.targets, stray.kind) == (("TC-SVC-01.1",), "comment")


# ── 5. syntax the grammar does not read ────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-21")
def test_newer_syntax_outside_what_is_read_leaves_the_file_readable(agent: TraceConfig) -> None:
    text = (
        "namespace Probe;\n\npublic static class Extensions\n{\n    extension(string text)\n    {\n"
        "        public bool IsBlank => string.IsNullOrWhiteSpace(text);\n    }\n}\n\n"
        'public class Tests\n{\n    [Fact(DisplayName = "TC-SVC-01.1 still read")]\n'
        "    public void StillRead() { }\n}\n"
    )
    found = read_tests(agent, text, "tests/Agent.Tests/Unit/ModernTests.cs")
    assert [link.dst for link in found.links] == ["TC-SVC-01.1"]
    assert not [f for f in found.findings if f.code == "V08"]


@pytest.mark.verifies("REQ-QMT-21")
def test_a_parse_error_inside_a_test_is_v08(agent: TraceConfig) -> None:
    text = (
        'public class T\n{\n    [Fact(DisplayName = "TC-SVC-01.1 x"\n    public void M() { }\n}\n'
    )
    found = read_tests(agent, text, "tests/Agent.Tests/Unit/TTests.cs")
    assert [f.code for f in found.findings] == ["V08"] and found.items == ()


# ── 6. configuration ───────────────────────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-21", "DSN-QMT-03")
def test_a_type_read_by_xunit_carries_exactly_one_link() -> None:
    local = (AGENT / "qmstrace.toml").read_text(encoding="utf-8")
    two = SCHEMA.replace(
        'Assumes    = { from = ["requirement", "design_element"]',
        'Assumes    = { from = ["requirement", "design_element", "automated_test"]',
    )
    assert two != SCHEMA
    with pytest.raises(CouldNotJudge) as caught:
        TraceConfig.parse(local, two)
    assert "names no link of its own" in caught.value.what
    assert "2 links to choose from (verifies, Assumes)" in caught.value.what


@pytest.mark.verifies("REQ-QMT-21")
def test_a_whole_test_class_inside_if_is_reported_not_read(agent: TraceConfig) -> None:
    text = (
        '#if NEVER\npublic class T\n{\n    [Fact(DisplayName = "TC-SVC-01.1 x")]\n'
        "    public void M() { }\n}\n#endif\n"
    )
    found = read_tests(agent, text, "tests/Agent.Tests/Unit/TTests.cs")
    assert found.items == ()
    assert [f.code for f in found.findings] == ["V15"]


@pytest.mark.verifies("REQ-QMT-21")
@pytest.mark.parametrize("base", ["Base<int>", "Probe.Base", "global::Probe.Base"])
def test_a_generic_or_qualified_base_still_names_its_subclasses_runs(
    agent: TraceConfig, base: str
) -> None:
    text = (
        "namespace Probe;\n\npublic abstract class Base\n{\n"
        '    [Fact(DisplayName = "TC-SVC-01.1 inherited")]\n    public void M() { }\n}\n\n'
        f"public class Derived : {base} {{ }}\n"
    )
    (item,) = read_tests(agent, text, "tests/Agent.Tests/Unit/DerivedTests.cs").items
    assert item.runs_as == (("Probe.Derived", "M"),)


def test_an_empty_file_and_a_broken_one(agent: TraceConfig) -> None:
    assert files(agent, "  \n") == Extracted()
    broken = files(agent, "/// Implements: DSN-SVC-01\npublic class K {\n    [Fact(\n}\n")
    assert [f.code for f in broken.findings] == ["V08"] and broken.items == ()


# ── 7. a file with no type to document — #64 (ADR-0007) ────────────────────────────────────

RAZOR = "src/Admin/Clients.razor"


@pytest.mark.verifies("REQ-QMT-21", "DSN-QMT-15")
@pytest.mark.parametrize(
    "text",
    [
        '@* Implements: DSN-SVC-01 *@\n@page "/clients"\n<h1>Clients</h1>\n',
        '@page "/clients"\n@using App.Data\n@* Implements: DSN-SVC-01 *@\n\n<h1>Clients</h1>\n',
        '@*\n  Implements: DSN-SVC-01\n*@\n@page "/clients"\n<h1>Clients</h1>\n',
        '@page "/clients"\n@* <summary>Implements: DSN-SVC-01</summary> *@\n<h1>C</h1>\n',
    ],
    ids=["before the directives", "after them", "spanning lines", "with xml around it"],
)
def test_a_razor_page_links_through_the_comment_at_its_head(agent: TraceConfig, text: str) -> None:
    found = files(agent, text, path=RAZOR)
    assert [link.dst for link in found.links] == ["DSN-SVC-01"]
    assert found.items[0].id == RAZOR and found.items[0].title == "Clients"
    assert found.strays == () and found.findings == ()


@pytest.mark.verifies("REQ-QMT-21")
@pytest.mark.parametrize(
    ("text", "line"),
    [
        ('@page "/c"\n<h1>C</h1>\n@* Implements: DSN-SVC-01 *@\n', 3),
        ('@page "/c"\n@code {\n@* Implements: DSN-SVC-01 *@\n}\n', 3),
        ('/// Implements: DSN-SVC-01\n@page "/c"\n<h1>C</h1>\n', 1),
    ],
    ids=["below the head", "inside the code block", "written as a C# comment"],
)
def test_a_razor_marker_that_is_not_read_is_a_stray(
    agent: TraceConfig, text: str, line: int
) -> None:
    found = files(agent, text, path=RAZOR)
    assert found.links == ()
    assert [(s.marker, s.targets, s.line, s.kind) for s in found.strays] == [
        ("Implements", ("DSN-SVC-01",), line, "razor")
    ]


@pytest.mark.verifies("REQ-QMT-21")
def test_a_razor_page_is_never_handed_to_the_csharp_parser(agent: TraceConfig) -> None:
    # Markup put a `///` field line inside an error span, which made the whole file V08.
    found = files(agent, '/// Implements: DSN-SVC-01\n<MyComp Value="1" />\n', path=RAZOR)
    assert found.findings == () and len(found.items) == 1
    bare = files(agent, '@page "/c"\n<h1>C</h1>\n', path=RAZOR)
    assert bare.links == () and bare.strays == () and bare.findings == ()


@pytest.mark.verifies("REQ-QMT-21")
def test_a_razor_pages_own_copy_is_not_a_marker(agent: TraceConfig) -> None:
    found = files(agent, '@page "/c"\n<p>Implements: DSN-SVC-01 soon</p>\n', path=RAZOR)
    assert found.links == () and found.strays == ()


@pytest.mark.verifies("REQ-QMT-21", "DSN-QMT-15")
@pytest.mark.parametrize("lead", ["//", "///"], ids=["a plain comment", "a doc comment"])
def test_top_level_statements_link_through_the_comment_the_file_opens_with(
    agent: TraceConfig, lead: str
) -> None:
    text = f"{lead} Implements: DSN-SVC-01\nvar app = WebApplication.Create(args);\napp.Run();\n"
    found = files(agent, text, path="src/Agent/Program.cs")
    assert [link.dst for link in found.links] == ["DSN-SVC-01"]
    assert found.strays == () and found.findings == ()


@pytest.mark.verifies("REQ-QMT-21")
def test_a_comment_below_the_opening_block_is_still_a_stray(agent: TraceConfig) -> None:
    text = "// a header\n\nvar app = Create();\n// Implements: DSN-SVC-01\napp.Run();\n"
    found = files(agent, text, path="src/Agent/Program.cs")
    assert found.links == ()
    assert [(s.line, s.kind) for s in found.strays] == [(4, "doccomment")]


@pytest.mark.verifies("REQ-QMT-21")
def test_a_file_that_has_a_type_is_never_read_by_its_own_leading_comment(
    agent: TraceConfig,
) -> None:
    found = files(agent, "// Implements: DSN-SVC-01\npublic class K { }\n")
    assert found.links == ()
    assert [(s.line, s.kind) for s in found.strays] == [(1, "doccomment")]


@pytest.mark.verifies("REQ-QMT-21")
def test_a_razor_digest_follows_the_page_and_not_its_comments(agent: TraceConfig) -> None:
    one = files(agent, '@* Implements: DSN-SVC-01 *@\n@page "/c"\n<h1>C</h1>\n', path=RAZOR)
    two = files(agent, '@page "/c"\n@* Implements: DSN-SVC-02 *@\n\n<h1>C</h1>\n', path=RAZOR)
    assert one.items[0].digest == two.items[0].digest
    three = files(agent, '@page "/c"\n<h1>Clients</h1>\n', path=RAZOR)
    assert three.items[0].digest != one.items[0].digest
