"""The ledger's tables as data — one JSON document per table, format `qmstrace.table/1`
(ADR-0005).

A document carries what a reader needs to trust it before its rows: the project, the schema's
digest, the commit each repo had checked out and whether its tree was clean, that it was not
pinned, the violation and gap counts, and every notice. Identical inputs give identical bytes:
no timestamp, no machine path.

Implements: DSN-QMT-16
"""

from __future__ import annotations

import json

from qmstrace.core.assessment import Checkout, ProjectAssessment
from qmstrace.core.tables import Cell, Column, Table

FORMAT = "qmstrace.table/1"
DRAFT = "generated from the ledger — not an issued revision"


def document(project: ProjectAssessment, built: Table) -> str:
    """One of the project's tables as a `qmstrace.table/1` JSON document."""
    notices = [notice.text for notice in project.notices]
    if project.violations:
        notices.append(
            f"{len(project.violations)} violation(s) — the links they refuse are not in this "
            "table; qmstrace ledger check lists them."
        )
    notices += built.notices
    body: dict[str, object] = {
        "format": FORMAT,
        "table": built.name,
        "project": project.config.project,
        "draft": DRAFT,
        "schema": project.config.schema_digest,
        "ledger": _checkout(project.ledger),
        "read": [
            {"repo": repo.name, "location": repo.location, **_read(repo.checkout)}
            for repo in project.repos
        ],
        "pinned": False,
        "violations": len(project.violations),
        "gaps": len(project.gaps),
        "notices": notices,
        "columns": [_column(column) for column in built.columns],
        "rows": [{c.name: _cell(row.get(c.name)) for c in built.columns} for row in built.rows],
    }
    return json.dumps(body, indent=2, ensure_ascii=False) + "\n"


def _column(column: Column) -> dict[str, object]:
    return {"name": column.name, "cell": column.cell, "type": column.type, "via": column.via}


def _checkout(checkout: Checkout | None) -> dict[str, object] | None:
    return None if checkout is None else {"commit": checkout.commit, "clean": checkout.clean}


def _read(checkout: Checkout | None) -> dict[str, object]:
    return _checkout(checkout) or {"commit": None, "clean": None}


def _cell(value: Cell) -> object:
    return list(value) if isinstance(value, tuple) else value
