"""Source and baseline evidence text shared by text views and the offline browser.

Implements: DSN-QMT-12
"""

from __future__ import annotations

from collections import Counter

from qmstrace.core.assessment import Assessment, ExternalState, SiblingState
from qmstrace.core.baselines import BaselineState
from qmstrace.core.config import SchemaForm
from qmstrace.render._presentation import _noun


def _schema(assessment: Assessment) -> str:
    config = assessment.config
    if config.schema_form is SchemaForm.BY_PATH:
        where = f"the project's {assessment.schema_location}, by path"
    elif config.schema_form is SchemaForm.VERIFIED_COPY:
        where = "the project's, as a verified copy under [schema]"
    else:
        return "schema: this repo's own, under [schema] in qmstrace.toml — no ledger"
    return f"schema: {where} — plus this repo's qmstrace.toml"


def _external(state: ExternalState) -> str:
    head = f"external {state.prefix}*:"
    tail = f"each cited {state.prefix}N is judged at the ledger's import"
    if state.location is None:
        return (
            f"{head} NOT VERIFIED — no ledger beside this repo ('ledger' in qmstrace.toml); {tail}"
        )
    if state.declared is None:
        return f"{head} NOT VERIFIED — {state.location} is not reachable; {tail}"
    return f"{head} verified against {state.location} ({state.declared} declared)"


def _siblings(assessment: Assessment) -> list[str]:
    lines = [_sibling(state) for state in assessment.siblings]
    if not assessment.siblings_located:
        lines.append(
            "siblings: NOT LOCATED — no ledger beside this repo ('ledger' in qmstrace.toml), "
            "so the project's other repos cannot be found"
        )
    unverified = assessment.graph.unverified()
    if unverified:
        count = len(unverified)
        lines.append(
            f"not verified here: {count} {_noun(count, 'citation', 'citations')} of another "
            f"repo's items ({', '.join(unverified)}) — judged at the ledger's import"
        )
    return lines


def _sibling(state: SiblingState) -> str:
    if state.declares is None:
        if state.problem == "not reachable":
            return f"sibling {state.name}: NOT REACHABLE at {state.location}"
        return f"sibling {state.name}: at {state.location}, {state.problem}"
    declares = ", ".join(f"{n} {t}" for t, n in state.declares.items()) or "nothing declared"
    return (
        f"sibling {state.name}: {declares} — read from {state.location}'s working tree, not "
        "pinned; cite its items by ID"
    )


def _unread(assessment: Assessment) -> list[str]:
    """What this run could not read — only what applies, in `status`'s words."""
    lines = [_external(s) for s in assessment.externals if s.declared is None]
    lines += [_sibling(s) for s in assessment.siblings if s.declares is None]
    if not assessment.siblings_located:
        lines.append("siblings: NOT LOCATED — the project's other repos cannot be found")
    return lines


def _problems(assessment: Assessment) -> list[str]:
    """What this run could not read, and what it refused — only when there is any."""
    lines = _unread(assessment)
    if assessment.violations:
        count = len(assessment.violations)
        lines.append(
            f"{count} {_noun(count, 'violation', 'violations')} — the links they refuse are not "
            "shown; `qmstrace status` counts them"
        )
    return [f"  {line}" for line in lines]


def _baseline_lines(state: BaselineState, *, where: str = "") -> list[str]:
    """Each governing baseline and its tags' evidence — `where` names the repo in the ledger's
    check."""
    lines = []
    for baseline in state.baselines:
        lines.append(
            f"baseline {baseline.scope}{where} ({baseline.subject}): {baseline.label} "
            f"@ {baseline.snapshot.commit[:12]}"
        )
        for tag in baseline.tags:
            if tag.annotated:
                lines.append(f"  {tag.name}: annotated; tagger {tag.tagger}; date {tag.date}")
    return lines


def _baselines(assessment: Assessment) -> list[str]:
    lines = _baseline_lines(assessment.baseline_state)
    if assessment.config.baselines:
        lines.append(_change_counts(assessment))
    return lines


def _change_counts(assessment: Assessment) -> str:
    comparisons = assessment.baseline_state.comparisons
    frozen = sum(c.before is not None for c in comparisons)
    states = Counter(c.state for c in comparisons)
    withdrawn = sum(i.fields.get("Status") == "withdrawn" for i in assessment.graph.items())
    return (
        f"controlled document items: {frozen} frozen · {states['changed']} changed · "
        f"{states['new']} new · {states['removed']} removed · {withdrawn} withdrawn"
    )


def evidence(assessment: Assessment) -> tuple[str, ...]:
    """Source and baseline evidence shared by the offline browser and text views."""
    return tuple(
        [
            _schema(assessment),
            *(_external(state) for state in assessment.externals),
            *_siblings(assessment),
            *_baselines(assessment),
            *(notice.text for notice in assessment.notices),
            "Working-tree snapshot; its commit has not been verified. Regenerate to refresh.",
            "Traversal stops at this repo's edge. Sibling contents are not pinned.",
            "Suspects need review; edits and passing tests do not record review.",
        ]
    )
