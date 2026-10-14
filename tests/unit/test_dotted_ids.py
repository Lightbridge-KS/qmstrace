"""Dotted IDs (ADR-0002) — an ID's number may carry dotted parts, and every reader takes an ID
whole or not at all.

The load-bearing claims, each pinned by a test:

1. The one shape reads dotted IDs, and still refuses what never was an ID.
2. In running text an ID is bounded: never cut short, and a sentence's full stop is not part of
   it. On every fixture file, text without a dot reads exactly as the narrow shape read it.
3. Every reader agrees: a Markdown heading, a link field, a table row, a mention, a stray in a
   module, a pytest marker, a change request.
4. A heading that starts with a malformed ID is a lead, not prose — so a slip of this repo's
   kind is reported, naming the whole word.
5. A configuration may give a dotted prefix, and listings sort dotted numbers as numbers.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from qmstrace.core.config import TraceConfig
from qmstrace.core.graph._validation import _numbered
from qmstrace.core.model import ID_TOKEN, id_tokens
from qmstrace.extract import change_requests
from qmstrace.extract.markdown import extract as markdown
from qmstrace.extract.python import module, pytest_tests

FIXTURES = Path(__file__).parents[1] / "fixtures"
MINI = FIXTURES / "mini"
SCHEMA = (MINI / "ledger" / "qmstrace.schema.toml").read_text(encoding="utf-8")
SERVICE = (MINI / "service" / "qmstrace.toml").read_text(encoding="utf-8")
# The shape before ADR-0002, bounded as the Markdown reader bounded its mentions.
NARROW = re.compile(r"(?<![A-Za-z0-9-])([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d+)(?![A-Za-z0-9-])")


@pytest.fixture(scope="module")
def dotted() -> TraceConfig:
    """The service's configuration, with requirement and design IDs allowed a dotted part."""
    local = SERVICE.replace(r"'^REQ-SVC-\d{2}$'", r"'^REQ-SVC-\d{2}(?:\.\d+)?$'").replace(
        r"'^DSN-SVC-\d{2}$'", r"'^DSN-SVC-\d{2}(?:\.\d+)?$'"
    )
    assert local != SERVICE
    return TraceConfig.parse(local, SCHEMA)


# ── 1. the shape ───────────────────────────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-20", "DSN-QMT-04")
@pytest.mark.parametrize(
    "token",
    ["TC-SVC-04.1-01", "DSN-SVC-04.1", "TC-BAG-03.1", "REQ-SVC-1.2.3", "REQ-SVC-01", "CR-001"],
)
def test_these_read_as_ids(token: str) -> None:
    assert ID_TOKEN.fullmatch(token)


@pytest.mark.verifies("REQ-QMT-20")
@pytest.mark.parametrize(
    "token", ["TC-SVC-04.", "TC-SVC-.1", "TC-SVC-04.a", "REQ-SVC-01a", "REQ.SVC-01", "TC-SVC-04..1"]
)
def test_these_still_do_not(token: str) -> None:
    assert not ID_TOKEN.fullmatch(token)


# ── 2. running text ────────────────────────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-20", "DSN-QMT-04")
@pytest.mark.parametrize(
    ("text", "ids"),
    [
        (
            "See REQ-BAG-09. Then TC-FLT-04.1-01, TC-FLT-04.1-02 and DES-FLT-04.1.",
            ("REQ-BAG-09", "TC-FLT-04.1-01", "TC-FLT-04.1-02", "DES-FLT-04.1"),
        ),
        ("TC-BAG-03.1a is no ID, and neither is TC-BAG-03.1-", ()),
        ("x-REQ-SVC-01 and REQ-SVC-01x", ()),
        ("(TC-BAG-02.10), `TC-BAG-02.11`", ("TC-BAG-02.10", "TC-BAG-02.11")),
    ],
)
def test_an_id_in_text_is_read_whole_or_not_at_all(text: str, ids: tuple[str, ...]) -> None:
    assert id_tokens(text) == ids


@pytest.mark.verifies("REQ-QMT-20")
def test_on_every_fixture_and_golden_text_without_a_dot_reads_as_before() -> None:
    texts = [*FIXTURES.rglob("*"), *(FIXTURES.parent / "cli" / "golden").glob("*.txt")]
    files = [p for p in texts if p.is_file() and p.suffix in {".md", ".py", ".toml", ".txt"}]
    assert len(files) > 100
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert id_tokens(text) == tuple(NARROW.findall(text)), path


# ── 3. every reader agrees ─────────────────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-20", "DSN-QMT-04")
def test_a_dotted_heading_declares_its_item_whole(dotted: TraceConfig) -> None:
    text = "### REQ-SVC-04.1 — A part of four\n- Category: security\n- Origin: AGR-1\n"
    found = markdown("docs/req/service-srs.md", text, dotted.item_types["requirement"], dotted)
    assert [(i.id, i.title) for i in found.items] == [("REQ-SVC-04.1", "A part of four")]
    assert found.leads == () and found.findings == ()


@pytest.mark.verifies("REQ-QMT-20", "DSN-QMT-04")
def test_a_link_field_reads_dotted_targets_whole(dotted: TraceConfig) -> None:
    text = "## DSN-SVC-04.2 — Keys\nSatisfies: REQ-SVC-04.1, REQ-SVC-04.10\n"
    found = markdown("docs/design/keys.md", text, dotted.item_types["design_element"], dotted)
    assert [link.dst for link in found.links] == ["REQ-SVC-04.1", "REQ-SVC-04.10"]


@pytest.mark.verifies("REQ-QMT-20", "DSN-QMT-04")
def test_a_table_row_and_a_later_heading_mention_dotted_ids_whole(dotted: TraceConfig) -> None:
    text = "### Overview of REQ-SVC-04.1\n\n| REQ-SVC-04.2 | a row |\n|---|---|\n"
    found = markdown("docs/req/service-srs.md", text, dotted.item_types["requirement"], dotted)
    assert [(m.token, m.where) for m in found.mentions] == [
        ("REQ-SVC-04.1", "heading"),
        ("REQ-SVC-04.2", "row"),
    ]


@pytest.mark.verifies("REQ-QMT-20", "DSN-QMT-04")
def test_a_stray_in_a_module_names_dotted_ids_whole(dotted: TraceConfig) -> None:
    text = '"""Keys."""\n\n# Implements: DSN-SVC-04.1, DSN-SVC-04.2\n'
    found = module.extract("src/service/keys.py", text, dotted.item_types["component"], dotted)
    (stray,) = found.strays
    assert stray.targets == ("DSN-SVC-04.1", "DSN-SVC-04.2")


@pytest.mark.verifies("REQ-QMT-20", "DSN-QMT-04")
def test_a_pytest_marker_names_a_dotted_id(dotted: TraceConfig) -> None:
    text = 'import pytest\n\n@pytest.mark.verifies("REQ-SVC-04.1")\ndef test_x():\n    pass\n'
    found = pytest_tests.extract(
        "tests/unit/test_keys.py", text, dotted.item_types["test_case"], dotted
    )
    assert [link.dst for link in found.links] == ["REQ-SVC-04.1"]
    assert found.findings == ()


@pytest.mark.verifies("REQ-QMT-20")
def test_a_change_request_impacts_dotted_ids() -> None:
    text = "# CR-007 — Split four\n- State: accepted\n- Impacts: REQ-SVC-04.1, DSN-SVC-04.2\n"
    request, problem = change_requests.read("change-requests/CR-007.md", "CR-007", text)
    assert problem is None and request is not None
    assert request.impacts == frozenset({"REQ-SVC-04.1", "DSN-SVC-04.2"})


# ── 4. malformed leads ─────────────────────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-20", "DSN-QMT-04")
@pytest.mark.parametrize("word", ["REQ-SVC-04.1a", "REQ-SVC-03b", "REQ-SVC-04.1.2x"])
def test_a_heading_that_starts_with_a_malformed_id_is_a_lead(
    dotted: TraceConfig, word: str
) -> None:
    text = f"# Title\n\n### {word} — Something\n- Origin: AGR-1\n"
    found = markdown("docs/req/service-srs.md", text, dotted.item_types["requirement"], dotted)
    assert found.items == ()
    assert [(lead.token, lead.line) for lead in found.leads] == [(word, 3)]


@pytest.mark.verifies("REQ-QMT-20")
@pytest.mark.parametrize("heading", ["### Overview", "### IEC-62304 software safety class"])
def test_a_heading_that_is_not_an_id_of_any_shape_is_still_prose(
    dotted: TraceConfig, heading: str
) -> None:
    found = markdown(
        "docs/req/service-srs.md", heading + "\n", dotted.item_types["requirement"], dotted
    )
    assert found.items == () and found.findings == ()


# ── 5. configuration and listings ──────────────────────────────────────────────────────────


@pytest.mark.verifies("REQ-QMT-20", "DSN-QMT-03")
def test_a_configuration_may_give_a_dotted_prefix() -> None:
    local = SERVICE.replace(
        "[items.requirement]\n", '[items.requirement]\nid_prefix  = "REQ-SVC-04.1-"\n', 1
    ).replace(r"'^REQ-SVC-\d{2}$'", r"'^REQ-SVC-04\.1-\d{2}$'")
    config = TraceConfig.parse(local, SCHEMA)
    assert config.item_types["requirement"].id_prefix == "REQ-SVC-04.1-"


@pytest.mark.verifies("REQ-QMT-20")
def test_listings_sort_dotted_numbers_as_numbers() -> None:
    ids = ["AGR-10", "AGR-1.10", "AGR-2", "AGR-1.2", "AGR-1"]
    assert sorted(ids, key=_numbered) == ["AGR-1", "AGR-1.2", "AGR-1.10", "AGR-2", "AGR-10"]
