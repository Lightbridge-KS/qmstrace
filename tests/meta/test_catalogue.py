"""The two meta-tests — what guards the stand-in's one regression structurally.

The stand-in's only regression was the one command nobody re-ran after a rewrite. So:

1. Every registered command has at least one golden output.
2. Every code in the findings catalogue has a scenario that emits it — and every scenario's code
   is in the catalogue. A code nothing emits is dead text; a finding with no catalogue entry is
   wording that lives outside the one place it may.
3. Every finding — violation or gap — ends with a next move.
"""

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import pytest

from qmstrace.core import findings
from qmstrace.core.baselines import Baseline, ChangeRequest, Register, Snapshot, Tag
from qmstrace.core.config import TraceConfig
from qmstrace.core.findings import CODES
from qmstrace.core.graph import Surroundings, TraceGraph
from qmstrace.core.judge import guard, ownership_findings, suspects
from qmstrace.core.model import Finding, Item
from qmstrace.extract.base import REGISTRY
from qmstrace.infra.globbing import matches

GOLDEN = Path(__file__).parents[1] / "cli" / "golden"


def _goldens(name: str) -> list[Path]:
    """A command's goldens: what it prints, as text — or, for a command that emits data, JSON."""
    return [*GOLDEN.glob(f"{name}-*.txt"), *GOLDEN.glob(f"{name}-*.json")]


def test_every_command_has_a_golden(commands: list[str]) -> None:
    assert commands, "no command is registered"
    missing = [name for name in commands if not _goldens(name)]
    assert not missing, f"commands with no golden output in {GOLDEN}: {missing}"


def test_every_verb_of_a_group_has_a_golden(subcommands: dict[str, list[str]]) -> None:
    missing = [
        f"{group} {verb}"
        for group, verbs in subcommands.items()
        for verb in verbs
        if not _goldens(f"{group}-{verb}")
    ]
    assert not missing, f"verbs with no golden output in {GOLDEN}: {missing}"


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
    "S01": lambda c: suspect_scenario(c),
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
    **{
        code: (lambda c, code=code: guard_scenario(c, code))
        for code in ("V10", "V11", "V12", "V13")
    },
    "V14": lambda c: found(c, {SRS: REQ.replace("AGR-1", "TBD")}),
    "V15": lambda c: found(c, {TESTS: 'pytestmark = pytest.mark.verifies("REQ-SVC-01")\n'}),
    "V16": lambda c: found(c, {SRS: REQ + "\n| REQ-SVC-12 | a planned requirement |\n"}),
    "V17": lambda c: list(
        ownership_findings(
            c,
            tuple(
                replace(item, id="REQ-03")
                for item in REGISTRY["markdown"](SRS, REQ, c.item_types["requirement"], c).items
            ),
        )
    ),
}


def guard_scenario(config: TraceConfig, code: str) -> list[Finding]:
    before = REGISTRY["markdown"](SRS, REQ, config.item_types["requirement"], config).items
    after_text = REQ + "Reworded.\n" + ("- Change: CR-001\n" if code != "V10" else "")
    after = REGISTRY["markdown"](SRS, after_text, config.item_types["requirement"], config).items
    baseline = Baseline(
        "requirements",
        "service",
        ("requirement",),
        (Tag("baseline/service/requirements/1", "abc", False),),
        Snapshot("abc", config, before),
    )
    register = Register(
        available=True,
        accepted="accepted",
        requests=(
            (ChangeRequest("CR-001", "CR-001.md", "accepted", frozenset({"REQ-SVC-02"})),)
            if code == "V12"
            else ()
        ),
    )
    return list(
        guard(config, () if code == "V13" else after, (baseline,), frozenset(), register)[1]
    )


def test_every_catalogue_code_has_a_scenario_and_every_scenario_a_code() -> None:
    assert set(SCENARIOS) == set(CODES)


def suspect_scenario(config: TraceConfig) -> list[Finding]:
    from qmstrace.core.baselines import Comparison

    spec = config.item_types["requirement"]
    parts = [REGISTRY["markdown"](SRS, REQ.replace("Statement.", "Changed."), spec, config)]
    test_spec = config.item_types["automated_test"]
    tests = '@pytest.mark.verifies("REQ-SVC-01")\ndef test_x(): ...\n'
    test_part = REGISTRY["pytest"](TESTS, tests, test_spec, config)
    old, _ = TraceGraph.build(config, [REGISTRY["markdown"](SRS, REQ, spec, config), test_part])
    current, _ = TraceGraph.build(config, [*parts, test_part])
    baseline = Baseline(
        "requirements",
        "service",
        ("requirement",),
        (Tag("v1", "abc", False),),
        Snapshot("abc", config, tuple(old.items()), old),
    )
    comparison = Comparison(
        "REQ-SVC-01",
        baseline,
        old.nodes["REQ-SVC-01"].item,
        current.nodes["REQ-SVC-01"].item,
        "changed",
    )
    return [findings.suspect(s) for s in suspects(current, [comparison])]


@pytest.mark.parametrize("code", sorted(SCENARIOS))
def test_each_scenario_emits_its_code(service: TraceConfig, code: str) -> None:
    emitted = {finding.code for finding in SCENARIOS[code](service)}
    assert code in emitted, f"{code}: the scenario emitted {sorted(emitted) or 'nothing'}"


@pytest.mark.parametrize("code", sorted(SCENARIOS))
@pytest.mark.verifies("DSN-QMT-06")
def test_every_finding_says_what_to_do_next(service: TraceConfig, code: str) -> None:
    for finding in SCENARIOS[code](service):
        assert finding.what and finding.next_move.startswith(("Fix:", "Review:")), finding


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
