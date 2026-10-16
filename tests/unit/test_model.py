"""Item text and IDs — what a baseline will freeze, so it is pinned before anything digests it.

The load-bearing claims, each pinned by a test:

1. Layout is not a change: re-wrapping, other line endings, and another Unicode normal form
   give the same digest. Rewording does not.
2. A digest names its algorithm.
3. One generic pattern says what reads as an ID at all; a placeholder does not.
4. Qualified for the whole project, a derived ID carries its repo and every location is written
   from the ledger; an authored ID and a link's target are never touched.
"""

import unicodedata

import pytest

from qmstrace.core.model import (
    ID_TOKEN,
    Extracted,
    Finding,
    Item,
    Link,
    Stray,
    id_order,
    text_digest,
)


def test_rewrapping_a_paragraph_is_not_a_change() -> None:
    one = "The gateway shall reject a request\nthat carries no key."
    two = "The gateway shall reject a request that carries\n   no key."
    assert text_digest(one) == text_digest(two)


def test_other_line_endings_are_not_a_change() -> None:
    assert text_digest("a\nb\n") == text_digest("a\r\nb\r\n")


def test_another_unicode_normal_form_is_not_a_change() -> None:
    word = "café — naïve"
    assert text_digest(unicodedata.normalize("NFD", word)) == text_digest(word)


def test_rewording_is_a_change() -> None:
    assert text_digest("shall reject") != text_digest("shall refuse")


def test_a_digest_names_its_algorithm() -> None:
    digest = text_digest("x")
    assert digest.startswith("sha256:")
    assert len(digest) == len("sha256:") + 64


@pytest.mark.parametrize("token", ["REQ-SVC-01", "DSN-BCN-08", "AGR-3", "CR-001", "REQ-A1-2"])
def test_these_read_as_ids(token: str) -> None:
    assert ID_TOKEN.fullmatch(token)


@pytest.mark.parametrize("token", ["REQ-BCN-NN", "TBD", "G02", "req-svc-01", "REQ-"])
def test_these_do_not(token: str) -> None:
    assert not ID_TOKEN.fullmatch(token)


# ── 4. qualified for the whole project ─────────────────────────────────────────────────────


@pytest.mark.verifies("DSN-QMT-14")
def test_a_derived_id_carries_its_repo_and_an_authored_one_does_not() -> None:
    test = "tests/unit/test_api.py::test_x"
    part = Extracted(
        items=(
            Item(test, "test_case", "tests/unit/test_api.py", 4, "x", "d"),
            Item("REQ-SVC-01", "requirement", "docs/req/srs.md", 3, "r", "d"),
        ),
        links=(Link(test, "REQ-SVC-01", "verifies", "tests/unit/test_api.py", 3),),
        findings=(Finding("V06", "tests/unit/test_api.py", 4, "w", "n", test),),
        strays=(Stray("verifies", ("REQ-SVC-01",), "tests/unit/test_api.py", 9, item=test),),
    )
    seen = part.qualified("client", "../client", frozenset({"test_case"}))
    assert [i.id for i in seen.items] == [f"client:{test}", "REQ-SVC-01"]
    assert {i.file for i in seen.items} == {
        "../client/tests/unit/test_api.py",
        "../client/docs/req/srs.md",
    }
    assert (seen.links[0].src, seen.links[0].dst) == (f"client:{test}", "REQ-SVC-01")
    assert (seen.findings[0].item, seen.findings[0].file) == (
        f"client:{test}",
        "../client/tests/unit/test_api.py",
    )
    assert seen.strays[0].item == f"client:{test}"


def test_the_ledger_itself_keeps_its_paths_as_they_are() -> None:
    part = Extracted(items=(Item("REQ-SVC-01", "requirement", "docs/req/srs.md", 3, "r", "d"),))
    assert part.qualified("ledger", ".", frozenset()).items[0].file == "docs/req/srs.md"


@pytest.mark.verifies("DSN-QMT-16")
def test_ids_sort_with_their_numbers_read_as_numbers() -> None:
    ids = ["AGR-10", "TC-4.10", "REQ-SVC-10", "agent:tests/b.py", "AGR-2", "TC-4.2", "REQ-SVC-02"]
    assert sorted(ids, key=id_order) == [
        "AGR-2",
        "AGR-10",
        "REQ-SVC-02",
        "REQ-SVC-10",
        "TC-4.2",
        "TC-4.10",
        "agent:tests/b.py",
    ]
