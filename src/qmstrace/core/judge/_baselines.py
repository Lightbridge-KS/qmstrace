"""Baseline selection and fresh change-request guards. Pure judgment over snapshots.

Implements: DSN-QMT-07
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Never

from qmstrace.core import findings
from qmstrace.core.baselines import Baseline, Comparison, Register, Snapshot, Tag
from qmstrace.core.config import TraceConfig
from qmstrace.core.errors import CouldNotJudge
from qmstrace.core.model import ID_TOKEN, Finding, Item


def ownership_findings(config: TraceConfig, items: Iterable[Item]) -> tuple[Finding, ...]:
    """Report subject-less controlled document IDs before a baseline freezes them."""
    covered = {kind for scope in config.baselines.values() for kind in scope.covers}
    available = tuple(sorted(f"{name}={subject.key}" for name, subject in config.subjects.items()))
    wrong = []
    for item in items:
        if item.type not in covered or config.item_types[item.type].extractor != "markdown":
            continue
        matches = _matching_subjects(item, config)
        if len(matches) != 1:
            wrong.append(
                findings.subject_ownership(
                    item,
                    tuple(f"{name}={key}" for name, key in matches),
                    available,
                    duplicate_key=any(
                        sum(subject.key == key for subject in config.subjects.values()) > 1
                        for _, key in matches
                    ),
                    repeated_segment=len(set(matches)) != len(matches),
                )
            )
    return tuple(wrong)


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
            key = _subject(
                candidate, old_config if before else config, baseline, historical=before is not None
            )
            if before is not None and after is not None:
                _subject(after, config, baseline, historical=False)
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


def _matching_subjects(item: Item, config: TraceConfig) -> tuple[tuple[str, str], ...]:
    segments = item.id.split("-")[1:-1]
    return tuple(
        (name, subject.key)
        for name, subject in sorted(config.subjects.items())
        for segment in segments
        if subject.key == segment
    )


def _subject(item: Item, config: TraceConfig, baseline: Baseline, *, historical: bool) -> str:
    matches = _matching_subjects(item, config)
    if len(matches) != 1:
        where = "tagged snapshot" if historical else "current working tree"
        reason = (
            "repeated"
            if len(set(matches)) != len(matches)
            else "ambiguous"
            if matches
            else "unknown"
        )
        next_move = (
            "Fix: correct the current tree and establish a valid, approved successor baseline; "
            "editing today's item cannot repair the tagged snapshot, and the tag must not "
            "be rewritten."
            if historical
            else "Fix: give the current item exactly one configured subject key as a complete "
            "internal ID segment; baseline applicability cannot be judged until then."
        )
        raise CouldNotJudge(
            f"{item.id} at {item.file}:{item.line}: subject ownership is "
            f"{reason} in the {where} for "
            f"baseline {baseline.label} (matches: "
            f"{', '.join(f'{name}={key}' for name, key in matches) or 'none'}).",
            next_move,
        )
    return matches[0][1]


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
