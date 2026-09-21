"""Plain-text renderers — functions from an assessment to the bytes a reader sees.

Deterministic: everything is sorted, nothing depends on the clock or the machine, and every
path is shown relative to the repo. Every count is labelled. What could not be verified is
said in the header, never left for the reader to infer from an empty line.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from typing import Final

from qmstrace.core.assessment import Assessment, ExternalState, SiblingState
from qmstrace.core.config import SchemaForm, TraceConfig
from qmstrace.core.graph import Closure, Direction, Home, Node, Step
from qmstrace.core.model import Item

# `status` lists one item type line by line, and reads two of its fields by name. A known
# hard-coding (codebase blueprint § 8): every trace schema so far calls them this.
LISTED: Final = "requirement"
CATEGORY: Final = "Category"
VERIFY_BY: Final = "Verify-by"
TESTED: Final = "test"


def status(assessment: Assessment) -> str:
    """What was scanned, what lies around the repo, and one line per requirement."""
    lines = [_schema(assessment), f"scanned ({assessment.tree_label}):"]
    lines += _scanned(assessment)
    lines.append(f"links: {len(assessment.graph.links)}")
    lines += [_external(state) for state in assessment.externals]
    lines += _siblings(assessment)
    lines += [notice.text for notice in assessment.notices]
    lines += _listing(assessment)
    lines += ["", _violations(assessment)]
    return "\n".join(lines)


def _schema(assessment: Assessment) -> str:
    config = assessment.config
    if config.schema_form is SchemaForm.BY_PATH:
        where = f"the project's {assessment.schema_location}, by path"
    elif config.schema_form is SchemaForm.VERIFIED_COPY:
        where = "the project's, as a verified copy under [schema]"
    else:
        return "schema: this repo's own, under [schema] in qmstrace.toml — no ledger"
    return f"schema: {where} — plus this repo's qmstrace.toml"


def _scanned(assessment: Assessment) -> list[str]:
    config = assessment.config
    width = max(len(name) for name in config.item_types) + 2
    scanned = {s.item_type: s for s in assessment.scanned}
    lines = []
    for name, item_type in config.item_types.items():
        s = scanned.get(name)
        if s is None:
            lines.append(f"  {name:<{width}}known to the project, not scanned here")
            continue
        line = (
            f"  {name:<{width}}{s.items:>3} {_noun(s.items, 'item', 'items'):<5} in "
            f"{s.files:>2} {_noun(s.files, 'file', 'files'):<5}  {', '.join(s.patterns)}"
        )
        if s.ignored:
            line += f" · {s.ignored} {_noun(s.ignored, 'file', 'files')} ignored by "
            line += ", ".join(s.ignore)
        if item_type.extractor == "pytest":
            line += " · test functions: a parametrised function is one test case"
        lines.append(line)
    return lines


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


def _listing(assessment: Assessment) -> list[str]:
    config, graph = assessment.config, assessment.graph
    listed = graph.items(LISTED)
    if not listed:
        return []
    markers = sorted({k.marker for item in listed for k in graph.outgoing(item.id)})
    rows = [(item, _row(config, assessment, item, markers)) for item in listed]
    widths = [max(len(row[i]) for _, row in rows) for i in range(len(rows[0][1]))]

    def line(row: list[str]) -> str:
        cells = [cell.ljust(width) for cell, width in zip(row[:-1], widths, strict=False)]
        return "  " + "  ".join(cells) + "  — " + row[-1]

    tested = [row for item, row in rows if item.fields.get(VERIFY_BY, TESTED) == TESTED]
    apart = [(item, row) for item, row in rows if item.fields.get(VERIFY_BY, TESTED) != TESTED]
    lines = ["", *(line(row) for row in tested)]
    if apart:
        ways = sorted({item.fields[VERIFY_BY] for item, _ in apart})
        lines += ["", f"verified by {' or '.join(ways)} — no recorded basis yet, listed apart:"]
        lines += [line(row) for _, row in apart]
    lines += _categories(config, listed)
    return lines


def _row(config: TraceConfig, assessment: Assessment, item: Item, markers: list[str]) -> list[str]:
    """One requirement's cells: ID, category, what it points at, what hangs off it, title."""
    graph = assessment.graph
    row = [item.id]
    if CATEGORY in config.item_types[LISTED].fields:
        row.append(item.fields.get(CATEGORY, "?"))
    for marker in markers:
        targets = ", ".join(k.dst for k in graph.outgoing(item.id, marker))
        row.append(f"{marker.lower()} {targets or '—'}")
    for source_type in _downstream_types(config):
        sources = sorted(
            {k.src for k in graph.incoming(item.id) if _type_of(assessment, k.src) == source_type}
        )
        cell = f"{source_type.replace('_', ' ')}s {len(sources)}"
        levels = config.item_types[source_type].levels
        if levels and sources:
            counted = Counter(_level(assessment, s) for s in sources)
            cell += " (" + ", ".join(f"{lv} {counted[lv]}" for lv in levels if counted[lv]) + ")"
        row.append(cell)
    row.append(item.title)
    return row


def _downstream_types(config: TraceConfig) -> list[str]:
    """The item types whose links toward the listed type count for coverage, in the schema's
    order."""
    wanted = {
        source
        for link in config.links.values()
        if link.counts_for_coverage and LISTED in link.targets
        for source in link.sources
    }
    return [name for name in config.item_types if name in wanted]


def _type_of(assessment: Assessment, item_id: str) -> str | None:
    node = assessment.graph.node(item_id)
    return node.type if node else None


def _level(assessment: Assessment, item_id: str) -> str | None:
    node = assessment.graph.node(item_id)
    return node.item.level if node and node.item else None


def _categories(config: TraceConfig, listed: Iterable[Item]) -> list[str]:
    allowed = config.item_types[LISTED].values.get(CATEGORY, ())
    used = {item.fields.get(CATEGORY) for item in listed}
    unused = [value for value in allowed if value not in used]
    if not unused:
        return []
    return [
        "",
        f"categories with no requirement here: {', '.join(unused)}",
        "  (a prompt, not a gap — not every product needs one under every category)",
    ]


def _violations(assessment: Assessment) -> str:
    found = assessment.violations
    if not found:
        return "0 violations"
    counted = Counter(f.code for f in found)
    by_code = ", ".join(f"{code} \u00d7{n}" for code, n in sorted(counted.items()))
    return f"{len(found)} {_noun(len(found), 'violation', 'violations')} ({by_code})"


def _noun(count: int, one: str, many: str) -> str:
    return one if count == 1 else many


# ── thread ──────────────────────────────────────────────────────────────────────────────────

_SECTIONS: Final = {
    Direction.BACKWARD: "backward — what it derives from:",
    Direction.FORWARD: "forward — what hangs off it, nearest first:",
}


def thread(assessment: Assessment, item_id: str) -> str:
    """One item, what it derives from, and what hangs off it — each item once, nearest first."""
    graph = assessment.graph
    start = graph.nodes[item_id]
    walks = [graph.backward([item_id]), graph.forward([item_id])]
    lines = [_heading(start), f"  {_what(start)}"]
    lines += _problems(assessment)
    for walk in walks:
        lines += ["", _SECTIONS[walk.direction]]
        lines += _tree(assessment, walk, item_id) or [f"  {_nothing(start, walk.direction)}"]
    counted = " · ".join(f"{w.direction.value}: {_counts(assessment, w)}" for w in reversed(walks))
    lines += ["", f"{counted} — this repo only"]
    return "\n".join(lines)


def _heading(node: Node) -> str:
    return f"{node.id} — {node.title}" if node.title and node.title not in node.id else node.id


def _what(node: Node) -> str:
    """The type and home of an item, and where to read it."""
    kind = node.type.replace("_", " ") if node.type else "an item of unknown type"
    if node.home is Home.SIBLING:
        kind += f", in sibling {node.repo} — not pinned"
    elif node.home is Home.EXTERNAL:
        kind += f", in the {node.repo}"
    elif node.home is Home.UNVERIFIED:
        return "not verified here — judged at the ledger's import"
    if node.item is not None and node.item.level:
        kind += f", {node.item.level}"
    shown_elsewhere = node.where is None or node.where.startswith(node.id.split("::")[0])
    return kind if shown_elsewhere else f"{kind} · {node.where}"


def _problems(assessment: Assessment) -> list[str]:
    """What this run could not read, and what it refused — only when there is any."""
    lines = [_external(s) for s in assessment.externals if s.declared is None]
    lines += [_sibling(s) for s in assessment.siblings if s.declares is None]
    if not assessment.siblings_located:
        lines.append("siblings: NOT LOCATED — the project's other repos cannot be found")
    if assessment.violations:
        count = len(assessment.violations)
        lines.append(
            f"{count} {_noun(count, 'violation', 'violations')} — the links they refuse are not "
            "shown; `qmstrace status` counts them"
        )
    return [f"  {line}" for line in lines]


def _tree(assessment: Assessment, walk: Closure, start: str) -> list[str]:
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
            text = f"{'  ' * depth}{step.via.marker:<{width}}{_line(assessment, walk, step)}"
            lines.append(text)
            if not _ends_here(assessment, walk, step):
                descend(item, depth + 1)

    descend(start, 1)
    return lines


def _line(assessment: Assessment, walk: Closure, step: Step) -> str:
    node = step.node
    text = f"{_heading(node)} · {_what(node)}"
    if _is_dependency(assessment, step):
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


def _is_dependency(assessment: Assessment, step: Step) -> bool:
    link_type = assessment.config.links.get(step.via.marker)
    return link_type is not None and not link_type.counts_for_coverage


def _ends_here(assessment: Assessment, walk: Closure, step: Step) -> bool:
    """A backward walk shows an assumed item and stops there."""
    return walk.direction is Direction.BACKWARD and _is_dependency(assessment, step)


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


def _counts(assessment: Assessment, walk: Closure) -> str:
    counted = Counter(
        (step.node.type or "unverified item").replace("_", " ")
        for item_id, step in walk.steps.items()
        if item_id not in walk.starts
    )
    if not counted:
        return "nothing"
    order = [t.replace("_", " ") for t in assessment.config.item_types]
    ranked = sorted(counted, key=lambda t: (order.index(t) if t in order else len(order), t))
    return ", ".join(f"{counted[t]} {t if counted[t] == 1 else t + 's'}" for t in ranked)
