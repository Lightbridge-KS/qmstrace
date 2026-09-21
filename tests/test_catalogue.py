"""The two meta-tests — what guards the stand-in's one regression structurally.

The stand-in's only regression was the one command nobody re-ran after a rewrite. So:

1. Every registered command has at least one golden output.
2. Every code in the findings catalogue has a scenario that emits it — and every scenario's code
   is in the catalogue. A code nothing emits is dead text; a finding with no catalogue entry is
   wording that lives outside the one place it may.
3. Every finding — violation or gap — ends with a next move.
"""

from collections.abc import Callable
from pathlib import Path

import pytest

from qmstrace.core.config import TraceConfig
from qmstrace.core.findings import CODES
from qmstrace.core.graph import Surroundings, TraceGraph
from qmstrace.core.model import Finding, Item
from qmstrace.extract.base import REGISTRY
from qmstrace.infra.globbing import matches

GOLDEN = Path(__file__).parent / "cli" / "golden"


def test_every_command_has_a_golden(commands: list[str]) -> None:
    assert commands, "no command is registered"
    missing = [name for name in commands if not list(GOLDEN.glob(f"{name}-*.txt"))]
    assert not missing, f"commands with no golden output in {GOLDEN}: {missing}"


# ── one scenario per code — the smallest text that emits it ────────────────────────────────

REQ = "### REQ-SVC-01 — X\nStatement.\n- Category: security\n- Origin: AGR-1\n- Verify-by: test\n"
AGREED = Surroundings(externals={"agreement": frozenset({"AGR-1"})})


def found(
    config: TraceConfig, files: dict[str, str], *, misplaced: tuple[Item, ...] = ()
) -> list[Finding]:
    """Extract each file as the type its path is scanned for, then build the graph."""
    extracted = []
    for path, text in files.items():
        (item_type,) = [t for t in config.item_types.values() if t.files and matches(path, t.files)]
        assert item_type.extractor is not None
        extracted.append(REGISTRY[item_type.extractor](path, text, item_type, config))
    return TraceGraph.build(config, extracted, AGREED, misplaced=misplaced)[1]


SRS, TESTS = "docs/req/s-srs.md", "tests/unit/test_t.py"
Scenario = Callable[[TraceConfig], list[Finding]]
SCENARIOS: dict[str, Scenario] = {
    "V01": lambda c: found(c, {SRS: REQ + "\n" + REQ}),
    "V02": lambda c: found(c, {SRS: REQ + "\n### REQ-SVC-1 — Short\n"}),
    "V03": lambda c: found(c, {TESTS: '@pytest.mark.verifies("REQ-SVC-09")\ndef test_x(): ...\n'}),
    "V04": lambda c: found(c, {SRS: REQ + "- Satisfies: REQ-SVC-01\n"}),
    "V05": lambda c: found(c, {SRS: REQ.replace("- Verify-by: test\n", "")}),
    "V06": lambda c: found(c, {"tests/test_top.py": "def test_x(): ...\n"}),
    "V07": lambda c: found(
        c,
        {SRS: REQ},
        misplaced=REGISTRY["markdown"](
            "docs/notes.md", REQ.replace("01", "05"), c.item_types["requirement"], c
        ).items,
    ),
    "V08": lambda c: found(c, {TESTS: "def test_x(:\n"}),
    "V09": lambda c: found(c, {SRS: REQ.replace("AGR-1", "AGR-9")}),
    "V14": lambda c: found(c, {SRS: REQ.replace("AGR-1", "TBD")}),
    "V15": lambda c: found(c, {TESTS: 'pytestmark = pytest.mark.verifies("REQ-SVC-01")\n'}),
}


def test_every_catalogue_code_has_a_scenario_and_every_scenario_a_code() -> None:
    assert set(SCENARIOS) == set(CODES)


@pytest.mark.parametrize("code", sorted(SCENARIOS))
def test_each_scenario_emits_its_code(service: TraceConfig, code: str) -> None:
    emitted = {finding.code for finding in SCENARIOS[code](service)}
    assert code in emitted, f"{code}: the scenario emitted {sorted(emitted) or 'nothing'}"


@pytest.mark.parametrize("code", sorted(SCENARIOS))
def test_every_finding_says_what_to_do_next(service: TraceConfig, code: str) -> None:
    for finding in SCENARIOS[code](service):
        assert finding.what and finding.next_move.startswith("Fix:"), finding


def test_every_gap_says_what_to_do_next(project: Path) -> None:
    """A gap's code and text are the project's; its next move is the engine's, and never missing."""
    from qmstrace.workspace import Workspace

    gaps = [
        g
        for repo in ("service", "client")
        for g in Workspace.open(project / repo).assessment().gaps
    ]
    assert gaps, "the fixture project should leave some rule unmet"
    for gap in gaps:
        assert gap.code.startswith("G") and gap.next_move.startswith("Fix:"), gap
