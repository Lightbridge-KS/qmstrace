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
