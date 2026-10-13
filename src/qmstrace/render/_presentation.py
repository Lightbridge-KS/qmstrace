"""Shared item labels, individual findings and pluralized counts.

Implements: DSN-QMT-12
"""

from __future__ import annotations

from qmstrace.core.graph import Home, Node
from qmstrace.core.model import Finding


def _heading(node: Node) -> str:
    return f"{node.id} — {node.title}" if node.title and node.title not in node.id else node.id


def _what(node: Node) -> str:
    """The type and home of an item, and where to read it."""
    kind = node.type.replace("_", " ") if node.type else "an item of unknown type"
    if node.fields.get("Status") == "withdrawn":
        kind += ", withdrawn — excluded from coverage"
    if node.home is Home.SIBLING:
        kind += f", in sibling {node.repo} — not pinned"
    elif node.home is Home.EXTERNAL:
        kind += f", in the {node.repo}"
    elif node.home is Home.UNVERIFIED:
        return "not verified here — judged at the ledger's import"
    elif node.repo is not None:  # a judged item of the project's graph: its repo
        kind += f", in {node.repo}"
    if node.item is not None and node.item.level:
        kind += f", {node.item.level}"
    return kind if _where_shown_by_id(node) else f"{kind} · {node.where}"


def _where_shown_by_id(node: Node) -> bool:
    """Whether the ID already says where the item is — a module's path, a test's node ID,
    qualified by its repo or not — so the location need not be printed again."""
    if node.where is None:
        return True
    path = node.id.split("::")[0]
    if node.repo is not None and path.startswith(f"{node.repo}:"):
        path = path[len(node.repo) + 1 :]
    file = node.where.rsplit(":", 1)[0]
    return file == path or file.endswith(f"/{path}")


def _finding(finding: Finding, *, indent: str) -> str:
    return (
        f"{indent}{finding.code}  {finding.file}:{finding.line}  {finding.what} {finding.next_move}"
    )


def _noun(count: int, one: str, many: str) -> str:
    return one if count == 1 else many
