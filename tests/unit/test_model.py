"""Item text and IDs — what a baseline will freeze, so it is pinned before anything digests it.

The load-bearing claims, each pinned by a test:

1. Layout is not a change: re-wrapping, other line endings, and another Unicode normal form
   give the same digest. Rewording does not.
2. A digest names its algorithm.
3. One generic pattern says what reads as an ID at all; a placeholder does not.
"""

import unicodedata

import pytest

from qmstrace.core.model import ID_TOKEN, text_digest


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
