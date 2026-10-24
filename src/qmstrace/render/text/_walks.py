"""Thread and impact text, sharing local and ledger walk presentation.

Implements: DSN-QMT-12
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from typing import Final

from qmstrace.core.assessment import Assessment, ProjectAssessment
from qmstrace.core.config import TraceConfig
from qmstrace.core.graph import Closure, Direction, Home, Node, Step, TraceGraph
from qmstrace.render._evidence import _external, _problems
from qmstrace.render._presentation import _heading, _noun, _what
from qmstrace.render._style import PLAIN, Style

_SECTIONS: Final = {
    Direction.BACKWARD: "backward — what it derives from:",
    Direction.FORWARD: "forward — what hangs off it, nearest first:",
}


def thread(assessment: Assessment, item_id: str, *, style: Style = PLAIN) -> str:
    """One item, what it derives from, and what hangs off it — each item once, nearest first."""
    return _thread(
        assessment.config,
        assessment.graph,
        item_id,
        _problems(assessment)
        + [f"  {n.text}" for n in assessment.notices if n.text.startswith("workspace:")],
        "this repo only",
        style=style,
    )


def ledger_thread(project: ProjectAssessment, item_id: str, *, style: Style = PLAIN) -> str:
    """One item across the whole project, from the ledger — the walk crosses every repo's edge."""
    return _thread(
        project.config,
        project.graph,
        item_id,
        _project_problems(project),
        _project_scope(project),
        style=style,
    )


def _thread(
    config: TraceConfig,
    graph: TraceGraph,
    item_id: str,
    problems: list[str],
    scope: str,
    *,
    style: Style = PLAIN,
) -> str:
    start = graph.nodes[item_id]
    walks = [graph.backward([item_id]), graph.forward([item_id])]
    lines = [_heading(start, style=style), f"  {_what(start, style=style)}"]
    lines += [style.warning(line) for line in problems]
    for walk in walks:
        lines += ["", style.heading(_SECTIONS[walk.direction])]
        lines += _tree(config, walk, item_id, style=style) or [
            f"  {_nothing(start, walk.direction)}"
        ]
    counted = " · ".join(f"{w.direction.value}: {_counts(config, w)}" for w in reversed(walks))
    lines += ["", f"{counted} — {scope}"]
    return "\n".join(lines)


def impact(assessment: Assessment, item_ids: Iterable[str], *, style: Style = PLAIN) -> str:
    """The combined impact of several starts, and a candidate change-request line."""
    graph = assessment.graph
    notes = [f"  {notice.text}" for notice in assessment.notices]
    if any(graph.nodes[i].home is Home.SIBLING for i in set(item_ids)):
        notes.append("  sibling ancestry and downstream links there are not scanned")
    return _impact(
        assessment.config,
        graph,
        item_ids,
        "impact — working-tree analysis, this repo only",
        _problems(assessment) + notes,
        "this repo only",
        style=style,
    )


def ledger_impact(
    project: ProjectAssessment, item_ids: Iterable[str], *, style: Style = PLAIN
) -> str:
    """The combined impact of several starts across the whole project, from the ledger."""
    return _impact(
        project.config,
        project.graph,
        item_ids,
        f"impact — {_project_scope(project)}",
        _project_problems(project),
        _project_scope(project),
        style=style,
    )


def _impact(
    config: TraceConfig,
    graph: TraceGraph,
    item_ids: Iterable[str],
    title: str,
    problems: list[str],
    scope: str,
    *,
    style: Style = PLAIN,
) -> str:
    starts = set(item_ids)
    forward = graph.forward(starts)
    backward = graph.backward(starts)
    downstream = set(forward.steps) - starts
    external_types = {source.item_type for source in config.externals.values()}
    origins = {
        item_id
        for item_id, step in backward.steps.items()
        if item_id not in starts
        and step.node.type in external_types
        and not _is_dependency(config, step)
    }
    lines = [style.heading(title), "", style.heading("starting items:")]
    lines += [
        f"  {_heading(graph.nodes[i], style=style)} · {_what(graph.nodes[i], style=style)}"
        for i in sorted(starts)
    ]
    lines += [style.warning(line) for line in problems]

    lines += ["", "downstream — grouped by item type:"]
    order = list(config.item_types)
    groups = {graph.nodes[i].type or "unverified item" for i in downstream}
    for kind in sorted(groups, key=lambda t: (order.index(t) if t in order else len(order), t)):
        members = sorted(
            i for i in downstream if (graph.nodes[i].type or "unverified item") == kind
        )
        lines.append(f"  {kind.replace('_', ' ')} ({len(members)}):")
        lines += [f"    {_line(config, forward, forward.steps[i], style=style)}" for i in members]
    if not downstream:
        lines.append("  nothing here hangs off the starting items")

    lines += ["", "upstream origins — of the starting items:"]
    lines += [
        f"  {_heading(graph.nodes[i], style=style)} · {_what(graph.nodes[i], style=style)}"
        for i in sorted(origins)
    ]
    if not origins:
        lines.append("  no upstream origins reached here")

    covered = {kind for baseline in config.baselines.values() for kind in baseline.covers}
    candidates = sorted(i for i in starts | downstream if graph.nodes[i].type in covered)
    unknown = sorted(i for i in starts | downstream if graph.nodes[i].type is None)
    lines += [
        "",
        "candidate for review — configured baseline types, not a claim of edits or frozen state:",
    ]
    if unknown:
        lines.append(f"  unknown type, omitted from the candidate: {', '.join(unknown)}")
    if candidates:
        lines.append(style.heading(f"Impacts: {', '.join(candidates)}"))
    elif not covered:
        lines.append("  no candidate line — no baseline item types are configured")
    else:
        lines.append("  no candidate line — no items with a known type covered by a baseline")
    lines += [
        "",
        f"starts: {len(starts)} · downstream: {_counts(config, forward)} · "
        f"upstream origins: {len(origins)} — {scope}",
    ]
    return "\n".join(lines)


def _project_scope(project: ProjectAssessment) -> str:
    count = len(project.repos)
    return f"the project's {count} {_noun(count, 'repo', 'repos')}, working trees, not pinned"


def _project_problems(project: ProjectAssessment) -> list[str]:
    """What the ledger's walk could not read, and what it refused — only when there is any."""
    lines = [_external(s) for s in project.externals if s.declared is None]
    lines += [n.text for n in project.notices if n.text.startswith("workspace:")]
    if project.violations:
        count = len(project.violations)
        lines.append(
            f"{count} {_noun(count, 'violation', 'violations')} — the links they refuse are not "
            "shown; `qmstrace ledger check` lists them"
        )
    return [f"  {line}" for line in lines]


def _tree(config: TraceConfig, walk: Closure, start: str, *, style: Style = PLAIN) -> list[str]:
    width = max((len(s.via.marker) for s in walk.steps.values()), default=0) + 2
    lines: list[str] = []
    shown = {start}

    def descend(parent: str, depth: int) -> None:
        for step in walk.children(parent):
            item = step.node.id
            if item in shown:  # a cycle back to the start
                lines.append(f"{'  ' * depth}{step.via.marker:<{width}}{item} — the item itself")
                continue
            shown.add(item)
            text = (
                f"{'  ' * depth}{step.via.marker:<{width}}{_line(config, walk, step, style=style)}"
            )
            lines.append(text)
            if not _ends_here(config, walk, step):
                descend(item, depth + 1)

    descend(start, 1)
    return lines


def _line(config: TraceConfig, walk: Closure, step: Step, *, style: Style = PLAIN) -> str:
    node = step.node
    text = f"{_heading(node, style=style)} · {_what(node, style=style)}"
    if _is_dependency(config, step):
        text += (
            " · assumes it — counts toward no coverage"
            if walk.direction is Direction.FORWARD
            else " · assumed — what it derives from is not followed"
        )
        if node.home is Home.SIBLING:
            text += "; judged at the ledger's import"
    for link in step.also:
        other = link.dst if walk.direction is Direction.FORWARD else link.src
        text += (
            f" · also {link.marker} {other}"
            if walk.direction is Direction.FORWARD
            else f" · also {link.marker} from {other}"
        )
    return text


def _is_dependency(config: TraceConfig, step: Step) -> bool:
    link_type = config.links.get(step.via.marker)
    return link_type is not None and not link_type.counts_for_coverage


def _ends_here(config: TraceConfig, walk: Closure, step: Step) -> bool:
    """A backward walk shows an assumed item and stops there."""
    return walk.direction is Direction.BACKWARD and _is_dependency(config, step)


def _nothing(start: Node, direction: Direction) -> str:
    if direction is Direction.FORWARD:
        return "nothing here hangs off it"
    if start.home is Home.SIBLING:
        return f"declared in sibling {start.repo} — what it derives from there is not shown"
    if start.home is Home.EXTERNAL:
        return f"declared in the {start.repo}, outside any product repo"
    if start.home is Home.UNVERIFIED:
        return "not verified here — judged at the ledger's import"
    return "it derives from nothing here"


def _counts(config: TraceConfig, walk: Closure) -> str:
    counted = Counter(
        (step.node.type or "unverified item").replace("_", " ")
        for item_id, step in walk.steps.items()
        if item_id not in walk.starts
    )
    if not counted:
        return "nothing"
    order = [t.replace("_", " ") for t in config.item_types]
    ranked = sorted(counted, key=lambda t: (order.index(t) if t in order else len(order), t))
    return ", ".join(f"{counted[t]} {t if counted[t] == 1 else t + 's'}" for t in ranked)
