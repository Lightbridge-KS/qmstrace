"""Judging the work — coverage rules applied to this repo's items. Pure: data in, gaps out.

A coverage rule is data in the project's trace schema: which link an item type must have. An
unmet rule is a **gap** — expected in the middle of the work, and failed only by the gate. No
rule is hidden: a rule with no `where` applies to every item of its type, and one with a `where`
to the items whose field has exactly that value. Rules are judged on this repo's items only;
whether an item is covered across the project is the ledger's question.

A gap's next move is built from data: the form of the marker to write comes from the extractor
that reads it (`forms`), a violation that refused the needed link is named first, and a marker
written where it is not read (a stray) is named when it is the reason.

Implements: DSN-QMT-06, DSN-QMT-07, DSN-QMT-08
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Never

from qmstrace.core import findings
from qmstrace.core.baselines import (
    Baseline,
    Comparison,
    Register,
    Snapshot,
    Suspect,
    SuspectReason,
    Tag,
)
from qmstrace.core.config import CoverageRule, TraceConfig
from qmstrace.core.errors import CouldNotJudge
from qmstrace.core.graph import TraceGraph
from qmstrace.core.model import ID_TOKEN, Finding, Item, Stray

Form = Callable[[str, str], str]


def coverage(
    config: TraceConfig,
    graph: TraceGraph,
    violations: Iterable[Finding] = (),
    strays: Iterable[Stray] = (),
    forms: Mapping[str, Form] | None = None,
) -> list[Finding]:
    """Every unmet coverage rule on this repo's items, sorted by file, line and code.

    Parameters
    ----------
    violations
        What the graph refused — a gap whose needed link was refused points at it.
    strays
        Markers written where they are not read.
    forms
        For each item type this repo scans, how its items write a link.
    """
    refused = list(violations)
    stray_list = list(strays)
    gaps: list[Finding] = []
    for rule in config.rules:
        for item in graph.items(rule.item_type):
            if item.fields.get("Status") == "withdrawn":
                continue
            if any(item.fields.get(key) != value for key, value in rule.where.items()):
                continue
            links = (
                graph.incoming(item.id, rule.marker)
                if rule.direction == "incoming"
                else graph.outgoing(item.id, rule.marker)
            )
            active = [
                link
                for link in links
                if all(
                    graph.nodes[node].fields.get("Status") != "withdrawn"
                    for node in (link.src, link.dst)
                )
            ]
            if not active:
                fix = _fix(config, rule, item, refused, stray_list, forms or {})
                gaps.append(findings.unmet_rule(rule.code, item, rule.text, fix))
    return sorted(gaps, key=lambda f: (f.file, f.line, f.code))


def resolve_baselines(
    config: TraceConfig,
    tags: tuple[Tag, ...],
    snapshots: Mapping[str, Snapshot],
    ancestry: frozenset[tuple[str, str]],
) -> tuple[Baseline, ...]:
    """Resolve each configured scope using the partial order of reachable commits."""
    result = []
    for scope in config.baselines.values():
        groups: dict[str, list[Tag]] = {}
        for tag in tags:
            match = scope.tag.fullmatch(tag.name)
            if match:
                subject = scope.subject if scope.subject is not None else match.group("subject")
                groups.setdefault(subject, []).append(tag)
        for subject, candidates in sorted(groups.items()):
            commits = _latest({t.commit for t in candidates}, ancestry)
            chosen = tuple(
                sorted((t for t in candidates if t.commit in commits), key=lambda t: t.name)
            )
            if len(commits) != 1:
                _ambiguous(tuple(t.name for t in chosen))
            snapshot = snapshots[chosen[0].commit]
            # A type rename must not erase the historical scope's identities.
            old_scopes = snapshot.config.baselines.values() if snapshot.config else ()
            old_types = {
                kind
                for old in old_scopes
                if any(old.tag.fullmatch(t.name) for t in chosen)
                for kind in old.covers
            }
            covers = tuple(sorted(set(scope.covers) | old_types))
            result.append(Baseline(scope.name, subject, covers, chosen, snapshot))
    return tuple(result)


def guard(
    config: TraceConfig,
    items: Iterable[Item],
    baselines: tuple[Baseline, ...],
    ancestry: frozenset[tuple[str, str]],
    register: Register,
) -> tuple[tuple[Comparison, ...], tuple[Finding, ...]]:
    """Compare document identities once, then verify every fresh citation offered for a change."""
    current = {i.id: i for i in items if config.item_types[i.type].extractor == "markdown"}
    prior = {
        b.snapshot.commit: {
            i.id: i
            for i in b.snapshot.items
            if b.snapshot.config is not None
            and b.snapshot.config.item_types[i.type].extractor == "markdown"
        }
        for b in baselines
    }
    ids = set(current).union(*(set(old) for old in prior.values()))
    comparisons: list[Comparison] = []
    wrong: list[Finding] = []
    requests = {r.id: r for r in register.requests}
    for item_id in sorted(ids):
        after = current.get(item_id)
        eligible = []
        for baseline in baselines:
            before = prior[baseline.snapshot.commit].get(item_id)
            candidate = before or after
            if candidate is None or candidate.type not in baseline.covers:
                continue
            old_config = baseline.snapshot.config
            if old_config is None:
                continue
            key = _subject(candidate, old_config if before else config)
            old_keys = {s.key for s in old_config.subjects.values()}
            if key not in old_keys:
                continue  # a new subject is not a change to the old subject's baseline
            if baseline.subject != "*":
                subject = old_config.subjects.get(baseline.subject)
                if subject is None or subject.key != key:
                    continue
            eligible.append(baseline)
        if not eligible:
            continue
        latest = _latest({b.snapshot.commit for b in eligible}, ancestry)
        chosen = [b for b in eligible if b.snapshot.commit in latest]
        if len(latest) != 1:
            _ambiguous(tuple(sorted({t.name for b in chosen for t in b.tags})))
        first = chosen[0]
        combined = {t.name: t for b in chosen for t in b.tags}
        baseline = Baseline(
            ", ".join(sorted({b.scope for b in chosen})),
            first.subject,
            tuple(sorted({t for b in chosen for t in b.covers})),
            tuple(combined[n] for n in sorted(combined)),
            first.snapshot,
        )
        before = prior[baseline.snapshot.commit].get(item_id)
        state = (
            "removed"
            if after is None
            else "new"
            if before is None
            else "changed"
            if after.digest != before.digest
            else "frozen"
        )
        fresh = tuple(sorted(_citations(after) - _citations(before)))
        comparisons.append(Comparison(item_id, baseline, before, after, state, fresh))
        if state == "removed":
            assert before is not None
            wrong.append(findings.removed_frozen(before, baseline.label))
        elif state in {"changed", "new"}:
            assert after is not None
            if not fresh:
                wrong.append(findings.uncited_change(after, baseline.label, state))
            for citation in fresh:
                if not register.available:
                    continue
                request = requests.get(citation)
                if request is None or request.state != register.accepted:
                    detail = (
                        "does not exist or cannot be parsed"
                        if request is None
                        else (f"is '{request.state}', not '{register.accepted}'")
                    )
                    wrong.append(findings.invalid_request(after, citation, detail))
                elif item_id not in request.impacts:
                    wrong.append(findings.missing_impact(after, citation))
    return tuple(comparisons), tuple(wrong)


def _citations(item: Item | None) -> set[str]:
    if item is None:
        return set()
    return {
        s.strip() for s in item.fields.get("Change", "").split(",") if ID_TOKEN.fullmatch(s.strip())
    }


def suspects(graph: TraceGraph, comparisons: Iterable[Comparison]) -> tuple[Suspect, ...]:
    """Existing local dependants reached independently in each root's two graph versions.

    A reason always uses its upstream root's governing snapshot. A new dependant is
    traversed but not reported; a different root may have an older snapshot, so existence
    and edited state are evaluated per reason, never globally.
    """
    current = {item.id: item for item in graph.items()}
    reasons: dict[str, list[SuspectReason]] = {}
    for comparison in sorted(comparisons, key=lambda c: (c.id, c.baseline.snapshot.commit)):
        if comparison.state not in {"changed", "removed"}:
            continue
        snapshot = comparison.baseline.snapshot
        assert snapshot.graph is not None, "suspect judgment requires a validated snapshot graph"
        old = {item.id: item for item in snapshot.graph.items()}
        historical = snapshot.graph.forward([comparison.id]).steps
        present = graph.forward([comparison.id]).steps if comparison.id in current else {}
        root = comparison.after or comparison.before
        assert root is not None
        for item_id in sorted((historical.keys() | present.keys()) & old.keys() & current.keys()):
            if item_id == comparison.id:
                continue  # a cycle cannot make its own root suspect
            reasons.setdefault(item_id, []).append(
                SuspectReason(
                    comparison.id,
                    comparison.baseline,
                    comparison.state,
                    root.fields.get("Status") == "withdrawn",
                    current[item_id].digest != old[item_id].digest,
                    historical[item_id].distance if item_id in historical else None,
                    present[item_id].distance if item_id in present else None,
                )
            )
    return tuple(
        sorted(
            (Suspect(current[item_id], tuple(found)) for item_id, found in reasons.items()),
            key=lambda suspect: (suspect.distance, suspect.item.id),
        )
    )


def _subject(item: Item, config: TraceConfig) -> str:
    keys = [s.key for s in config.subjects.values() if s.key in item.id.split("-")[1:-1]]
    if len(keys) != 1:
        raise CouldNotJudge(
            f"{item.id}: subject ownership is {'ambiguous' if keys else 'unknown'}.",
            "Fix: give the item exactly one configured subject key as a complete ID segment; "
            "baseline ownership is never guessed.",
        )
    return keys[0]


def _latest(commits: set[str], ancestry: frozenset[tuple[str, str]]) -> set[str]:
    return {
        c for c in commits if not any(c != other and (c, other) in ancestry for other in commits)
    }


def _ambiguous(tags: tuple[str, ...]) -> Never:
    raise CouldNotJudge(
        f"No unique governing baseline: incomparable tags {', '.join(tags)}.",
        "Fix: establish an approved baseline after the merge; neither dates nor tag numbers "
        "can choose between these histories.",
    )


def _fix(
    config: TraceConfig,
    rule: CoverageRule,
    item: Item,
    refused: list[Finding],
    strays: list[Stray],
    forms: Mapping[str, Form],
) -> str:
    """The next move for one gap — the most specific reason first."""
    link = config.links[rule.marker]
    incoming = rule.direction == "incoming"
    for violation in refused:
        if violation.marker != rule.marker:
            continue
        own = violation.item == item.id or (violation.item is None and violation.file == item.file)
        if (not incoming and own) or (incoming and violation.target == item.id):
            return findings.fix_refused(violation)
    for stray in strays:
        if stray.marker != rule.marker:
            continue
        if incoming:
            meant = item.id in stray.targets
        elif stray.item is not None:  # in an item's section: only that item's gap
            meant = stray.item == item.id
        else:
            meant = stray.file == item.file
        if meant:
            return findings.fix_stray(stray)

    words = item.type.replace("_", " ")
    if incoming:
        here = [t for t in link.sources if t in forms]
        if not here:
            kinds = " or ".join(t.replace("_", " ") for t in link.sources)
            return findings.fix_none_here(kinds, item.id)
        source = here[0].replace("_", " ")
        fact = f"the {source} {rule.marker.lower()} {item.id}"
        return findings.fix_write(forms[here[0]](rule.marker, item.id), fact, on=source)
    target = " or ".join(t.replace("_", " ") for t in link.targets)
    form = forms.get(item.type)
    written = form(rule.marker, f"<{target} ID>") if form else f"'{rule.marker}: <{target} ID>'"
    if not any(t in forms for t in link.targets):
        return findings.fix_no_target(target, written)
    return findings.fix_write(written, f"this {words} {rule.marker.lower()} that {target}")
