"""Scanned inventory, requirement rows and the compact suspect summary.

Implements: DSN-QMT-12
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from typing import Final

from qmstrace.core import findings
from qmstrace.core.assessment import Assessment
from qmstrace.core.config import TraceConfig
from qmstrace.core.model import Finding, Item
from qmstrace.render._evidence import _baselines, _external, _schema, _siblings
from qmstrace.render._presentation import _finding, _noun

# Known status contract: requirement, Category and Verify-by remain schema-specific names.


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
    lines += _baselines(assessment)
    lines += [notice.text for notice in assessment.notices]
    lines += _listing(assessment)
    lines += _suspects(assessment)
    lines += ["", _violations(assessment)]
    return "\n".join(lines)


def _suspects(assessment: Assessment) -> list[str]:
    lines = ["", f"suspects: {len(assessment.suspects)} — informational; this repo only"]
    for suspect in assessment.suspects:
        if suspect.distance == 1:
            lines.append(_finding(findings.suspect(suspect), indent="  "))
    farther = Counter(s.distance for s in assessment.suspects if s.distance > 1)
    for distance, count in sorted(farther.items()):
        lines.append(f"  distance {distance}: {count} {_noun(count, 'suspect', 'suspects')}")
    if assessment.suspects:
        lines.append(
            "  qmstrace check lists every suspect and its reasons; review is not recorded here"
        )
    return lines


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
    controlled = next((c for c in assessment.baseline_state.comparisons if c.id == item.id), None)
    if controlled:
        changes = f": {', '.join(controlled.fresh)}" if controlled.fresh else ""
        row[0] += f" [{controlled.state}{changes}; {controlled.baseline.label}]"
    if item.fields.get("Status") == "withdrawn":
        row[0] += " [withdrawn]"
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
    counts = f"{_counted(assessment.violations, 'violation')} · {_counted(assessment.gaps, 'gap')}"
    if assessment.violations or assessment.gaps:
        counts += " — qmstrace check lists them"
    return counts


def _counted(found: Iterable[Finding], noun: str) -> str:
    """A labelled count, broken down by code: 2 violations (V03, V05 once each)."""
    counted = Counter(f.code for f in found)
    total = sum(counted.values())
    text = f"{total} {noun if total == 1 else noun + 's'}"
    if total:
        text += " (" + ", ".join(f"{c} \u00d7{n}" for c, n in sorted(counted.items())) + ")"
    return text
