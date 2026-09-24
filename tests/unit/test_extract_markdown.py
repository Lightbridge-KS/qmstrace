"""The Markdown extractor — requirements and design elements, read from text.

The load-bearing claims, each pinned by a test:

1. A heading whose ID matches the type's pattern declares an item; the item is its section,
   down to the next heading at the same or a higher level. Only this repo's IDs end it.
2. Fields are `Key: value` lines, list bullet and bold keys tolerated; a field named after a
   link marker is a link, several targets comma-separated. Other `Key:` lines are prose.
3. A heading inside a code fence declares nothing; frontmatter is not read.
4. An item's text ignores layout and leaves the `Change:` line out; a changed link field is a
   change.
5. A link field that is not a list of IDs is reported (V14) — `Origin: TBD` never passes.
6. A heading that starts with some other ID is handed back as a lead, never dropped.
7. What the fixture project declares today keeps its titles and digests; a fence closes on
   its own mark.
8. A sub-section is part of its item: its text, its fields and its links.
9. A section number, emphasis or backticks around the ID and a trailing Pandoc attribute are
   layout: the heading still declares, and restyling or renumbering is not a change.
"""

from pathlib import Path

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


# ── 7. what the fixture project declares today, pinned before any rule changes ────────────

MINI = Path(__file__).parents[1] / "fixtures" / "mini"
SCHEMA_TEXT = (MINI / "ledger" / "qmstrace.schema.toml").read_text(encoding="utf-8")

# An item with no sub-heading and no decorated heading keeps its title and digest across
# every change to the reading rules — a baseline cut before a change must stay comparable.
PINNED = [
    (
        "service",
        "docs/req/service-srs.md",
        "requirement",
        "REQ-SVC-01",
        12,
        "A call carries a key",
        "sha256:2ebbd8cf2f7080afe6caf92bd49edd046483f8b3d215748a73371802a36a5347",
    ),
    (
        "service",
        "docs/req/service-srs.md",
        "requirement",
        "REQ-SVC-02",
        21,
        "Records survive a restart",
        "sha256:41b1d2452671a501369cb6341d904159c2330f553546ed9e43aa95fbff1ba0c8",
    ),
    (
        "service",
        "docs/req/service-srs.md",
        "requirement",
        "REQ-SVC-03",
        28,
        "The record format is written down",
        "sha256:4518974cafc1dde2714cf2abe1fb422d0086996f72edd360d9f063a7a910653b",
    ),
    (
        "service",
        "docs/design/service-design.md",
        "design_element",
        "DSN-SVC-01",
        8,
        "Key check",
        "sha256:68cc4e200c84985560cb087d18749db5bfd8abc8533de46513f2ad51b0b1dd49",
    ),
    (
        "service",
        "docs/design/service-design.md",
        "design_element",
        "DSN-SVC-02",
        13,
        "Record store",
        "sha256:1a3097d190e25774acafdf633877a9caa7d54014d068da878cec58619dc382f5",
    ),
    (
        "client",
        "docs/req/client-srs.md",
        "requirement",
        "REQ-CLT-01",
        3,
        "The client sends its key on every call",
        "sha256:cdcb9b6b79c5dd6cd33bb8c604dc8c56919121efbdb40140c331c3f95920669c",
    ),
    (
        "solo",
        "docs/req/app-srs.md",
        "requirement",
        "REQ-APP-01",
        3,
        "A greeting",
        "sha256:af5bdede9072ddd82920cb17ee815b697a3f6e6c2701175f7be60f0a276636b2",
    ),
]


def _config(repo: str) -> TraceConfig:
    local = (MINI / repo / "qmstrace.toml").read_text(encoding="utf-8")
    return TraceConfig.parse(local) if repo == "solo" else TraceConfig.parse(local, SCHEMA_TEXT)


@pytest.mark.parametrize(("repo", "path", "item_type"), sorted({p[:3] for p in PINNED}))
def test_the_fixture_projects_items_keep_their_titles_and_digests(
    repo: str, path: str, item_type: str
) -> None:
    config = _config(repo)
    text = (MINI / repo / path).read_text(encoding="utf-8")
    found = extract(path, text, config.item_types[item_type], config)
    expected = [p[3:] for p in PINNED if p[:3] == (repo, path, item_type)]
    assert [(i.id, i.line, i.title, i.digest) for i in found.items] == expected
    assert not found.findings and not found.leads


@pytest.mark.parametrize(
    ("opener", "closer"), [("```", "```"), ("~~~", "~~~"), ("```python", "```")]
)
def test_a_fence_closes_on_its_own_mark(service: TraceConfig, opener: str, closer: str) -> None:
    other = "~~~" if closer == "```" else "```"
    text = f"{opener}\n{other}\n### REQ-SVC-09 — hidden\n{closer}\n### REQ-SVC-01 — X\n"
    assert [item.id for item in read(service, text).items] == ["REQ-SVC-01"]


def test_a_longer_fence_holds_a_fenced_example(service: TraceConfig) -> None:
    """A skill or a how-to shows a design doc with its Mermaid block inside a longer fence."""
    text = (
        "````markdown\n```mermaid\nflowchart LR\n```\n### REQ-SVC-09 — an example\n````\n"
        "### REQ-SVC-01 — X\n"
    )
    assert [item.id for item in read(service, text).items] == ["REQ-SVC-01"]


def test_a_line_with_an_info_string_does_not_close_a_fence(service: TraceConfig) -> None:
    text = "```\n```python\n### REQ-SVC-09 — an example\n```\n### REQ-SVC-01 — X\n"
    assert [item.id for item in read(service, text).items] == ["REQ-SVC-01"]


# ── 8. an item is a section ────────────────────────────────────────────────────────────────

SECTIONED = """\
### REQ-SVC-01 — A call carries a key
The service shall reject a call that carries no key.

#### Acceptance criteria
- A call with no key gets status 401.

#### Traceability
- Origin: AGR-1
- Category: security

### REQ-SVC-02 — Records survive a restart
The service shall keep every record across a restart.
"""


def test_a_deeper_heading_keeps_the_item_open(service: TraceConfig) -> None:
    found = read(service, SECTIONED)
    one, _ = found.items
    assert one.fields == {"Origin": "AGR-1", "Category": "security"}
    assert [(link.src, link.dst, link.line) for link in found.links] == [("REQ-SVC-01", "AGR-1", 8)]


def test_an_edit_under_a_sub_heading_is_a_change(service: TraceConfig) -> None:
    edited = SECTIONED.replace("gets status 401", "gets status 403")
    assert read(service, SECTIONED).items[0].digest != read(service, edited).items[0].digest
    assert read(service, SECTIONED).items[1].digest == read(service, edited).items[1].digest


def test_a_sub_heading_enters_the_text_without_its_marks(service: TraceConfig) -> None:
    deeper = SECTIONED.replace("#### Acceptance criteria", "##### Acceptance criteria")
    assert read(service, SECTIONED).items[0].digest == read(service, deeper).items[0].digest
    renamed = SECTIONED.replace("#### Acceptance criteria", "#### Criteria")
    assert read(service, SECTIONED).items[0].digest != read(service, renamed).items[0].digest


@pytest.mark.parametrize("heading", ["### Notes", "## Notes", "# Notes"])
def test_a_plain_heading_at_the_items_level_or_higher_ends_it(
    service: TraceConfig, heading: str
) -> None:
    text = f"### REQ-SVC-01 — X\nStatement.\n{heading}\n- Origin: AGR-9\n"
    found = read(service, text)
    assert [item.id for item in found.items] == ["REQ-SVC-01"] and not found.links


def test_an_id_shaped_word_of_no_kind_here_is_a_sub_heading(service: TraceConfig) -> None:
    """`IEC-62304` has an ID's shape, but this repo declares nothing like it."""
    text = "### REQ-SVC-01 — X\nStatement.\n#### IEC-62304 software safety class\n- Origin: AGR-1\n"
    found = read(service, text)
    (item,) = found.items
    assert item.fields == {"Origin": "AGR-1"} and len(found.links) == 1


@pytest.mark.parametrize("token", ["REQ-CLT-01", "DSN-SVC-01", "REQ-SVC-1"])
def test_a_heading_with_this_repos_kind_of_id_ends_the_item(
    service: TraceConfig, token: str
) -> None:
    text = f"### REQ-SVC-01 — X\nStatement.\n#### {token} — Other\n- Origin: AGR-9\n"
    found = read(service, text)
    assert [item.id for item in found.items] == ["REQ-SVC-01"] and not found.links
    assert [lead.token for lead in found.leads] == [token]


def test_items_never_nest(service: TraceConfig) -> None:
    text = "## REQ-SVC-01 — X\nOne.\n### REQ-SVC-02 — Y\n- Origin: AGR-2\n"
    one, two = read(service, text).items
    assert (one.fields, two.fields) == ({}, {"Origin": "AGR-2"})


def test_a_second_change_line_names_the_first(service: TraceConfig) -> None:
    text = "### REQ-SVC-01 — X\n- Change: CR-001\n#### Change history\n- Change: CR-002\n"
    (finding,) = read(service, text).findings
    assert (finding.code, finding.line) == ("V08", 4)
    assert "a second Change field for REQ-SVC-01 (the first is at line 2)" in finding.what


def test_a_marker_in_a_sub_section_is_read_even_when_the_type_does_not_carry_it(
    service: TraceConfig,
) -> None:
    """The graph refuses it (V04) — a sub-section is part of the item, not a hiding place."""
    text = "### REQ-SVC-01 — X\nStatement.\n#### Design\nSatisfies: REQ-SVC-02\n"
    (link,) = read(service, text).links
    assert (link.src, link.marker, link.dst) == ("REQ-SVC-01", "Satisfies", "REQ-SVC-02")


# ── 9. heading forms ───────────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "heading",
    [
        "### REQ-SVC-01 — T",
        "### 4.2 REQ-SVC-01 — T",
        "### 4.2.1. REQ-SVC-01 — T",
        "### § 4.2 REQ-SVC-01 — T",
        "### **REQ-SVC-01** — T",
        "### **REQ-SVC-01 — T**",
        "### __REQ-SVC-01__ — T",
        "### *REQ-SVC-01* — T",
        "### _REQ-SVC-01_ — T",
        "### `REQ-SVC-01` — T",
        "### REQ-SVC-01 — T {#sec-t}",
        "### REQ-SVC-01 — T {.unnumbered}",
        "### REQ-SVC-01 — T {-}",
        "### 4.2 **REQ-SVC-01** — T {#sec-t .unnumbered}",
    ],
)
def test_a_decorated_heading_declares_the_item(service: TraceConfig, heading: str) -> None:
    found = read(service, f"# Doc\n\n{heading}\nStatement.\n- Origin: AGR-1\n")
    (item,) = found.items
    assert (item.id, item.line, item.title) == ("REQ-SVC-01", 3, "T")
    assert [link.dst for link in found.links] == ["AGR-1"] and not found.leads


def test_renumbering_or_restyling_a_heading_is_not_a_change(service: TraceConfig) -> None:
    plain = "### REQ-SVC-01 — T\nStatement.\n"
    styled = "### 4.3 **REQ-SVC-01** — T {#sec-t}\nStatement.\n"
    assert digest_of(service, plain) == digest_of(service, styled)


def test_a_sub_heading_numbered_under_the_item_is_renumbered_freely(
    service: TraceConfig,
) -> None:
    before = "### 4.2 REQ-SVC-01 — T\nS.\n#### 4.2.1 Flow {#flow}\nX.\n"
    after = "### 4.3 REQ-SVC-01 — T\nS.\n#### 4.3.1 Flow\nX.\n"
    assert digest_of(service, before) == digest_of(service, after)


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("#### 404 when unknown", "#### 410 when unknown"),
        ("#### 1. Happy path", "#### 2. Happy path"),
        ("#### 4.2.1 Flow", "#### 5.2.1 Flow"),
    ],
)
def test_any_other_sub_heading_number_is_text(
    service: TraceConfig, before: str, after: str
) -> None:
    item = "### 4.2 REQ-SVC-01 — T\nS.\n{}\nX.\n"
    assert digest_of(service, item.format(before)) != digest_of(service, item.format(after))


@pytest.mark.parametrize(
    "heading",
    ["### Calls need a key (REQ-SVC-01)", "## 2024 roadmap", "### 4.2 Overview {#overview}"],
)
def test_a_heading_that_does_not_start_with_an_id_declares_nothing(
    service: TraceConfig, heading: str
) -> None:
    assert read(service, heading + "\n- Origin: AGR-1\n") == Extracted()
