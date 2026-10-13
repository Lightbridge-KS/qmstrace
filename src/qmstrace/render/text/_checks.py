"""Local and ledger check findings, quiet notices and result lines.

Implements: DSN-QMT-12
"""

from __future__ import annotations

from collections import Counter
from typing import Final

from qmstrace.core import findings
from qmstrace.core.assessment import Assessment, ProjectAssessment
from qmstrace.core.baselines import Suspect
from qmstrace.core.model import Finding
from qmstrace.render._evidence import (
    _baseline_lines,
    _baselines,
    _change_counts,
    _external,
    _unread,
)
from qmstrace.render._presentation import _finding, _noun

VIOLATION_HEADING: Final = "violations — wrong at any stage; each fails the check:"


PROJECT_GAP_HEADING: Final = (
    "gaps — coverage not met yet; only the gate (qmstrace ledger check --strict) fails on them"
)


def check(assessment: Assessment, *, strict: bool, quiet: bool) -> str:
    """Every violation and gap, one line each with its next move, and a result line that says
    what this run could not see — the one line a pipeline or an agent may read alone."""
    notices = _notices(assessment)
    lines: list[str] = []
    if not quiet:
        lines.append(_read(assessment))
    lines += notices if quiet else [f"  {n}" for n in notices]
    lines += _findings_block(assessment.violations, assessment.gaps, assessment.suspects, quiet)
    lines.append(_result(assessment, strict=strict))
    return "\n".join(lines)


def _findings_block(
    violations: tuple[Finding, ...],
    gaps: tuple[Finding, ...],
    suspects: tuple[Suspect, ...],
    quiet: bool,
) -> list[str]:
    """Violations, gaps and suspects — a heading each, one line per finding with its next move."""
    lines: list[str] = []
    for heading, found in ((VIOLATION_HEADING, violations),
                           (findings.GAP_HEADING + ":", gaps),
                           ("suspects — review needed; never fail the gate:",
                            tuple(findings.suspect(s) for s in suspects))):  # fmt: skip
        if not found:
            continue
        if not quiet:
            lines += ["", heading]
        lines += [_finding(f, indent="" if quiet else "  ") for f in found]
    if not quiet:
        lines.append("")
    return lines


def ledger_check(project: ProjectAssessment, *, strict: bool, quiet: bool) -> str:
    """The ledger's check: every repo read, judged as one graph, and a result line that says it
    read working trees, not pins — in every form of the output, `--quiet` too."""
    notices = _project_notices(project)
    lines: list[str] = []
    if not quiet:
        lines.append("read — each repo's working tree, not pinned:")
        lines += _project_repos(project)
    lines += notices if quiet else [f"  {n}" for n in notices]
    gaps_heading = findings.GAP_HEADING
    block = _findings_block(project.violations, project.gaps, project.suspects, quiet)
    lines += [PROJECT_GAP_HEADING + ":" if line == gaps_heading + ":" else line for line in block]
    lines.append(_project_result(project, strict=strict))
    return "\n".join(lines)


def _project_repos(project: ProjectAssessment) -> list[str]:
    order = list(project.config.item_types)
    name_width = max(len(repo.name) for repo in project.repos)
    place_width = max(len(repo.location) for repo in project.repos)
    lines = []
    for repo in project.repos:
        counted = [
            f"{s.items} {s.item_type.replace('_', ' ')}{'' if s.items == 1 else 's'}"
            for s in sorted(repo.scanned, key=lambda s: order.index(s.item_type))
            if s.items
        ]
        shown = " · ".join(counted) if counted else "no items"
        lines.append(f"  {repo.name:<{name_width}}  {repo.location:<{place_width}}  {shown}")
    return lines


def _project_notices(project: ProjectAssessment) -> list[str]:
    """What the ledger's check could not verify or judge — in every form of its output."""
    lines = [_external(state) for state in project.externals if state.declared is None]
    lines += [
        f"external {s.prefix}*: verified against {s.location} ({s.declared} declared)"
        for s in project.externals
        if s.declared is not None
    ]
    for repo in project.repos:
        lines += _baseline_lines(repo.baseline_state, where=f" in {repo.name}")
    if project.config.baselines:
        lines.append(_project_change_counts(project))
    return lines + [notice.text for notice in project.notices]


def _project_change_counts(project: ProjectAssessment) -> str:
    comparisons = [c for repo in project.repos for c in repo.baseline_state.comparisons]
    frozen = sum(c.before is not None for c in comparisons)
    states = Counter(c.state for c in comparisons)
    withdrawn = sum(i.fields.get("Status") == "withdrawn" for i in project.graph.items())
    return (
        f"controlled document items: {frozen} frozen · {states['changed']} changed · "
        f"{states['new']} new · {states['removed']} removed · {withdrawn} withdrawn"
    )


def _project_result(project: ProjectAssessment, *, strict: bool) -> str:
    items = len(project.graph.items())
    repos = len(project.repos)
    violations, gaps = len(project.violations), len(project.gaps)
    parts = [
        f"result: {violations} {_noun(violations, 'violation', 'violations')}, {gaps} "
        f"{_noun(gaps, 'gap', 'gaps')} in {items} {_noun(items, 'item', 'items')} across "
        f"{repos} {_noun(repos, 'repo', 'repos')}",
        f"{len(project.suspects)} {_noun(len(project.suspects), 'suspect', 'suspects')} "
        "(informational)",
        f"exit {1 if project.fails(strict=strict) else 0}",
        "gate: gaps fail"
        if strict
        else "authoring: gaps do not fail — the gate is qmstrace ledger check --strict",
        "working trees, not pinned",
    ]
    unseen = [f"the {s.name}" for s in project.externals if s.declared is None]
    if unseen:
        parts.append(f"NOT VERIFIED: {', '.join(unseen)}")
    if project.config.baselines:
        parts += [_project_change_counts(project), "remote-tag completeness NOT VERIFIED"]
    cited = any(i.fields.get("Change") for i in project.graph.items())
    if (project.config.change_requests or cited) and not project.register.available:
        parts.append("change requests NOT VERIFIED")
    return " · ".join(parts)


def _notices(assessment: Assessment) -> list[str]:
    """Everything this run could not verify or judge — in every form of `check`, `--quiet` too."""
    lines = _unread(assessment)
    unverified = assessment.graph.unverified()
    if unverified:
        count = len(unverified)
        lines.append(
            f"not verified here: {count} {_noun(count, 'citation', 'citations')} of another "
            f"repo's items ({', '.join(unverified)}) — judged at the ledger's import"
        )
    return lines + _baselines(assessment) + [notice.text for notice in assessment.notices]


def _read(assessment: Assessment) -> str:
    order = list(assessment.config.item_types)
    counted = [
        f"{s.items} {s.item_type.replace('_', ' ')}{'' if s.items == 1 else 's'}"
        for s in sorted(assessment.scanned, key=lambda s: order.index(s.item_type))
    ]
    if not any(s.items for s in assessment.scanned):
        return "read: no items — qmstrace status shows what was scanned, and where"
    return "read: " + ", ".join(counted)


def _result(assessment: Assessment, *, strict: bool) -> str:
    items = sum(s.items for s in assessment.scanned)
    violations, gaps = len(assessment.violations), len(assessment.gaps)
    parts = [
        f"result: {violations} {_noun(violations, 'violation', 'violations')}, {gaps} "
        f"{_noun(gaps, 'gap', 'gaps')} in {items} {_noun(items, 'item', 'items')}",
        f"{len(assessment.suspects)} "
        f"{_noun(len(assessment.suspects), 'suspect', 'suspects')} (informational)",
        f"exit {1 if assessment.fails(strict=strict) else 0}",
        "gate: gaps fail"
        if strict
        else "authoring: gaps do not fail — the gate is qmstrace check --strict",
    ]
    unseen = [f"the {s.name}" for s in assessment.externals if s.declared is None]
    unseen += [f"sibling {s.name}" for s in assessment.siblings if s.declares is None]
    if not assessment.siblings_located:
        unseen.append("the project's other repos")
    if assessment.graph.unverified():
        unseen.append(f"{len(assessment.graph.unverified())} cited IDs")
    if unseen:
        parts.append(f"NOT VERIFIED: {', '.join(unseen)}")
    if assessment.config.baselines:
        parts += [_change_counts(assessment), "remote-tag completeness NOT VERIFIED"]
    has_citations = any(i.fields.get("Change") for i in assessment.graph.items())
    if (
        assessment.config.change_requests or has_citations
    ) and not assessment.baseline_state.register.available:
        parts.append("change requests NOT VERIFIED")
    return " · ".join(parts)
