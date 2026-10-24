"""Configuration-only path diagnostics; locations are relative to the active trace root.

Implements: DSN-QMT-12
"""

from qmstrace.core.locations import Paths
from qmstrace.render._style import PLAIN, Style


def paths(view: Paths, *, style: Style = PLAIN) -> str:
    lines = [
        style.heading(f"project: {view.project}"),
        style.location(view.source),
        "path anchor: current trace root; map entries start at the map's directory",
        f"ledger: {view.ledger or 'not located'} — "
        f"{'available' if view.ledger_available else style.warning('NOT AVAILABLE')}",
    ]
    for repo in view.repos:
        state = "available" if repo.available else style.warning("NOT AVAILABLE")
        current = " · current repo" if repo.current else ""
        lines.append(f"repo {repo.name}: {repo.location or 'not mapped'} — {state}{current}")
    return "\n".join([*lines, "Locations only; no items scanned or baselines judged. Exit 0."])
