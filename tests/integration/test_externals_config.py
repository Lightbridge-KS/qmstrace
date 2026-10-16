"""The two `[externals.*]` misconfigurations a project met while designing one agreement per
engagement, reproduced on the `cases` fixture as the issues report them.

1. Two externals whose prefixes overlap (#55) are refused before any citation is judged, so no
   `V09` names the wrong file and invites a duplicate clause.
2. An external whose `source` is a pattern (#56) is refused, not read as a file that is not
   checked out here.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from qmstrace.cli import app

AC = "^\\s*[-*]\\s+\\*\\*(AC-\\d+)\\*\\*"


def engagements(ledger: Path, *tables: tuple[str, str]) -> None:
    """Add one external per engagement, (name, source) each, all with the prefix `AC-`, and
    have REQ-SVC-01 cite the second engagement's clause."""
    schema = ledger / "qmstrace.schema.toml"
    extra = "".join(
        f'\n[externals.{name}]\nitem_type   = "origin_clause"\nprefix      = "AC-"\n'
        f"source      = \"{source}\"\ndeclared_as = '{AC}'\n"
        for name, source in tables
    )
    text = schema.read_text(encoding="utf-8")
    schema.write_text(text.replace("\n[change_requests]", extra + "\n[change_requests]", 1))
    for number, engagement in enumerate(("eng1", "eng2"), start=1):
        (ledger / engagement).mkdir(exist_ok=True)
        (ledger / engagement / "agreement.md").write_text(f"- **AC-{number}** — a clause.\n")
    srs = ledger / "docs" / "req" / "service-srs.md"
    text = srs.read_text(encoding="utf-8")
    srs.write_text(text.replace("- Origin: AGR-1\n", "- Origin: AGR-1, AC-2\n", 1))


def ledger_check(ledger: Path) -> tuple[int, str]:
    done = CliRunner().invoke(app, ["-C", str(ledger), "ledger", "check"])
    return done.exit_code, done.output


@pytest.mark.verifies("DSN-QMT-03")
def test_two_engagements_sharing_a_prefix_are_refused_before_any_citation_is_judged(
    cases: Path,
) -> None:
    ledger = cases / "ledger"
    engagements(ledger, ("eng1", "eng1/agreement.md"), ("eng2", "eng2/agreement.md"))
    code, output = ledger_check(ledger)
    assert code == 2, output
    assert "[externals.eng1] and [externals.eng2] have the same prefix, 'AC-'" in output
    assert "V09" not in output and "declares no AC-2" not in output


@pytest.mark.verifies("DSN-QMT-03")
def test_a_pattern_source_is_refused_not_read_as_unreachable(cases: Path) -> None:
    ledger = cases / "ledger"
    engagements(ledger, ("engagements", "*/agreement.md"))
    code, output = ledger_check(ledger)
    assert code == 2, output
    assert "'externals.engagements.source' is '*/agreement.md', a pattern" in output
    assert "NOT VERIFIED" not in output
