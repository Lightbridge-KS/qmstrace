"""The glob matcher — one for every tree, pinned on the patterns the test bed really uses.

The load-bearing claims, each pinned by a test:

1. `**` matches zero or more whole folders, so `src/**/*.py` includes `src/app.py`.
2. `*` never crosses a folder.
3. Case counts.
"""

import pytest

from qmstrace.infra.globbing import matches

CASES = [
    ("src/app.py", "src/**/*.py", True),
    ("src/pkg/deep/app.py", "src/**/*.py", True),
    ("__init__.py", "**/__init__.py", True),
    ("src/pkg/__init__.py", "**/__init__.py", True),
    ("tests/test_x.py", "tests/**/test_*.py", True),
    ("tests/unit/test_x.py", "tests/**/test_*.py", True),
    ("tests/unit/helpers.py", "tests/**/test_*.py", False),
    ("docs/req/gateway-srs.md", "docs/req/*-srs.md", True),
    ("docs/req/old/gateway-srs.md", "docs/req/*-srs.md", False),
    ("docs/req/gateway-prd.md", "docs/req/*-srs.md", False),
    ("Docs/req/gateway-srs.md", "docs/req/*-srs.md", False),
    ("docs/design/gateway-design.md", "docs/design/*.md", True),
]


@pytest.mark.parametrize(("path", "pattern", "expected"), CASES)
def test_a_pattern_from_the_test_bed(path: str, pattern: str, expected: bool) -> None:
    assert matches(path, [pattern]) is expected


def test_any_of_several_patterns_is_enough() -> None:
    assert matches("docs/x.qmd", ["docs/*.md", "docs/*.qmd"])
    assert not matches("docs/x.txt", ["docs/*.md", "docs/*.qmd"])
    assert not matches("docs/x.md", [])
