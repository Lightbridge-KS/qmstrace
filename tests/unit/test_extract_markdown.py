"""The Markdown extractor — requirements and design elements, read from text.

The load-bearing claims, each pinned by a test:

1. A heading whose ID matches the type's pattern declares an item; its body runs to the next
   heading of any level — the test bed's `## Section` headings end an item.
2. Fields are `Key: value` lines, list bullet and bold keys tolerated; a field named after a
   link marker is a link, several targets comma-separated. Other `Key:` lines are prose.
3. A heading inside a code fence declares nothing; frontmatter is not read.
4. An item's text ignores layout and leaves the `Change:` line out; a changed link field is a
   change.
5. A link field that is not a list of IDs is reported (V14) — `Origin: TBD` never passes.
6. A heading that starts with some other ID is handed back as a lead, never dropped.
"""

import pytest

from qmstrace.core.config import TraceConfig
from qmstrace.core.model import Extracted
from qmstrace.extract.markdown import extract

SRS = """\
---
summary: The service's requirement items.
---

# Service — requirements

## Keys

### REQ-SVC-01 — A call carries a key
The service shall reject, with status 401, a call
that carries no valid key.

- Category: security
- Origin: AGR-1
- Verify-by: test
- Change: CR-001

## Storage

### REQ-SVC-02 — Records survive a restart
The service shall keep every record across a restart.

- **Category:** reliability
- **Origin**: AGR-2, AGR-3
- Verify-by: test
Note: this line is prose, not a field.
"""


def read(config: TraceConfig, text: str, item_type: str = "requirement") -> Extracted:
    return extract("docs/req/service-srs.md", text, config.item_types[item_type], config)


def digest_of(config: TraceConfig, text: str) -> str:
    (item,) = read(config, text).items
    return item.digest


# ── 1 & 2. items, their bodies, fields and links ───────────────────────────────────────────


def test_a_heading_with_a_matching_id_declares_an_item(service: TraceConfig) -> None:
    found = read(service, SRS)
    one, two = found.items
    assert (one.id, one.type, one.line, one.title) == (
        "REQ-SVC-01",
        "requirement",
        9,
        "A call carries a key",
    )
    assert one.fields == {
        "Category": "security",
        "Origin": "AGR-1",
        "Verify-by": "test",
        "Change": "CR-001",
    }
    assert (two.id, two.line) == ("REQ-SVC-02", 20)
    assert not found.findings and not found.leads


def test_a_field_named_after_a_link_marker_is_the_link(service: TraceConfig) -> None:
    links = read(service, SRS).links
    assert [(link.src, link.marker, link.dst, link.line) for link in links] == [
        ("REQ-SVC-01", "Origin", "AGR-1", 14),
        ("REQ-SVC-02", "Origin", "AGR-2", 24),
        ("REQ-SVC-02", "Origin", "AGR-3", 24),
    ]


def test_bold_keys_are_read_either_way(service: TraceConfig) -> None:
    two = read(service, SRS).items[1]
    assert two.fields["Category"] == "reliability"
    assert two.fields["Origin"] == "AGR-2, AGR-3"


def test_a_key_that_is_neither_a_field_nor_a_marker_is_prose(service: TraceConfig) -> None:
    two = read(service, SRS).items[1]
    assert "Note" not in two.fields
    with_note, without = SRS, SRS.replace("Note: this line is prose, not a field.\n", "")
    assert digest_of(service, with_note.split("## Storage")[1]) != digest_of(
        service, without.split("## Storage")[1]
    )


def test_a_section_heading_ends_the_item_before_it(service: TraceConfig) -> None:
    one = read(service, SRS).items[0]
    later = SRS.replace("## Storage\n", "## Storage\nThis paragraph belongs to no item.\n")
    assert read(service, later).items[0].digest == one.digest


def test_a_marker_under_the_wrong_kind_of_item_is_still_read(service: TraceConfig) -> None:
    """`Satisfies:` under a requirement becomes a link, so the graph can refuse it (V04)."""
    text = "### REQ-SVC-01 — X\nStatement.\n- Satisfies: REQ-SVC-02\n"
    (link,) = read(service, text).links
    assert (link.src, link.marker, link.dst) == ("REQ-SVC-01", "Satisfies", "REQ-SVC-02")


def test_a_design_element_with_a_bare_satisfies_line(service: TraceConfig) -> None:
    text = (
        "## Elements\n\n"
        "## DSN-SVC-01 — Key check\n"
        "Satisfies: REQ-SVC-01, REQ-SVC-02\n\n"
        "The check runs before any handler.\n"
    )
    found = extract(
        "docs/design/service-design.md", text, service.item_types["design_element"], service
    )
    (item,) = found.items
    assert (item.id, item.line, item.title) == ("DSN-SVC-01", 3, "Key check")
    assert [link.dst for link in found.links] == ["REQ-SVC-01", "REQ-SVC-02"]


# ── 3. fences and frontmatter ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize("fence", ["```", "~~~"])
def test_a_heading_inside_a_fence_declares_nothing(service: TraceConfig, fence: str) -> None:
    text = f"{fence}markdown\n### REQ-SVC-09 — An example\n- Origin: AGR-9\n{fence}\n"
    assert read(service, text) == Extracted()


def test_a_fence_inside_an_item_is_part_of_its_text(service: TraceConfig) -> None:
    base = "### REQ-SVC-01 — X\nStatement.\n```\n### not a heading\n- Origin: AGR-9\n```\n"
    found = read(service, base)
    assert len(found.items) == 1 and not found.links
    assert digest_of(service, base) != digest_of(service, base.replace("not a heading", "other"))


def test_frontmatter_is_not_read(service: TraceConfig) -> None:
    text = "---\ntitle: x\n---\n### REQ-SVC-01 — X\nStatement.\n"
    other = text.replace("title: x", "title: y")
    assert digest_of(service, text) == digest_of(service, other)
    # a `---` never closed is a thematic break, not frontmatter: what follows is read
    assert [item.id for item in read(service, "---\n### REQ-SVC-01 — X\n").items] == ["REQ-SVC-01"]


# ── 4. item text ───────────────────────────────────────────────────────────────────────────


ITEM = "### REQ-SVC-01 — A call carries a key\nThe service shall reject a call.\n- Origin: AGR-1\n"


def test_rewrapping_is_not_a_change(service: TraceConfig) -> None:
    wrapped = ITEM.replace("shall reject a call.", "shall reject\n  a call.")
    assert digest_of(service, ITEM) == digest_of(service, wrapped)


@pytest.mark.parametrize(
    "change", ["- Change: CR-001", "- **Change:** CR-001", "Change: CR-001, CR-002"]
)
def test_citing_a_change_request_is_not_a_change(service: TraceConfig, change: str) -> None:
    assert digest_of(service, ITEM) == digest_of(service, ITEM + change + "\n")


def test_an_origin_gaining_a_clause_is_a_change(service: TraceConfig) -> None:
    assert digest_of(service, ITEM) != digest_of(service, ITEM.replace("AGR-1", "AGR-1, AGR-2"))


def test_rewording_the_title_is_a_change(service: TraceConfig) -> None:
    assert digest_of(service, ITEM) != digest_of(service, ITEM.replace("carries", "holds"))


# ── 5. a link field that links nothing ─────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("value", "links", "said"),
    [
        ("TBD", [], "'TBD' is not an ID"),
        ("AGR-1, AGR-X", ["AGR-1"], "'AGR-X' is not an ID"),
        ("", [], "the line names no ID"),
    ],
)
def test_a_link_field_that_is_not_a_list_of_ids_is_v14(
    service: TraceConfig, value: str, links: list[str], said: str
) -> None:
    found = read(service, f"### REQ-SVC-01 — X\n- Origin: {value}\n")
    assert [link.dst for link in found.links] == links
    (finding,) = found.findings
    assert (finding.code, finding.line, finding.item) == ("V14", 2, "REQ-SVC-01")
    assert said in finding.what
    assert "never invent" in finding.next_move


# ── 6. leads ───────────────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("token", ["REQ-SVC-1", "REQ-CLT-01", "DSN-SVC-01", "REQ-SCV-01"])
def test_a_heading_with_another_id_is_a_lead(service: TraceConfig, token: str) -> None:
    found = read(service, f"# Title\n\n### {token} — Something\n- Origin: AGR-1\n")
    assert found.items == () and found.links == ()
    (lead,) = found.leads
    assert (lead.token, lead.item_type, lead.line) == (token, "requirement", 3)


@pytest.mark.parametrize("heading", ["### Overview", "### REQ-BCN-NN — a placeholder", "#hashtag"])
def test_a_heading_with_no_id_is_prose(service: TraceConfig, heading: str) -> None:
    assert read(service, heading + "\n") == Extracted()
