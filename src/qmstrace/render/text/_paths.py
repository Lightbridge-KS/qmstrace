"""Configuration-only path diagnostics; locations are relative to the active trace root.

Implements: DSN-QMT-12
"""

from qmstrace.core.locations import Paths


def paths(view: Paths) -> str:
    lines = [
        f"project: {view.project}",
        view.source,
        "path anchor: current trace root; map entries start at the map's directory",
        f"ledger: {view.ledger or 'not located'} — "
        f"{'available' if view.ledger_available else 'NOT AVAILABLE'}",
    ]
    for repo in view.repos:
        state = "available" if repo.available else "NOT AVAILABLE"
        current = " · current repo" if repo.current else ""
        lines.append(f"repo {repo.name}: {repo.location or 'not mapped'} — {state}{current}")
    return "\n".join([*lines, "Locations only; no items scanned or baselines judged. Exit 0."])
