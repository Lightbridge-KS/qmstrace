"""Historical snapshot reading and baseline judgment orchestration.

Implements: DSN-QMT-07
"""

from __future__ import annotations

import posixpath
from collections.abc import Iterable
from dataclasses import replace
from pathlib import Path

from qmstrace.core import findings, judge
from qmstrace.core.baselines import BaselineState, Register, Snapshot
from qmstrace.core.config import TraceConfig
from qmstrace.core.errors import CouldNotJudge
from qmstrace.core.graph import Surroundings, TraceGraph
from qmstrace.core.model import Finding, Item, Notice
from qmstrace.infra.git import IGit
from qmstrace.infra.tree import GitTree
from qmstrace.workspace._discovery import CONFIG_FILE, _configuration
from qmstrace.workspace._scanning import _scan


def _judged_baselines(
    root: Path,
    config: TraceConfig,
    source: IGit,
    items: Iterable[Item],
    register: Register,
    *,
    repo: str | None = None,
    location: str = ".",
) -> tuple[BaselineState, tuple[Finding, ...]]:
    """One repo's baselines, read from its reachable tags, and the guard over its items. In
    the ledger's check, `repo` names it: its snapshots are read with the same qualified IDs and
    locations as today's items, so the two can be compared."""
    source.state()
    tags = tuple(
        t
        for t in source.tags_reachable_from_head()
        if any(s.tag.fullmatch(t.name) for s in config.baselines.values())
    )
    commits = sorted({t.commit for t in tags})
    ancestry = frozenset(
        (a, b) for a in commits for b in commits if a != b and source.is_ancestor(a, b)
    )
    snapshots = {c: Snapshot(c, None, repo=repo) for c in commits}
    selected = judge.resolve_baselines(config, tags, snapshots, ancestry)
    for commit in sorted({b.snapshot.commit for b in selected}):
        tree = GitTree(source, commit)
        if CONFIG_FILE not in tree.files():
            continue
        tags_here = ", ".join(t.name for t in tags if t.commit == commit)
        try:
            tagged = _configuration(root, tree)
            scan = _scan(tree, tagged, tagged.item_types.values(), with_misplaced=True)
        except CouldNotJudge as stopped:
            raise CouldNotJudge(
                f"Historical trace data at {tags_here} ({commit}) cannot be read: {stopped.what}",
                f"{stopped.next_move} Correct the current tree and establish a valid, approved "
                "successor baseline; editing today's files cannot repair this snapshot, and "
                "the tag must not be rewritten.",
            ) from None
        extracted, misplaced = scan.extracted, scan.misplaced
        if repo is not None:
            derived = frozenset(t.name for t in tagged.item_types.values() if t.derives_ids)
            extracted = tuple(p.qualified(repo, location, derived) for p in extracted)
            misplaced = tuple(
                replace(i, file=posixpath.normpath(posixpath.join(location, i.file)))
                for i in misplaced
            )
        found_items = tuple(i for part in extracted for i in part.items)
        historical, found = TraceGraph.build(
            tagged,
            extracted,
            Surroundings(every_sibling_read=False),
            misplaced=misplaced,
        )
        problems = [f for f in found if f.code not in findings.SNAPSHOT_SAFE]
        if problems or misplaced or len({i.id for i in found_items}) != len(found_items):
            where = f" in {repo}" if repo is not None else ""
            raise CouldNotJudge(
                f"Historical trace data at {tags_here} ({commit}){where} cannot form a reliable "
                f"snapshot: {_problems(problems)}",
                "Fix: inspect the tagged configuration and source; do not replace historical "
                "data with today's tree or rewrite the baseline tag.",
            )
        snapshots[commit] = Snapshot(commit, tagged, found_items, historical, repo=repo)
    baselines = judge.resolve_baselines(config, tags, snapshots, ancestry)
    comparisons, wrong = judge.guard(config, items, baselines, ancestry, register)
    return BaselineState(baselines, comparisons, register), wrong


# Problems listed one by one in a refusal; past this, they are counted by code (ADR-0002).
_SHOWN = 3


def _problems(problems: list[Finding]) -> str:
    """What makes a tagged snapshot unreadable — every problem when there are few, else a count
    by code, the first few, and where to see the rest."""
    listed = "; ".join(f"{f.code} {f.file}:{f.line}: {f.what}" for f in problems[:_SHOWN])
    if len(problems) <= _SHOWN:
        return listed
    counts: dict[str, int] = {}
    for finding in problems:
        counts[finding.code] = counts.get(finding.code, 0) + 1
    by_code = ", ".join(f"{n} {code}" for code, n in sorted(counts.items()))
    rest = len(problems) - _SHOWN
    return (
        f"{len(problems)} findings ({by_code}), the first {_SHOWN}: {listed}; and {rest} more — "
        "a check run in a checkout of the tag lists every one"
    )


def _baseline_notices(repo: str, state: BaselineState) -> list[Notice]:
    """What one repo's baselines leave unverified, in the ledger's check."""
    if not state.baselines:
        return [Notice(f"baselines in {repo}: no matching reachable local tag — nothing frozen")]
    notices: list[Notice] = []
    for baseline in state.baselines:
        historical = baseline.snapshot.graph
        if historical is not None and any(n.item is None for n in historical.nodes.values()):
            notices.append(
                Notice(
                    f"baseline {baseline.label} in {repo}: historical citations outside it "
                    "NOT VERIFIED — each tagged version is read on its own"
                )
            )
        if baseline.snapshot.config is None:
            notices.append(
                Notice(
                    f"baseline {baseline.label} in {repo}: before trace configuration — "
                    "freezes nothing"
                )
            )
        for tag in baseline.tags:
            if not tag.annotated:
                notices.append(
                    Notice(
                        f"baseline {tag.name} in {repo}: lightweight tag — weaker evidence; "
                        "no tagger or tag date"
                    )
                )
    return notices
